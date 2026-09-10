"""Article Q&A REST API route."""

from flask import Blueprint, request, jsonify
from app.api.schemas.common import ApiResponse
from app.services.qa_service import ArticleQAService
from app.services.article_extractor import ArticleExtractor
from app.services.text_cleaner import TextCleaner
from app.constants import ErrorCodes

qa_bp = Blueprint("qa_api", __name__)
extractor = ArticleExtractor()

@qa_bp.route("/api/article/ask", methods=["POST"])
def ask_article():
    """Answers factual questions directly grounded in the article content."""
    payload = request.get_json(force=True, silent=True) or {}
    question = payload.get("question", "").strip()
    article_text = payload.get("text", "").strip()
    url = payload.get("url", "").strip()

    if not question:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Question cannot be empty."
        ).model_dump()), 400

    if not article_text and url:
        try:
            extracted = extractor.extract(url)
            article_text = extracted.get("text", "")
        except Exception as e:
            return jsonify(ApiResponse.fail(
                code=ErrorCodes.ARTICLE_EXTRACTION_FAILED,
                message=f"Could not extract article: {e}"
            ).model_dump()), 400

    cleaned = TextCleaner.clean(article_text)
    res = ArticleQAService.answer_question(cleaned, question)
    return jsonify(ApiResponse.ok(res).model_dump()), 200
