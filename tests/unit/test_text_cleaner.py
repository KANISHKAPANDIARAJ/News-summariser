"""Unit tests for TextCleaner service."""

from app.services.text_cleaner import TextCleaner

def test_unicode_normalization():
    raw = "Caf\u00e9\u200b and \u201cquotes\u201d"
    cleaned = TextCleaner.clean(raw)
    assert "Café" in cleaned
    assert "quotes" in cleaned

def test_html_stripping():
    raw = "<p>This is a paragraph.</p><script>alert('xss');</script> And another line."
    cleaned = TextCleaner.clean(raw)
    assert "<p>" not in cleaned
    assert "</p>" not in cleaned
    assert "This is a paragraph." in cleaned

def test_boilerplate_removal():
    paragraphs = [
        "Major economic indicators rose today across Asian markets.",
        "Subscribe to our newsletter for daily updates.",
        "Follow us on Twitter.",
        "The central bank held interest rates unchanged at 3.5%."
    ]
    cleaned = TextCleaner.remove_boilerplate(paragraphs)
    assert len(cleaned) == 2
    assert "Subscribe to our newsletter" not in cleaned[0]
    assert "Subscribe to our newsletter" not in cleaned[1]

def test_sentence_segmentation():
    text = "Dr. Elena Vance spoke at the summit. The event took place in Geneva! Did you hear about it? Yes, we did."
    sentences = TextCleaner.segment_sentences(text)
    assert len(sentences) == 4
    assert sentences[0].startswith("Dr. Elena Vance")

def test_language_detection():
    assert TextCleaner.detect_language("செய்திகள் மற்றும் புதிய தகவல்கள்") == "ta"
    assert TextCleaner.detect_language("यह एक महत्वपूर्ण समाचार है।") == "hi"
    assert TextCleaner.detect_language("This is an English breaking news update.") == "en"
