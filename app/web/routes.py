"""Web UI routes serving dashboard and shared summary reports."""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    abort,
    make_response,
)
from app.db import get_db_session
from app.repositories.summary_repo import SummaryRepository
from app.repositories.article_repo import ArticleRepository
from app.models.article import Article
from app.models.summary import Summary
from app.models.translation import Translation
from app.services.article_extractor import ArticleExtractor, ArticleExtractionError
from app.services.text_cleaner import TextCleaner
from app.services.summarizer import HierarchicalSummarizer
from app.services.sentiment_analyzer import SentimentAnalyzer
from app.services.keypoint_extractor import KeypointExtractor
from app.services.translator import TranslationService
from app.constants import SUPPORTED_LANGUAGES
from app.utils.cache import compute_content_hash
from app.utils.logger import logger

web_bp = Blueprint("web", __name__)
extractor = ArticleExtractor()
summarizer = HierarchicalSummarizer()
sentiment_analyzer = SentimentAnalyzer()
keypoint_extractor = KeypointExtractor()
translator = TranslationService()


@web_bp.route("/", methods=["GET", "POST"])
def index():
    """Renders the AI News Workspace dashboard with support for form and API submissions."""
    error = None
    summary = None
    key_sentences = []
    sentiment = None
    summary_length = "medium"
    language = "en"
    summary_id = None

    if request.method == "POST":
        input_type = request.form.get("input_type", "url")
        summary_length = request.form.get("summary_length", "medium")
        language = request.form.get("language", "en").lower().strip()
        url = request.form.get("url", "").strip()
        text = request.form.get("text", "").strip()

        article_title = "Direct Input"
        raw_text = ""
        source_url = None

        if input_type == "url" or (url and not text):
            source_url = url
            try:
                extracted = extractor.extract(url)
                raw_text = extracted["text"]
                article_title = extracted.get("title") or "Web Article"
            except ArticleExtractionError as ee:
                error = str(ee)
            except Exception as e:
                error = f"Extraction failed: {e}"
        else:
            raw_text = text

        cleaned_text = TextCleaner.clean(raw_text) if raw_text else ""
        if not error and len(cleaned_text.strip()) < 30:
            error = "Please provide at least 30 characters of article content."

        if not error:
            try:
                # 1. Summarize
                summ_res = summarizer.summarize(
                    cleaned_text, length_profile=summary_length
                )
                raw_summary = summ_res["summary"]

                # 2. Keypoints & Sentiment
                key_sentences_list = [
                    kp["text"]
                    for kp in keypoint_extractor.extract_key_points(
                        cleaned_text, top_n=3
                    )
                ]
                sentiment = sentiment_analyzer.analyze(cleaned_text)

                # 3. Translation if requested
                if language != "en" and language in SUPPORTED_LANGUAGES:
                    trans_res = translator.translate(raw_summary, target_lang=language)
                    summary = trans_res["translation"]
                    key_sentences = [
                        translator.translate(s, target_lang=language)["translation"]
                        for s in key_sentences_list
                    ]
                else:
                    summary = raw_summary
                    key_sentences = key_sentences_list

                # 4. Save to Persistent DB
                content_hash = compute_content_hash(cleaned_text)
                with get_db_session() as session:
                    art_repo = ArticleRepository(session)
                    sum_repo = SummaryRepository(session)

                    art = art_repo.get_by_content_hash(content_hash)
                    if not art:
                        art = Article(
                            url=source_url,
                            content_hash=content_hash,
                            title=article_title,
                            raw_text=raw_text,
                            cleaned_text=cleaned_text,
                            word_count=len(cleaned_text.split()),
                        )
                        art_repo.create(art)

                    db_sum = sum_repo.get_by_article_and_profile(art.id, summary_length)
                    if not db_sum:
                        db_sum = Summary(
                            article_id=art.id,
                            summary_type="hierarchical_map_reduce",
                            length_profile=summary_length,
                            text=raw_summary,
                            compression_ratio=summ_res["compression_ratio"],
                            processing_time_ms=summ_res["processing_time_ms"],
                            model_name=summ_res["model_name"],
                        )
                        sum_repo.create_summary(db_sum)
                    summary_id = db_sum.id

                # Redirect to preserve PRG (Post-Redirect-Get) pattern or render
                resp = make_response(
                    redirect(
                        url_for("web.shared_summary", sum_id=summary_id, lang=language)
                    )
                )
                return resp

            except Exception as e:
                logger.error(f"Error processing submission: {e}")
                error = f"Processing error: {str(e)}"

    # Retrieve recent summaries from persistent database
    recent_items = []
    with get_db_session() as session:
        sum_repo = SummaryRepository(session)
        for s in sum_repo.list_recent_summaries(limit=8):
            art = s.article
            recent_items.append(
                {
                    "id": s.id,
                    "summary": s.text[:90] + "...",
                    "title": art.title if art else "Article Summary",
                    "length": s.length_profile,
                }
            )

    return render_template(
        "index.html",
        summary=summary,
        key_sentences=key_sentences,
        error=error,
        summary_length=summary_length,
        language=language,
        sentiment=sentiment,
        recent=recent_items,
        supported_languages=SUPPORTED_LANGUAGES,
    )


@web_bp.route("/s/<sum_id>")
def shared_summary(sum_id: str):
    """Renders the shareable summary view from persistent database."""
    with get_db_session() as session:
        sum_repo = SummaryRepository(session)
        summary_rec = sum_repo.get_by_id(sum_id)
        if not summary_rec:
            abort(404)

        article = summary_rec.article
        lang = request.args.get("lang", "en").lower().strip()

        display_text = summary_rec.text
        # Check translation
        if lang != "en" and lang in SUPPORTED_LANGUAGES:
            trans_rec = sum_repo.get_translation(summary_rec.id, lang)
            if trans_rec:
                display_text = trans_rec.translated_text
            else:
                try:
                    trans_res = translator.translate(summary_rec.text, target_lang=lang)
                    new_trans = Translation(
                        summary_id=summary_rec.id,
                        source_language="en",
                        target_language=lang,
                        translated_text=trans_res["translation"],
                        model_name=trans_res["model_name"],
                    )
                    sum_repo.create_translation(new_trans)
                    display_text = new_trans.translated_text
                except Exception as e:
                    logger.warning(f"On-demand translation failed: {e}")

        # Sentiment and keypoints from article if available
        analysis = sum_repo.get_analysis_by_article_id(article.id) if article else None

        sentiment_data = None
        key_sentences = []
        if analysis:
            sentiment_data = {
                "label": analysis.sentiment_label,
                "score": analysis.sentiment_score,
                "distribution": analysis.sentiment_distribution,
            }
            key_sentences = [kp.get("text", "") for kp in analysis.key_points[:3]]

        return render_template(
            "shared_summary.html",
            summary=display_text,
            key_sentences=key_sentences,
            summary_length=summary_rec.length_profile,
            url=article.url if article else None,
            title=article.title if article else "Summary",
            text=article.cleaned_text if article else None,
            language=lang,
            sentiment=sentiment_data,
            sum_id=sum_id,
            compression_ratio=summary_rec.compression_ratio,
            processing_time_ms=summary_rec.processing_time_ms,
        )
