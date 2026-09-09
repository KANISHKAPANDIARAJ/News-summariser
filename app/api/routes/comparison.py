"""Semantic comparison and multi-source analysis routes."""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.api.schemas.analysis import CompareRequest, MultiSourceRequest
from app.api.schemas.common import ApiResponse
from app.services.comparison_service import ArticleComparisonService
from app.services.news_aggregator import MultiSourceAggregator
from app.constants import ErrorCodes
from app.utils.logger import logger

comparison_bp = Blueprint("comparison_api", __name__)
comparator = ArticleComparisonService()
aggregator = MultiSourceAggregator()

@comparison_bp.route("/api/compare", methods=["POST"])
def compare_articles():
    """Compares two articles semantically and highlights topical differences."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        req = CompareRequest(**data)
    except ValidationError as ve:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Invalid request payload.",
            details=ve.errors()
        ).model_dump()), 422

    try:
        res = comparator.compare(req.text_a, req.text_b)
        return jsonify(ApiResponse.ok(res).model_dump()), 200
    except Exception as e:
        logger.error(f"Article comparison failed: {e}")
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message=f"Comparison failed: {str(e)}"
        ).model_dump()), 500

@comparison_bp.route("/api/multi-source", methods=["POST"])
def multi_source_synthesis():
    """Synthesizes consensus and contrast across multiple news sources."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        req = MultiSourceRequest(**data)
    except ValidationError as ve:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Invalid request payload.",
            details=ve.errors()
        ).model_dump()), 422

    try:
        res = aggregator.analyze_sources(req.articles)
        return jsonify(ApiResponse.ok(res).model_dump()), 200
    except ValueError as ve:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.VALIDATION_ERROR,
            message=str(ve)
        ).model_dump()), 400
    except Exception as e:
        logger.error(f"Multi-source analysis failed: {e}")
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message=f"Multi-source analysis failed: {str(e)}"
        ).model_dump()), 500
