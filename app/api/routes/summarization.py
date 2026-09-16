"""Summarization REST API routes with multilingual support and partial success handling."""

from __future__ import annotations
import time

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.api.schemas.summary import SummarizeRequest
from app.api.schemas.common import ApiResponse
from app.constants import SUPPORTED_LANGUAGES, ErrorCodes
from app.services.article_extractor import ArticleExtractionError, ArticleExtractor
from app.services.language_detector import LanguageDetector
from app.services.multilingual_summarizer import MultilingualSummarizer
from app.services.text_cleaner import TextCleaner
from app.services.topic_classifier import TopicClassifier
from app.db import get_db_session
from app.repositories.article_repo import ArticleRepository
from app.repositories.summary_repo import SummaryRepository
from app.models.article import Article
from app.models.summary import Summary
from app.utils.cache import compute_content_hash
from app.utils.logger import logger

summarization_bp = Blueprint("summarization_api", __name__)
extractor = ArticleExtractor()
multilingual_summarizer = MultilingualSummarizer()


@summarization_bp.route("/api/summarize", methods=["POST"])
def summarize_article():
    """Generates an abstractive summary of an article from URL or raw text in English or regional languages."""
    start_time = time.perf_counter()

    try:
        data = request.get_json(force=True, silent=True) or {}
        req = SummarizeRequest(**data)
    except ValidationError as ve:
        return jsonify(
            ApiResponse.fail(
                code=ErrorCodes.VALIDATION_ERROR,
                message="Invalid request payload.",
                details=ve.errors(),
            ).model_dump()
        ), 422

    if not req.url and not req.text:
        return jsonify(
            ApiResponse.fail(
                code=ErrorCodes.VALIDATION_ERROR,
                message="Either 'url' or 'text' must be provided.",
            ).model_dump()
        ), 400

    target_lang = (req.language or "en").lower().strip()
    if target_lang != "auto" and target_lang not in SUPPORTED_LANGUAGES:
        return jsonify(
            ApiResponse.fail(
                code=ErrorCodes.UNSUPPORTED_LANGUAGE,
                message=f"Language '{target_lang}' is not supported.",
            ).model_dump()
        ), 400

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
            return jsonify(
                ApiResponse.fail(
                    code=ErrorCodes.ARTICLE_EXTRACTION_FAILED, message=str(ee)
                ).model_dump()
            ), 400
        except Exception as e:  # noqa: BLE001
            return jsonify(
                ApiResponse.fail(
                    code=ErrorCodes.ARTICLE_EXTRACTION_FAILED,
                    message=f"Extraction failed: {e!s}",
                ).model_dump()
            ), 400
    else:
        raw_text = req.text

    cleaned_text = TextCleaner.clean(raw_text)
    if len(cleaned_text.strip()) < 30:
        return jsonify(
            ApiResponse.fail(
                code=ErrorCodes.TEXT_TOO_SHORT,
                message="Article content is too short to summarize (minimum 30 characters).",
            ).model_dump()
        ), 400

    content_hash = compute_content_hash(cleaned_text)

    # 2. Detect Language
    lang_info = LanguageDetector.detect(cleaned_text)
    source_lang = lang_info["language_code"]
    effective_target_lang = source_lang if target_lang == "auto" else target_lang

    # 3. Classify Topic & Reading Time
    topic_info = TopicClassifier.classify(cleaned_text)
    orig_words = len(cleaned_text.split())
    reading_time = f"~{max(1, round(orig_words / 200))} min read"

    # 4. Multilingual Summarization
    try:
        summ_res = multilingual_summarizer.summarize(
            text=cleaned_text,
            source_lang=source_lang,
            target_lang=effective_target_lang,
            length_profile=req.length_profile,
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Multilingual summarization failure: {e!s}")
        return jsonify(
            ApiResponse.fail(
                code=ErrorCodes.SUMMARIZATION_FAILED,
                message=f"Summarization pipeline failed: {e!s}",
            ).model_dump()
        ), 500

    total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    summary_words = len(summ_res["summary"].split())
    comp_ratio = round((summary_words / max(1, orig_words)) * 100.0, 1)

    # 5. Database Persistence
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
                language=source_lang,
                word_count=orig_words,
            )
            article_repo.create(db_article)

        db_summary = Summary(
            article_id=db_article.id,
            summary_type=summ_res["pipeline_type"],
            length_profile=req.length_profile,
            text=summ_res["summary"],
            compression_ratio=comp_ratio,
            processing_time_ms=total_latency_ms,
            model_name=summ_res["model_name"],
        )
        summary_repo.create_summary(db_summary)
        summary_id = db_summary.id
        persisted_article_id = db_article.id
        persisted_article_title = db_article.title
        persisted_article_url = db_article.url

    response_data = {
        "summary_id": summary_id,
        "article_id": persisted_article_id,
        "summary": summ_res["summary"],
        "length_profile": req.length_profile,
        "compression_ratio": comp_ratio,
        "processing_time_ms": total_latency_ms,
        "model_name": summ_res["model_name"],
        "language": effective_target_lang,
        "source_language": source_lang,
        "language_name": lang_info["language_name"],
        "original_title": persisted_article_title,
        "original_url": persisted_article_url,
        "word_count": orig_words,
        "summary_word_count": summary_words,
        "reading_time": reading_time,
        "topic": topic_info["category"],
        "quality": summ_res.get("quality", {}),
    }

    return jsonify(ApiResponse.ok(response_data).model_dump()), 200


@summarization_bp.route("/api/summaries/<summary_id>", methods=["GET"])
def get_summary_by_id(summary_id: str):
    """Retrieves an existing summary by its unique identifier."""
    with get_db_session() as session:
        summary_repo = SummaryRepository(session)
        summary = summary_repo.get_by_id(summary_id)
        if not summary:
            return jsonify(
                ApiResponse.fail(
                    code=ErrorCodes.RESOURCE_NOT_FOUND,
                    message=f"Summary with ID '{summary_id}' not found.",
                ).model_dump()
            ), 404

        article = summary.article
        data = {
            **summary.to_dict(),
            "article": article.to_dict() if article else None,
            "translations": [t.to_dict() for t in summary.translations],
        }
        return jsonify(ApiResponse.ok(data).model_dump()), 200
