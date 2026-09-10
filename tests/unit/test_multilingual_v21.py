"""Unit tests for V2.1 Multilingual NLP, PDF generation, Q&A, and Language Detection."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.language_detector import LanguageDetector
from app.services.translation_manager import TranslationManager, TranslationValidationError
from app.services.pdf_report import PDFReportGenerator
from app.services.qa_service import ArticleQAService
from app.services.topic_classifier import TopicClassifier
from app.services.multilingual_summarizer import MultilingualSummarizer

def test_language_detector_multilingual():
    # Tamil
    res_ta = LanguageDetector.detect("கோவை மாவட்டத்தில் நாளை மின்தடை ஏற்படும் என அறிவிப்பு.")
    assert res_ta["language_code"] == "ta"
    assert res_ta["confidence"] > 0.9

    # Hindi
    res_hi = LanguageDetector.detect("दिल्ली में मौसम विभाग ने भारी बारिश की चेतावनी जारी की है।")
    assert res_hi["language_code"] == "hi"
    assert res_hi["confidence"] > 0.9

    # English
    res_en = LanguageDetector.detect("Stock markets rally following favorable inflation data.")
    assert res_en["language_code"] == "en"

def test_translation_validation():
    tm = TranslationManager()
    # Valid output
    assert tm.validate_translation_output("Hello", "வணக்கம் நண்பா", "en", "ta") is True

    # Bad token rejection
    try:
        tm.validate_translation_output("Hello", "This has <unk> token", "en", "en")
        assert False, "Failed to reject <unk>"
    except TranslationValidationError:
        pass

    # Empty rejection
    try:
        tm.validate_translation_output("Hello", "   ", "en", "ta")
        assert False, "Failed to reject empty output"
    except TranslationValidationError:
        pass

def test_pdf_report_generation_tamil():
    data = {
        "title": "கோவை மின்வாரியம் அறிவிப்பு",
        "publisher": "ABP Live",
        "author": "செய்தியாளர்",
        "published_date": "10-09-2026",
        "language_name": "Tamil",
        "summary": "கோவையில் நாளை காலை 9 மணி முதல் மாலை 4 மணி வரை மின் பாதையில் பராமரிப்புப் பணிகள் காரணமாக மின்தடை ஏற்படும்.",
        "key_points": [{"text": "காலை 9 முதல் மாலை 4 வரை மின்சாரம் நிறுத்தப்படும்."}],
        "sentiment": {"label": "neutral", "distribution": {"positive": 0.2, "neutral": 0.7, "negative": 0.1}},
        "entities": [{"text": "கோவை", "label": "LOCATION"}],
        "keywords": ["மின்சாரம்", "கோவை"],
        "word_count": 120,
        "summary_word_count": 22,
        "compression_ratio": 81.6,
        "processing_time_ms": 1100,
        "reading_time": "~1 min read",
    }
    pdf_bytes = PDFReportGenerator.generate_report(data, target_language="ta")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")

def test_pdf_report_generation_english():
    data = {
        "title": "Tech Summit 2026",
        "publisher": "Tech Daily",
        "summary": "Researchers announced major breakthroughs in long-document abstractive summarization.",
        "key_points": [{"text": "Hierarchical Map-Reduce eliminates context loss."}],
        "sentiment": {"label": "positive", "distribution": {"positive": 0.8, "neutral": 0.15, "negative": 0.05}},
        "word_count": 200,
        "summary_word_count": 15,
        "compression_ratio": 92.5,
    }
    pdf_bytes = PDFReportGenerator.generate_report(data, target_language="en")
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 2000

def test_article_qa_service():
    article = (
        "The city electricity board announced that a scheduled power shutdown will take place on September 10, 2026. "
        "The outage will affect Coimbatore Central, Gandhipuram, and RS Puram. "
        "Power will be restored by 4 PM following essential line maintenance."
    )
    ans = ArticleQAService.answer_question(article, "When will power be restored?")
    assert "4 PM" in ans["answer"]
    assert ans["confidence"] > 0.3

def test_topic_classifier():
    tech_text = "Nvidia and OpenAI announced a partnership to deploy advanced GPU compute clusters."
    assert TopicClassifier.classify(tech_text)["category"] in ("Technology", "AI")

    local_text = "District authorities announced a power cut and electricity shutdown for line maintenance."
    assert TopicClassifier.classify(local_text)["category"] == "Local News"

def test_quality_score_calculation():
    ms = MultilingualSummarizer()
    good_summary = "Coimbatore electricity department announced maintenance shutdown on Thursday."
    score = ms.calculate_quality_score(good_summary, good_summary * 3, "en")
    assert score["level"] == "good"
    assert score["score"] >= 0.75
