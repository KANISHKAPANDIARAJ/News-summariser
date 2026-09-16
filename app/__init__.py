"""Application Factory for AI News Intelligence Platform."""

from pathlib import Path

from flask import Flask, jsonify
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.analysis import analysis_bp
from app.api.routes.articles import articles_bp
from app.api.routes.comparison import comparison_bp
from app.api.routes.health import health_bp
from app.api.routes.history import history_bp
from app.api.routes.jobs import jobs_bp
from app.api.routes.qa import qa_bp
from app.api.routes.reports import reports_bp
from app.api.routes.summarization import summarization_bp
from app.api.routes.translation import translation_bp
from app.api.routes.tts import tts_bp
from app.api.schemas.common import ApiResponse
from app.config import get_config
from app.constants import ErrorCodes
from app.db import init_db
from app.utils.logger import logger
from app.web.routes import web_bp


def create_app(config_class=None) -> Flask:
    """Application Factory creating and configuring the Flask application."""
    root_dir = Path(__file__).resolve().parent.parent
    templates_dir = root_dir / "templates"
    static_dir = root_dir / "static"

    app = Flask(
        __name__,
        template_folder=str(templates_dir),
        static_folder=str(static_dir),
    )

    # Load Configuration
    if config_class is None:
        cfg = get_config()
        app.config.from_object(cfg)
    else:
        app.config.from_object(config_class)

    # Initialize Database Tables
    with app.app_context():
        try:
            init_db()
            logger.info("Database schema initialized successfully.")
        except SQLAlchemyError as e:
            logger.error(f"Error initializing database schema: {e!s}")

    # Register Blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(articles_bp)
    app.register_blueprint(summarization_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(translation_bp)
    app.register_blueprint(tts_bp)
    app.register_blueprint(comparison_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(qa_bp)

    # Security Headers Middleware
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # Global Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        if hasattr(app, "test_client") and "api/" in getattr(e, "description", ""):
            return jsonify(ApiResponse.fail(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message="Resource not found."
            ).model_dump()), 404
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.RESOURCE_NOT_FOUND,
            message="Endpoint or resource not found."
        ).model_dump()), 404

    @app.errorhandler(413)
    def handle_large_payload(e):
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Request payload exceeds maximum permitted size."
        ).model_dump()), 413

    @app.errorhandler(500)
    def handle_server_error(e):
        logger.error(f"Unhandled 500 internal server error: {e!s}")
        return jsonify(ApiResponse.fail(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message="An unexpected internal server error occurred."
        ).model_dump()), 500

    logger.info("News Intelligence Platform Application created successfully.")
    return app
