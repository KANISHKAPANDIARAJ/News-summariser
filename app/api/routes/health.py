"""Health check and readiness endpoints."""

from __future__ import annotations
import time

from flask import Blueprint, jsonify

from app.api.schemas.common import ApiResponse
from app.db import engine
from app.ml.model_manager import get_model_manager

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """Liveness probe: verifies basic server execution without triggering ML inference."""
    # Check DB connectivity
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
            db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False

    status = "healthy" if db_ok else "degraded"
    return jsonify(
        ApiResponse.ok(
            {
                "status": status,
                "database": "connected" if db_ok else "disconnected",
                "timestamp": int(time.time()),
                "version": "2.0.0",
            }
        ).model_dump()
    ), 200 if db_ok else 503


@health_bp.route("/api/ready", methods=["GET"])
def readiness_check():
    """Readiness probe: reports component readiness for traffic routing."""
    model_mgr = get_model_manager()
    return jsonify(
        ApiResponse.ok(
            {
                "status": "ready",
                "summarizer_loaded": model_mgr.is_summarizer_loaded(),
                "device": model_mgr.device,
            }
        ).model_dump()
    ), 200
