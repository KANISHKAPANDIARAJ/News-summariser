"""Summarization REST API routes."""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.api.schemas.summary import SummarizeRequest, SummaryResponse
from app.api.schemas.common import ApiResponse
from app.services.article_extractor import ArticleExtractor, ArticleExtractionError
from app.services.text_cleaner import TextCleaner
from app.services.summarizer import HierarchicalSummarizer, SummarizationError
from app.services.translator import TranslationService, TranslationError
from app.db import get_db_session
from app.repositories.article_repo import ArticleRepository
from app.repositories.summary_repo import SummaryRepository
from app.models.article import Article
from app.models.summary import Summary
from app.models.translation import Translation
from app.utils.cache import compute_content_hash
from app.constants import ErrorCodes, SUPPORTED_LANGUAGES
from app.utils.logger import logger

summarization_bp = Blueprint("summarization_api", __name__)
extractor = ArticleExtractor()
summarizer = HierarchicalSummarizer()
translator = TranslationService()

@summarization_bp.route("/api/summarize", methods=["POST"])
def summarize_article():
    """Generates an abstractive summary of an article from URL or raw text."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        req = SummarizeRequest(**data)
    except ValidationError as ve:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Invalid request payload.",
            details=ve.errors()
        ).model_dump()), 422

    if not req.url and not req.text:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Either 'url' or 'text' must be provided."
        ).model_dump()), 400

    target_lang = req.language.lower().strip()
    if target_lang not in SUPPORTED_LANGUAGES:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.UNSUPPORTED_LANGUAGE,
            message=f"Language '{target_lang}' is not supported."
        ).model_dump()), 400

    # 1. Retrieve or extract content
    article_title = "Direct Input"
    article_url = req.url
    author = None
    publisher = None
    published_date = None
    image_url = None

    if req.url:
        try:
            extracted = extractor.extract(req.url)
            raw_text = extracted["text"]
            article_title = extracted.get("title") or "Web Article"
            author = extracted.get("author")
            publisher = extracted.get("publisher")
            published_date = extracted.get("published_date")
            image_url = extracted.get("image_url")
        except ArticleExtractionError as ee:
            return jsonify(ApiResponse.fail(
                code=ErrorCodes.ARTICLE_EXTRACTION_FAILED,
                message=str(ee)
            ).model_dump()), 400
    else:
        raw_text = req.text

    cleaned_text = TextCleaner.clean(raw_text)
    if len(cleaned_text.strip()) < 30:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.TEXT_TOO_SHORT,
            message="Article content is too short to summarize (minimum 30 characters)."
        ).model_dump()), 400

    content_hash = compute_content_hash(cleaned_text)

    # 2. Database Persistence and Cache Check
    with get_db_session() as session:
        article_repo = ArticleRepository(session)
        summary_repo = SummaryRepository(session)

        db_article = article_repo.get_by_content_hash(content_hash)
        if not db_article:
            db_article = Article(
                url=article_url,
                content_hash=content_hash,
                title=article_title,
                author=author,
                publisher=publisher,
                published_date=published_date,
                image_url=image_url,
                raw_text=raw_text,
                cleaned_text=cleaned_text,
                language=TextCleaner.detect_language(cleaned_text),
                word_count=len(cleaned_text.split()),
            )
            article_repo.create(db_article)

        # Check existing summary for this profile
        db_summary = summary_repo.get_by_article_and_profile(db_article.id, req.length_profile)
        if not db_summary:
            try:
                summ_res = summarizer.summarize(cleaned_text, length_profile=req.length_profile)
                db_summary = Summary(
                    article_id=db_article.id,
                    summary_type="hierarchical_map_reduce",
                    length_profile=req.length_profile,
                    text=summ_res["summary"],
                    compression_ratio=summ_res["compression_ratio"],
                    processing_time_ms=summ_res["processing_time_ms"],
                    model_name=summ_res["model_name"],
                )
                summary_repo.create_summary(db_summary)
            except SummarizationError as se:
                return jsonify(ApiResponse.fail(
                    code=ErrorCodes.SUMMARIZATION_FAILED,
                    message=str(se)
                ).model_dump()), 500

        # Translation check
        final_summary_text = db_summary.text
        if target_lang != "en":
            db_trans = summary_repo.get_translation(db_summary.id, target_lang)
            if not db_trans:
                try:
                    trans_res = translator.translate(db_summary.text, target_lang=target_lang)
                    db_trans = Translation(
                        summary_id=db_summary.id,
                        source_language="en",
                        target_language=target_lang,
                        translated_text=trans_res["translation"],
                        model_name=trans_res["model_name"],
                    )
                    summary_repo.create_translation(db_trans)
                except TranslationError as te:
                    logger.warning(f"Translation to {target_lang} failed: {te}")
            if db_trans:
                final_summary_text = db_trans.translated_text

        response_payload = SummaryResponse(
            summary_id=db_summary.id,
            article_id=db_article.id,
            summary=final_summary_text,
            length_profile=db_summary.length_profile,
            compression_ratio=db_summary.compression_ratio or 0.0,
            processing_time_ms=db_summary.processing_time_ms or 0.0,
            model_name=db_summary.model_name,
            language=target_lang,
            original_title=db_article.title,
            original_url=db_article.url,
        )

        return jsonify(ApiResponse.ok(response_payload.model_dump()).model_dump()), 200

@summarization_bp.route("/api/summaries/<summary_id>", methods=["GET"])
def get_summary_by_id(summary_id: str):
    """Retrieves an existing summary by its unique identifier."""
    with get_db_session() as session:
        summary_repo = SummaryRepository(session)
        summary = summary_repo.get_by_id(summary_id)
        if not summary:
            return jsonify(ApiResponse.fail(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"Summary with ID '{summary_id}' not found."
            ).model_dump()), 404

        article = summary.article
        data = {
            **summary.to_dict(),
            "article": article.to_dict() if article else None,
            "translations": [t.to_dict() for t in summary.translations],
        }
        return jsonify(ApiResponse.ok(data).model_dump()), 200
