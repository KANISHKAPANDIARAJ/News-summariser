"""Translation REST API route with quality validation and fallback routing."""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.api.schemas.analysis import TranslateRequest
from app.api.schemas.common import ApiResponse
from app.services.translation_manager import get_translation_manager, TranslationPairError, TranslationValidationError
from app.constants import ErrorCodes, SUPPORTED_LANGUAGES

translation_bp = Blueprint("translation_api", __name__)
translation_mgr = get_translation_manager()

@translation_bp.route("/api/translate", methods=["POST"])
def translate_content():
    """Translates text to a supported target language with quality validation."""
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
    source_lang = req.source_language.lower().strip()

    if target_lang not in SUPPORTED_LANGUAGES:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.UNSUPPORTED_LANGUAGE,
            message=f"Target language '{target_lang}' is not supported.",
            details={"supported_languages": list(SUPPORTED_LANGUAGES.keys())}
        ).model_dump()), 400

    try:
        res = translation_mgr.translate(req.text, src_lang=source_lang, tgt_lang=target_lang)
        return jsonify(ApiResponse.ok(res).model_dump()), 200
    except (TranslationPairError, TranslationValidationError) as te:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.TRANSLATION_FAILED,
            message=str(te)
        ).model_dump()), 400
    except Exception as e:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message=f"Translation failed: {str(e)}"
        ).model_dump()), 500
