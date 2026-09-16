"""Multilingual Language Detection service combining script analysis and statistical language modeling."""

import re
from typing import Dict, Any
import langdetect
from langdetect import DetectorFactory
from app.utils.logger import logger

# Enforce deterministic results from langdetect
DetectorFactory.seed = 0

LANGUAGE_METADATA = {
    "en": {"name": "English", "native": "English", "script": "Latin"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "script": "Tamil"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "script": "Devanagari"},
    "bn": {"name": "Bengali", "native": "বাংলা", "script": "Bengali"},
    "mr": {"name": "Marathi", "native": "मராठी", "script": "Devanagari"},
    "te": {"name": "Telugu", "native": "తెలుగు", "script": "Telugu"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "script": "Kannada"},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "script": "Malayalam"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "script": "Gujarati"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "script": "Gurmukhi"},
    "fr": {"name": "French", "native": "Français", "script": "Latin"},
    "de": {"name": "German", "native": "Deutsch", "script": "Latin"},
    "es": {"name": "Spanish", "native": "Español", "script": "Latin"},
    "it": {"name": "Italian", "native": "Italiano", "script": "Latin"},
    "pt": {"name": "Portuguese", "native": "Português", "script": "Latin"},
    "ru": {"name": "Russian", "native": "Русский", "script": "Cyrillic"},
    "zh": {"name": "Chinese", "native": "中文", "script": "Han"},
    "ja": {"name": "Japanese", "native": "日本語", "script": "Japanese"},
    "ko": {"name": "Korean", "native": "한국어", "script": "Hangul"},
    "ar": {"name": "Arabic", "native": "العربية", "script": "Arabic"},
}

# Unicode Script Ranges
SCRIPT_RANGES = [
    (re.compile(r"[\u0B80-\u0BFF]"), "ta"),  # Tamil
    (re.compile(r"[\u0980-\u09FF]"), "bn"),  # Bengali
    (re.compile(r"[\u0C00-\u0C7F]"), "te"),  # Telugu
    (re.compile(r"[\u0C80-\u0CFF]"), "kn"),  # Kannada
    (re.compile(r"[\u0D00-\u0D7F]"), "ml"),  # Malayalam
    (re.compile(r"[\u0A80-\u0AFF]"), "gu"),  # Gujarati
    (re.compile(r"[\u0A00-\u0A7F]"), "pa"),  # Punjabi
    (re.compile(r"[\u0600-\u06FF]"), "ar"),  # Arabic
    (re.compile(r"[\u0400-\u04FF]"), "ru"),  # Cyrillic (Russian)
    (re.compile(r"[\u3040-\u30FF]"), "ja"),  # Japanese (Hiragana/Katakana)
    (re.compile(r"[\uAC00-\uD7AF]"), "ko"),  # Korean (Hangul)
    (re.compile(r"[\u4E00-\u9FFF]"), "zh"),  # Chinese (Han)
    (re.compile(r"[\u0900-\u097F]"), "hi"),  # Devanagari (Hindi/Marathi)
]


class LanguageDetector:
    """Robust content-based language detector with script heuristics and fallback modeling."""

    @classmethod
    def detect(cls, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "language_code": "en",
                "language_name": "English",
                "native_name": "English",
                "confidence": 1.0,
                "detection_method": "default_fallback",
            }

        sample = text[:3000].strip()

        # 1. Non-Latin Script Detection via Unicode code points (100% deterministic for distinct scripts)
        for pattern, lang_code in SCRIPT_RANGES:
            matches = len(pattern.findall(sample))
            # If at least 15 characters match this distinct script, it's overwhelmingly that language
            if matches >= 15:
                # Disambiguate Devanagari (Hindi vs Marathi) if lang_code is 'hi'
                if lang_code == "hi":
                    try:
                        detected_langs = langdetect.detect_langs(sample)
                        if detected_langs:
                            top = detected_langs[0]
                            if top.lang in ("hi", "mr") and top.prob > 0.8:
                                lang_code = top.lang
                    except Exception:
                        pass

                meta = LANGUAGE_METADATA.get(
                    lang_code, {"name": lang_code.upper(), "native": lang_code}
                )
                return {
                    "language_code": lang_code,
                    "language_name": meta["name"],
                    "native_name": meta["native"],
                    "confidence": 0.99,
                    "detection_method": "unicode_script_analysis",
                }

        # 2. Statistical Language Detection via langdetect (for Latin and shared alphabets)
        try:
            detected_langs = langdetect.detect_langs(sample)
            if detected_langs:
                top = detected_langs[0]
                lang_code = top.lang.lower()

                # Map common dialect codes (e.g. zh-cn -> zh)
                if lang_code.startswith("zh"):
                    lang_code = "zh"

                meta = LANGUAGE_METADATA.get(
                    lang_code, {"name": lang_code.upper(), "native": lang_code}
                )
                return {
                    "language_code": lang_code,
                    "language_name": meta.get("name", lang_code),
                    "native_name": meta.get("native", lang_code),
                    "confidence": round(float(top.prob), 3),
                    "detection_method": "statistical_langdetect",
                }
        except Exception as e:
            logger.warning(f"Statistical language detection exception: {e}")

        # 3. Fallback to English
        return {
            "language_code": "en",
            "language_name": "English",
            "native_name": "English",
            "confidence": 0.50,
            "detection_method": "heuristic_fallback",
        }
