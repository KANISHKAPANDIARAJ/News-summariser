"""Comprehensive End-to-End Acceptance Test on ABP Live Tamil Article and English Regression."""

import sys
import json
from pathlib import Path

# Configure UTF-8 for console output on Windows
sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.services.article_extractor import ArticleExtractor
from app.services.language_detector import LanguageDetector
from app.services.multilingual_summarizer import MultilingualSummarizer
from app.services.pdf_report import PDFReportGenerator
from app.services.qa_service import ArticleQAService
from app.services.keypoint_extractor import KeypointExtractor
from app.services.sentiment_analyzer import SentimentAnalyzer
from app.services.entity_extractor import EntityExtractor
from app.services.keyword_extractor import KeywordExtractor

TAMIL_URL = "https://tamil.abplive.com/news/coimbatore/coimbatore-power-cut-10-09-2026-know-timings-areas-affected-by-power-shutdown-274010"

ENGLISH_SAMPLE = """
DeepMind researchers announced a major milestone in autonomous artificial intelligence today in London. 
The team unveiled an adaptive transformer architecture capable of processing multi-modal streaming inputs with sub-second latency.
The breakthrough was presented at the International Computer Science Symposium on October 14, 2026.
Venture capital funding for foundational machine learning models reached $22 billion this fiscal quarter.
Industry executives emphasized that robust validation benchmarks and strict ethical safeguards remain top operational priorities.
"""

def main():
    print("=" * 70)
    print("  AI NEWS INTELLIGENCE PLATFORM V2.1: FULL ACCEPTANCE TEST")
    print("=" * 70)

    # -------------------------------------------------------------
    # TEST 1: TAMIL ACCEPTANCE TEST (ABP Live Article)
    # -------------------------------------------------------------
    print("\n[STEP 1] Extracting ABP Live Tamil Article...")
    extractor = ArticleExtractor()
    extracted = extractor.extract(TAMIL_URL)
    raw_text = extracted.get("text", "")
    title = extracted.get("title", "")
    print(f"✓ Title: {title}")
    print(f"✓ Character Count: {len(raw_text)}")
    assert len(raw_text) > 200, "Extracted text too short!"

    print("\n[STEP 2] Verifying Content-Based Language Detection...")
    lang_info = LanguageDetector.detect(raw_text)
    print(f"✓ Detected Language: {lang_info['language_code']} ({lang_info['language_name']})")
    print(f"✓ Confidence: {lang_info['confidence']}")
    assert lang_info["language_code"] == "ta", f"Expected 'ta', got {lang_info['language_code']}"

    print("\n[STEP 3] Running Multilingual Summarization Pipeline (Tamil -> English -> Tamil)...")
    summarizer = MultilingualSummarizer()
    summ_res = summarizer.summarize(raw_text, source_lang="ta", target_lang="ta", length_profile="medium")
    tamil_summary = summ_res["summary"]
    print("\n--- GENERATED TAMIL SUMMARY ---")
    print(tamil_summary)
    print("--------------------------------")
    print(f"✓ Pipeline Type: {summ_res['pipeline_type']}")
    print(f"✓ Compression Ratio: {summ_res['compression_ratio']}%")
    print(f"✓ Latency: {summ_res['processing_time_ms']} ms")
    print(f"✓ Quality Score: {summ_res['quality']['score']} ({summ_res['quality']['level']})")

    # Anti-gibberish checks
    assert len(tamil_summary) > 40, "Summary too short!"
    assert "10, 2026, - -2026" not in tamil_summary, "Malformed date token found in summary!"
    assert "form of form" not in tamil_summary, "Repetitive phrase found in summary!"
    assert summ_res["quality"]["score"] >= 0.60, f"Quality score too low: {summ_res['quality']}"

    print("\n[STEP 4] Extracting MMR Key Points in Tamil...")
    keypoint_ext = KeypointExtractor()
    key_points = keypoint_ext.extract_key_points(raw_text, top_n=3)
    for idx, kp in enumerate(key_points):
        print(f"  {idx + 1}. {kp['text']}")
    assert len(key_points) > 0, "No key points extracted!"

    print("\n[STEP 5] Extracting Entities, Keywords, and Sentiment...")
    ent_ext = EntityExtractor()
    kw_ext = KeywordExtractor()
    sent_analyzer = SentimentAnalyzer()

    entities = ent_ext.extract_entities(raw_text)
    keywords = kw_ext.extract_keywords(raw_text, top_n=6)
    sentiment = sent_analyzer.analyze(raw_text)
    print(f"✓ Top Entities: {[e['text'] for e in entities[:4]]}")
    print(f"✓ Top Keywords: {keywords}")
    print(f"✓ Sentiment: {sentiment['label']} (Distribution: {sentiment['distribution']})")

    print("\n[STEP 6] Testing Extractive Q&A on Tamil Article...")
    qa_res = ArticleQAService.answer_question(raw_text, "எந்த பகுதியில் மின் தடை?")
    print(f"✓ Question: எந்த பகுதியில் மின் தடை?")
    print(f"✓ Answer: {qa_res['answer']}")
    print(f"✓ Confidence: {qa_res['confidence']}")

    print("\n[STEP 7] Generating Unicode Tamil PDF Report with ReportLab...")
    pdf_data = {
        "title": title,
        "url": TAMIL_URL,
        "publisher": extracted.get("publisher", "ABP Live"),
        "author": extracted.get("author", "ABP News"),
        "published_date": "10-09-2026",
        "language_name": "Tamil",
        "summary": tamil_summary,
        "key_points": key_points,
        "sentiment": sentiment,
        "entities": entities,
        "keywords": keywords,
        "word_count": len(raw_text.split()),
        "summary_word_count": len(tamil_summary.split()),
        "compression_ratio": summ_res["compression_ratio"],
        "processing_time_ms": summ_res["processing_time_ms"],
        "reading_time": "~3 min read",
    }
    pdf_bytes = PDFReportGenerator.generate_report(pdf_data, target_language="ta")
    pdf_out_path = PROJECT_ROOT / "evaluation" / "acceptance_test_tamil.pdf"
    with open(pdf_out_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"✓ Successfully generated native Tamil PDF: {len(pdf_bytes)} bytes -> {pdf_out_path}")
    assert len(pdf_bytes) > 5000, "PDF file size too small!"

    # -------------------------------------------------------------
    # TEST 2: ENGLISH REGRESSION TEST
    # -------------------------------------------------------------
    print("\n[STEP 8] Running English Regression Test...")
    eng_lang = LanguageDetector.detect(ENGLISH_SAMPLE)
    assert eng_lang["language_code"] == "en"

    eng_summ_res = summarizer.summarize(ENGLISH_SAMPLE, source_lang="en", target_lang="en", length_profile="medium")
    print("--- GENERATED ENGLISH SUMMARY ---")
    print(eng_summ_res["summary"])
    print("----------------------------------")
    print(f"✓ Pipeline: {eng_summ_res['pipeline_type']}")
    print(f"✓ English Compression: {eng_summ_res['compression_ratio']}%")
    assert eng_summ_res["pipeline_type"] == "native_english"
    assert len(eng_summ_res["summary"]) > 50

    print("\n" + "=" * 70)
    print("  ALL V2.1 ACCEPTANCE CRITERIA PASSED WITH ZERO REGRESSIONS!")
    print("=" * 70)

if __name__ == "__main__":
    main()
