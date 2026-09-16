"""History management REST API routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.api.schemas.common import ApiResponse
from app.constants import ErrorCodes
from app.db import get_db_session
from app.repositories.summary_repo import SummaryRepository

history_bp = Blueprint("history_api", __name__)


@history_bp.route("/api/history", methods=["GET"])
def get_history():
    """Lists recent article summaries from persistent storage."""
    limit = min(int(request.args.get("limit", 15)), 50)
    with get_db_session() as session:
        repo = SummaryRepository(session)
        summaries = repo.list_recent_summaries(limit=limit)
        items = []
        for s in summaries:
            art = s.article
            items.append(
                {
                    "summary_id": s.id,
                    "article_id": s.article_id,
                    "title": art.title if art else "Direct Text",
                    "url": art.url if art else None,
                    "summary_preview": s.text[:120]
                    + ("..." if len(s.text) > 120 else ""),
                    "length_profile": s.length_profile,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
            )
        return jsonify(ApiResponse.ok(items).model_dump()), 200


@history_bp.route("/api/history/<summary_id>", methods=["DELETE"])
def delete_history_item(summary_id: str):
    """Deletes a summary record from persistent storage."""
    with get_db_session() as session:
        repo = SummaryRepository(session)
        deleted = repo.delete_summary(summary_id)
        if not deleted:
            return jsonify(
                ApiResponse.fail(
                    code=ErrorCodes.RESOURCE_NOT_FOUND,
                    message=f"Summary with ID '{summary_id}' not found.",
                ).model_dump()
            ), 404
        return jsonify(
            ApiResponse.ok({"deleted": True, "summary_id": summary_id}).model_dump()
        ), 200
