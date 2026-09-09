"""Translation REST API route."""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.api.schemas.analysis import TranslateRequest
from app.api.schemas.common import ApiResponse
from app.services.translator import TranslationService, TranslationError
from app.constants import ErrorCodes, SUPPORTED_LANGUAGES

translation_bp = Blueprint("translation_api", __name__)
translator = TranslationService()

@translation_bp.route("/api/translate", methods=["POST"])
def translate_content():
    """Translates text to a supported target language."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        req = TranslateRequest(**data)
    except ValidationError as ve:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Invalid request payload.",
            details=ve.errors()
        ).model_dump()), 422

    target_lang = req.target_language.lower().strip()
    if target_lang not in SUPPORTED_LANGUAGES:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.UNSUPPORTED_LANGUAGE,
            message=f"Language '{target_lang}' is not supported.",
            details={"supported_languages": list(SUPPORTED_LANGUAGES.keys())}
        ).model_dump()), 400

    try:
        res = translator.translate(req.text, target_lang=target_lang, source_lang=req.source_language)
        return jsonify(ApiResponse.ok(res).model_dump()), 200
    except TranslationError as te:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.TRANSLATION_FAILED,
            message=str(te)
        ).model_dump()), 500
