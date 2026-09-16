"""Application Constants and Registries.

Defines supported languages, summary length profiles, and structured error codes.
"""

from typing import Dict

# Supported translation languages and their models
# Only languages with an actual verified backend translation model are listed
SUPPORTED_LANGUAGES: Dict[str, Dict[str, str]] = {
    "en": {"name": "English", "native": "English", "model": None},
    "ta": {"name": "Tamil", "native": "தமிழ்", "model": "suriya7/English-to-Tamil"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "model": "Helsinki-NLP/opus-mt-en-hi"},
    "fr": {
        "name": "French",
        "native": "Français",
        "model": "Helsinki-NLP/opus-mt-en-fr",
    },
    "de": {
        "name": "German",
        "native": "Deutsch",
        "model": "Helsinki-NLP/opus-mt-en-de",
    },
    "es": {
        "name": "Spanish",
        "native": "Español",
        "model": "Helsinki-NLP/opus-mt-en-es",
    },
    "it": {
        "name": "Italian",
        "native": "Italiano",
        "model": "Helsinki-NLP/opus-mt-en-it",
    },
    "pt": {
        "name": "Portuguese",
        "native": "Português",
        "model": "Helsinki-NLP/opus-mt-en-pt",
    },
    "ru": {
        "name": "Russian",
        "native": "Русский",
        "model": "Helsinki-NLP/opus-mt-en-ru",
    },
    "zh": {"name": "Chinese", "native": "中文", "model": "Helsinki-NLP/opus-mt-en-zh"},
    "ja": {
        "name": "Japanese",
        "native": "日本語",
        "model": "Helsinki-NLP/opus-mt-en-ja",
    },
    "ko": {"name": "Korean", "native": "한국어", "model": "Helsinki-NLP/opus-mt-en-ko"},
    "ar": {
        "name": "Arabic",
        "native": "العربية",
        "model": "Helsinki-NLP/opus-mt-en-ar",
    },
    "bn": {"name": "Bengali", "native": "বাংলা", "model": "Helsinki-NLP/opus-mt-en-bn"},
    "mr": {"name": "Marathi", "native": "मराठी", "model": "Helsinki-NLP/opus-mt-en-mr"},
}

SUMMARY_LENGTHS: Dict[str, Dict[str, int]] = {
    "short": {"min_length": 30, "max_length": 60},
    "medium": {"min_length": 60, "max_length": 120},
    "detailed": {"min_length": 120, "max_length": 250},
    # Backwards compatibility alias for older template
    "long": {"min_length": 120, "max_length": 250},
}


class ErrorCodes:
    INVALID_URL = "INVALID_URL"
    SSRF_BLOCKED = "SSRF_BLOCKED"
    ARTICLE_EXTRACTION_FAILED = "ARTICLE_EXTRACTION_FAILED"
    TEXT_TOO_SHORT = "TEXT_TOO_SHORT"
    SUMMARIZATION_FAILED = "SUMMARIZATION_FAILED"
    TRANSLATION_FAILED = "TRANSLATION_FAILED"
    UNSUPPORTED_LANGUAGE = "UNSUPPORTED_LANGUAGE"
    TTS_GENERATION_FAILED = "TTS_GENERATION_FAILED"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
