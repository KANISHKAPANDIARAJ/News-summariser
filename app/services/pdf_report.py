"""Professional PDF Intelligence Report Generator using ReportLab with full Unicode support."""

import io
from datetime import datetime, timezone
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from app.services.font_manager import FontManager


class PDFReportGenerator:
    """Generates clean, professional PDF intelligence reports supporting multilingual Unicode scripts."""

    @classmethod
    def generate_report(
        cls, data: Dict[str, Any], target_language: str = "en"
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        font_name = FontManager.get_font_for_language(target_language)
        title_font = font_name
        body_font = font_name

        # Styles
        styles = getSampleStyleSheet()

        # Custom Palette: Deep Amber / Emerald
        PRIMARY_COLOR = colors.HexColor("#78350f")  # amber-900
        SECONDARY_COLOR = colors.HexColor("#047857")  # emerald-700
        BG_LIGHT = colors.HexColor("#fffbeb")  # amber-50
        BORDER_COLOR = colors.HexColor("#fde68a")  # amber-200
        TEXT_DARK = colors.HexColor("#1e293b")  # slate-800
        MUTED_TEXT = colors.HexColor("#64748b")  # slate-500

        header_style = ParagraphStyle(
            "DocHeader",
            parent=styles["Normal"],
            fontName=title_font,
            fontSize=16,
            leading=20,
            textColor=PRIMARY_COLOR,
            fontStyle="Bold",
        )

        sub_header_style = ParagraphStyle(
            "SubHeader",
            parent=styles["Normal"],
            fontName="GeneralUnicode"
            if "GeneralUnicode" in styles["Normal"].fontName
            else body_font,
            fontSize=8,
            leading=11,
            textColor=MUTED_TEXT,
        )

        article_title_style = ParagraphStyle(
            "ArticleTitle",
            parent=styles["Normal"],
            fontName=title_font,
            fontSize=14,
            leading=18,
            textColor=PRIMARY_COLOR,
            fontStyle="Bold",
        )

        section_heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName=title_font,
            fontSize=10,
            leading=14,
            textColor=SECONDARY_COLOR,
            fontStyle="Bold",
        )

        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontName=body_font,
            fontSize=9.5,
            leading=14,
            textColor=TEXT_DARK,
        )

        meta_style = ParagraphStyle(
            "MetaStyle",
            parent=styles["Normal"],
            fontName=body_font,
            fontSize=8,
            leading=11,
            textColor=TEXT_DARK,
        )

        elements = []

        # 1. Header Bar Table
        now_str = datetime.now(timezone.utc).strftime("%B %d, %Y - %H:%M UTC")
        header_text = Paragraph("<b>AI NEWS INTELLIGENCE REPORT</b>", header_style)
        sub_text = Paragraph(
            f"Generated: {now_str} • Pipeline: V2.1 Production", sub_header_style
        )

        header_table = Table(
            [
                [
                    header_text,
                    Paragraph(
                        "<font color='#047857'><b>VERIFIED ANALYSIS</b></font>",
                        sub_header_style,
                    ),
                ],
                [sub_text, ""],
            ],
            colWidths=[400, 140],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elements.append(header_table)
        elements.append(
            HRFlowable(
                width="100%",
                thickness=1.5,
                color=PRIMARY_COLOR,
                spaceBefore=4,
                spaceAfter=8,
            )
        )

        # 2. Article Title & Source Metadata
        raw_title = data.get("title") or "Untitled News Article"
        prep_title = FontManager.prepare_text(raw_title, target_language)
        elements.append(Paragraph(prep_title, article_title_style))
        elements.append(Spacer(1, 4))

        meta_rows = [
            [
                Paragraph(
                    f"<b>Source:</b> {data.get('publisher') or 'Web Publication'}",
                    meta_style,
                ),
                Paragraph(
                    f"<b>Language:</b> {data.get('language_name') or target_language.upper()}",
                    meta_style,
                ),
                Paragraph(
                    f"<b>Reading Time:</b> {data.get('reading_time') or '~3 min read'}",
                    meta_style,
                ),
            ],
            [
                Paragraph(
                    f"<b>Author:</b> {data.get('author') or 'Not available'}",
                    meta_style,
                ),
                Paragraph(
                    f"<b>Published:</b> {data.get('published_date') or 'Recent'}",
                    meta_style,
                ),
                Paragraph(
                    f"<b>Word Count:</b> {data.get('word_count', 'N/A')}", meta_style
                ),
            ],
        ]
        meta_table = Table(meta_rows, colWidths=[180, 180, 180])
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(meta_table)
        elements.append(Spacer(1, 8))

        # 3. Summary Card
        elements.append(Paragraph("<b>ABSTRACTIVE SUMMARY</b>", section_heading_style))
        elements.append(Spacer(1, 2))
        summary_raw = data.get("summary") or "Summary not available."
        summary_prep = FontManager.prepare_text(summary_raw, target_language)

        summary_table = Table([[Paragraph(summary_prep, body_style)]], colWidths=[540])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(summary_table)
        elements.append(Spacer(1, 8))

        # 4. MMR Key Points
        key_points = data.get("key_points", [])
        if key_points:
            elements.append(
                Paragraph("<b>KEY POINTS (MMR RANKED)</b>", section_heading_style)
            )
            elements.append(Spacer(1, 2))
            kp_rows = []
            for kp in key_points[:4]:
                kp_text = kp.get("text", "") if isinstance(kp, dict) else str(kp)
                prep_kp = FontManager.prepare_text(kp_text, target_language)
                kp_rows.append(
                    [Paragraph("•", body_style), Paragraph(prep_kp, body_style)]
                )
            kp_table = Table(kp_rows, colWidths=[15, 525])
            kp_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            elements.append(kp_table)
            elements.append(Spacer(1, 8))

        # 5. Sentiment Spectrum & Performance Stats Table (side-by-side)
        sentiment = data.get("sentiment", {})
        dist = sentiment.get("distribution", {}) if isinstance(sentiment, dict) else {}
        pos = int(dist.get("positive", 0) * 100)
        neu = int(dist.get("neutral", 0) * 100)
        neg = int(dist.get("negative", 0) * 100)
        dominant = (
            sentiment.get("label", "neutral")
            if isinstance(sentiment, dict)
            else "neutral"
        )

        ratio = data.get("compression_ratio", 0)
        latency = data.get("processing_time_ms", 0)
        lat_sec = f"{latency / 1000:.1f}s" if latency else "N/A"

        analysis_grid = [
            [
                Paragraph("<b>DOCUMENT SENTIMENT</b>", section_heading_style),
                Paragraph("<b>PIPELINE PERFORMANCE METRICS</b>", section_heading_style),
            ],
            [
                Paragraph(
                    f"Dominant Polarity: <b>{dominant.upper()}</b><br/>Positive: {pos}% | Neutral: {neu}% | Negative: {neg}%",
                    body_style,
                ),
                Paragraph(
                    f"Original Words: <b>{data.get('word_count', 'N/A')}</b> | Summary Words: <b>{data.get('summary_word_count', 'N/A')}</b><br/>Compression Ratio: <b>{ratio}%</b> | Processing Latency: <b>{lat_sec}</b>",
                    body_style,
                ),
            ],
        ]
        grid_table = Table(analysis_grid, colWidths=[270, 270])
        grid_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND", (0, 1), (0, 1), BG_LIGHT),
                    ("BACKGROUND", (1, 1), (1, 1), BG_LIGHT),
                    ("BOX", (0, 1), (0, 1), 0.5, BORDER_COLOR),
                    ("BOX", (1, 1), (1, 1), 0.5, BORDER_COLOR),
                    ("TOPPADDING", (0, 1), (-1, 1), 4),
                    ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
                    ("LEFTPADDING", (0, 1), (-1, 1), 6),
                    ("RIGHTPADDING", (0, 1), (-1, 1), 6),
                ]
            )
        )
        elements.append(grid_table)
        elements.append(Spacer(1, 8))

        # 6. Named Entities & Keywords
        entities = data.get("entities", [])
        keywords = data.get("keywords", [])

        if entities or keywords:
            ent_list = (
                [f"{e.get('text')} ({e.get('label')})" for e in entities[:6]]
                if entities
                else ["None detected"]
            )
            kw_list = [f"#{k}" for k in keywords[:6]] if keywords else ["None detected"]

            tags_grid = [
                [
                    Paragraph("<b>NAMED ENTITIES</b>", section_heading_style),
                    Paragraph("<b>SALIENT KEYWORDS</b>", section_heading_style),
                ],
                [
                    Paragraph(", ".join(ent_list), body_style),
                    Paragraph("  ".join(kw_list), body_style),
                ],
            ]
            tags_table = Table(tags_grid, colWidths=[270, 270])
            tags_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            elements.append(tags_table)
            elements.append(Spacer(1, 8))

        # 7. Disclaimer & Canonical Source
        source_url = data.get("url") or "Manual Text Submission"
        elements.append(
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=BORDER_COLOR,
                spaceBefore=4,
                spaceAfter=4,
            )
        )
        disclaimer_p = Paragraph(
            f"<b>Source URL:</b> {source_url}<br/>"
            "<b>Disclaimer:</b> AI-generated news intelligence briefing. Tonal sentiment and model summaries are synthesized interpretations and must be verified against original reporting.",
            sub_header_style,
        )
        elements.append(disclaimer_p)

        # Build Document
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
