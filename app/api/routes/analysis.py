"""Intelligence Analysis REST API route."""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.api.schemas.analysis import AnalyzeRequest
from app.api.schemas.common import ApiResponse
from app.services.article_extractor import ArticleExtractor, ArticleExtractionError
from app.services.text_cleaner import TextCleaner
from app.services.sentiment_analyzer import SentimentAnalyzer
from app.services.keypoint_extractor import KeypointExtractor
from app.services.keyword_extractor import KeywordExtractor
from app.services.entity_extractor import EntityExtractor
from app.db import get_db_session
from app.repositories.article_repo import ArticleRepository
from app.repositories.summary_repo import SummaryRepository
from app.models.analysis import AnalysisResult
from app.utils.cache import compute_content_hash
from app.constants import ErrorCodes
from app.utils.logger import logger

analysis_bp = Blueprint("analysis_api", __name__)
extractor = ArticleExtractor()
sentiment_analyzer = SentimentAnalyzer()
keypoint_extractor = KeypointExtractor()
keyword_extractor = KeywordExtractor()
entity_extractor = EntityExtractor()

@analysis_bp.route("/api/analyze", methods=["POST"])
def analyze_article():
    """Extracts sentiment distribution, MMR key points, keywords, and entities from article."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        req = AnalyzeRequest(**data)
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

    if req.url:
        try:
            extracted = extractor.extract(req.url)
            raw_text = extracted["text"]
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
            message="Article content is too short for analysis."
        ).model_dump()), 400

    content_hash = compute_content_hash(cleaned_text)

    # 1. Run Intelligence Pipeline
    sentiment = sentiment_analyzer.analyze(cleaned_text)
    key_points = keypoint_extractor.extract_key_points(cleaned_text, top_n=req.num_key_points)
    keywords = keyword_extractor.extract_keywords(cleaned_text, top_n=8)
    entities = entity_extractor.extract_entities(cleaned_text)

    # 2. Persist to DB if associated with existing article
    with get_db_session() as session:
        article_repo = ArticleRepository(session)
        summary_repo = SummaryRepository(session)
        db_article = article_repo.get_by_content_hash(content_hash)

        if db_article:
            existing_analysis = summary_repo.get_analysis_by_article_id(db_article.id)
            if not existing_analysis:
                analysis_rec = AnalysisResult(
                    article_id=db_article.id,
                    sentiment_label=sentiment["label"],
                    sentiment_score=sentiment["score"],
                    sentiment_distribution=sentiment["distribution"],
                    key_points=key_points,
                    keywords=keywords,
                    entities=entities,
                )
                summary_repo.create_analysis(analysis_rec)

    response_payload = {
        "sentiment": sentiment,
        "key_points": key_points,
        "keywords": keywords,
        "entities": entities,
    }
    return jsonify(ApiResponse.ok(response_payload).model_dump()), 200
