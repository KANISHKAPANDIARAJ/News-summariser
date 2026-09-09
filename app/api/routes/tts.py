"""Text-to-Speech REST API routes."""

from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, url_for
from pydantic import ValidationError
from app.api.schemas.analysis import TTSRequest
from app.api.schemas.common import ApiResponse
from app.services.tts_service import TTSService
from app.constants import ErrorCodes
from app.utils.logger import logger

tts_bp = Blueprint("tts_api", __name__)
tts_service = TTSService()

@tts_bp.route("/api/tts", methods=["POST"])
def generate_audio():
    """Generates or retrieves cached MP3 audio file for text."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        req = TTSRequest(**data)
    except ValidationError as ve:
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Invalid request payload.",
            details=ve.errors()
        ).model_dump()), 422

    try:
        audio_info = tts_service.generate_audio_file(req.text, lang=req.language)
        audio_url = f"/api/tts/audio/{audio_info['filename']}"
        return jsonify(ApiResponse.ok({
            "filename": audio_info["filename"],
            "audio_url": audio_url,
            "language": audio_info["language"],
            "cached": audio_info["cached"],
            "size_bytes": audio_info["size_bytes"],
        }).model_dump()), 200
    except Exception as e:
        logger.error(f"TTS audio synthesis error: {e}")
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.TTS_GENERATION_FAILED,
            message=f"TTS synthesis failed: {str(e)}"
        ).model_dump()), 500

@tts_bp.route("/api/tts/audio/<filename>", methods=["GET"])
def stream_audio(filename: str):
    """Streams or downloads generated MP3 file."""
    # Prevent directory traversal
    safe_filename = Path(filename).name
    filepath = tts_service.cache_dir / safe_filename

    if not filepath.exists() or not filepath.is_file():
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.RESOURCE_NOT_FOUND,
            message="Audio file not found or expired."
        ).model_dump()), 404

    as_attachment = request.args.get("download", "false").lower() in ("true", "1")
    return send_file(
        filepath,
        mimetype="audio/mpeg",
        as_attachment=as_attachment,
        download_name=safe_filename
    )
