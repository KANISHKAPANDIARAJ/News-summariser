"""Report generation endpoints for PDF download."""

import io
from flask import Blueprint, request, send_file, jsonify
from app.db import get_db_session
from app.repositories.summary_repo import SummaryRepository
from app.services.pdf_report import PDFReportGenerator
from app.api.schemas.common import ApiResponse
from app.constants import ErrorCodes
from app.utils.logger import logger

reports_bp = Blueprint("reports_api", __name__)

@reports_bp.route("/api/reports/<summary_id>/pdf", methods=["GET"])
def download_summary_pdf(summary_id: str):
    """Generates and serves a downloadable Unicode PDF report for a stored summary."""
    lang = request.args.get("lang", "en").lower().strip()

    with get_db_session() as session:
        repo = SummaryRepository(session)
        summary = repo.get_by_id(summary_id)
        if not summary:
            return jsonify(ApiResponse.fail(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"Summary with ID '{summary_id}' not found."
            ).model_dump()), 404

        article = summary.article
        analysis = repo.get_analysis_by_article_id(article.id) if article else None

        # Check if requested translated text exists
        display_summary = summary.text
        if lang != "en":
            trans = repo.get_translation(summary.id, lang)
            if trans:
                display_summary = trans.translated_text

        # Compute dynamic stats
        orig_words = article.word_count if article else len(article.cleaned_text.split()) if article else 0
        summ_words = len(display_summary.split())
        comp_ratio = summary.compression_ratio or round((1.0 - (summ_words / max(1, orig_words))) * 100.0, 1)

        data = {
            "title": article.title if article else "News Intelligence Briefing",
            "url": article.url if article else None,
            "publisher": article.publisher if article else "News Source",
            "author": article.author if article else None,
            "published_date": article.published_date if article else None,
            "language_name": lang.upper(),
            "summary": display_summary,
            "key_points": analysis.key_points if analysis else [],
            "sentiment": {
                "label": analysis.sentiment_label if analysis else "neutral",
                "score": analysis.sentiment_score if analysis else 1.0,
                "distribution": analysis.sentiment_distribution if analysis else {"positive": 0.33, "neutral": 0.34, "negative": 0.33},
            },
            "entities": analysis.entities if analysis else [],
            "keywords": analysis.keywords if analysis else [],
            "word_count": orig_words,
            "summary_word_count": summ_words,
            "compression_ratio": comp_ratio,
            "processing_time_ms": summary.processing_time_ms or 1200,
            "reading_time": f"~{max(1, round(orig_words / 200))} min read",
        }

        try:
            pdf_bytes = PDFReportGenerator.generate_report(data, target_language=lang)
            safe_filename = f"news_report_{summary_id[:8]}_{lang}.pdf"
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype="application/pdf",
                as_attachment=True,
                download_name=safe_filename
            )
        except Exception as e:
            logger.error(f"Error generating PDF report for {summary_id}: {e}")
            return jsonify(ApiResponse.fail(
                code="PDF_GENERATION_FAILED",
                message=f"Failed to generate PDF: {str(e)}"
            ).model_dump()), 500

@reports_bp.route("/api/reports/pdf", methods=["POST"])
def generate_dynamic_pdf():
    """Generates PDF directly from submitted analysis payload."""
    payload = request.get_json(force=True, silent=True) or {}
    lang = payload.get("language", "en").lower().strip()

    try:
        pdf_bytes = PDFReportGenerator.generate_report(payload, target_language=lang)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"news_intelligence_report_{lang}.pdf"
        )
    except Exception as e:
        logger.error(f"Dynamic PDF generation error: {e}")
        return jsonify(ApiResponse.fail(
            code="PDF_GENERATION_FAILED",
            message=str(e)
        ).model_dump()), 500
