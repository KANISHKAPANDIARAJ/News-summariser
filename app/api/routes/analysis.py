"""Intelligence Analysis REST API route with multilingual support and framing signals."""

import re
from flask import Blueprint, jsonify, request

from pydantic import ValidationError
from app.api.schemas.analysis import AnalyzeRequest
from app.api.schemas.common import ApiResponse
from app.constants import ErrorCodes
from app.services.article_extractor import ArticleExtractionError, ArticleExtractor
from app.services.entity_extractor import EntityExtractor
from app.services.keypoint_extractor import KeypointExtractor
from app.services.keyword_extractor import KeywordExtractor
from app.services.language_detector import LanguageDetector
from app.services.sentiment_analyzer import SentimentAnalyzer
from app.services.text_cleaner import TextCleaner
from app.services.topic_classifier import TopicClassifier
from app.utils.logger import logger

analysis_bp = Blueprint("analysis_api", __name__)
extractor = ArticleExtractor()
sentiment_analyzer = SentimentAnalyzer()
keypoint_extractor = KeypointExtractor()
keyword_extractor = KeywordExtractor()
entity_extractor = EntityExtractor()

def compute_framing_signals(text: str) -> dict[str, str]:
    """Computes experimental linguistic framing indicators."""
    text_lower = text.lower()
    
    # Emotional / Sensational vocabulary
    sensational_words = ["shocking", "unbelievable", "disaster", "catastrophe", "massive", "unprecedented", "horrific", "explosive", "scandal"]
    sensational_count = sum(len(re.findall(rf"\b{w}\b", text_lower)) for w in sensational_words)
    
    # Attribution signals (quotes, according to, said, reported)
    attribution_words = ["said", "stated", "according to", "reported", "spokesperson", "officials", "confirmed", "announced", "கூறினார்", "தெரிவித்தார்"]
    attr_count = sum(len(re.findall(rf"\b{w}\b", text_lower)) for w in attribution_words)
    
    words_total = max(1, len(text.split()))
    
    attr_density = "High" if (attr_count / words_total) > 0.01 else "Moderate" if (attr_count / words_total) > 0.003 else "Low"
    sensational_level = "High" if sensational_count >= 3 else "Moderate" if sensational_count >= 1 else "Low"
    
    return {
        "sensational_language": sensational_level,
        "attribution_density": attr_density,
        "disclaimer": "Experimental linguistic framing indicators, not a factual determination of bias."
    }

@analysis_bp.route("/api/analyze", methods=["POST"])
def analyze_article():
    """Extracts sentiment distribution, MMR key points, keywords, entities, and framing signals."""
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
        except Exception as e:  # noqa: BLE001
            return jsonify(ApiResponse.fail(
                code=ErrorCodes.ARTICLE_EXTRACTION_FAILED,
                message=f"Extraction failed: {e!s}"
            ).model_dump()), 400
    else:
        raw_text = req.text

    cleaned_text = TextCleaner.clean(raw_text)
    if len(cleaned_text.strip()) < 30:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.TEXT_TOO_SHORT,
            message="Article content is too short for analysis."
        ).model_dump()), 400

    lang_info = LanguageDetector.detect(cleaned_text)
    topic_info = TopicClassifier.classify(cleaned_text)

    # 1. Run Intelligence Pipeline with error tolerance
    try:
        sentiment = sentiment_analyzer.analyze(cleaned_text)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Sentiment analysis warning: {e!s}")
        sentiment = {"label": "neutral", "score": 1.0, "distribution": {"positive": 0.33, "neutral": 0.34, "negative": 0.33}}

    try:
        key_points = keypoint_extractor.extract_key_points(cleaned_text, top_n=req.num_key_points)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Keypoint extraction warning: {e!s}")
        key_points = []

    try:
        keywords = keyword_extractor.extract_keywords(cleaned_text, top_n=8)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Keyword extraction warning: {e!s}")
        keywords = []

    try:
        entities = entity_extractor.extract_entities(cleaned_text)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Entity extraction warning: {e!s}")
        entities = []

    framing = compute_framing_signals(cleaned_text)

    response_payload = {
        "language": lang_info,
        "topic": topic_info,
        "sentiment": sentiment,
        "key_points": key_points,
        "keywords": keywords,
        "entities": entities,
        "framing_signals": framing,
    }
    return jsonify(ApiResponse.ok(response_payload).model_dump()), 200
