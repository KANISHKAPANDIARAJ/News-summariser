"""Article extraction route."""

from flask import Blueprint, jsonify, request

from pydantic import ValidationError
from app.api.schemas.article import ArticleExtractRequest
from app.api.schemas.common import ApiResponse
from app.constants import ErrorCodes
from app.services.article_extractor import ArticleExtractionError, ArticleExtractor
from app.services.text_cleaner import TextCleaner
from app.utils.logger import logger

articles_bp = Blueprint("articles_api", __name__)
extractor = ArticleExtractor()

@articles_bp.route("/api/articles/extract", methods=["POST"])
def extract_article():
    """Extracts raw and cleaned article text and metadata from a given URL."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        req = ArticleExtractRequest(**data)
    except ValidationError as ve:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Invalid request payload.",
            details=ve.errors()
        ).model_dump()), 422

    try:
        extracted = extractor.extract(req.url)
        cleaned_text = TextCleaner.clean(extracted["text"])
        words = len(cleaned_text.split())

        result = {
            **extracted,
            "raw_text": extracted["text"],
            "cleaned_text": cleaned_text,
            "word_count": words,
        }
        return jsonify(ApiResponse.ok(result).model_dump()), 200

    except ArticleExtractionError as ee:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.ARTICLE_EXTRACTION_FAILED,
            message=str(ee)
        ).model_dump()), 400
    except Exception as e:  # noqa: BLE001
        logger.error(f"Unexpected error during article extraction: {e!s}")
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message="An internal server error occurred while extracting the article."
        ).model_dump()), 500
