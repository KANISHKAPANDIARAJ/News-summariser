"""Text cleaning, normalization, boilerplate removal, and sentence segmentation."""

import re
import unicodedata
from typing import List

# Common news boilerplate patterns
BOILERPLATE_PATTERNS = [
    r"(?i)subscribe to (our )?(newsletter|updates)",
    r"(?i)follow us on (twitter|facebook|instagram|linkedin|threads)",
    r"(?i)all rights reserved\b.*",
    r"(?i)click here to read more",
    r"(?i)sign up for (free|the daily digest)",
    r"(?i)advertisement\b",
    r"(?i)share this (article|story) on\b.*",
    r"(?i)cookie policy|privacy policy|terms of service",
    r"(?i)we use cookies to improve your experience",
    r"(?i)photo by [^.\n]+",
]


class TextCleaner:
    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Normalizes unicode characters using NFKC format."""
        return unicodedata.normalize("NFKC", text)

    @staticmethod
    def strip_html(text: str) -> str:
        """Removes residual HTML tags and unescapes entities."""
        clean = re.sub(r"<[^>]+>", " ", text)
        clean = re.sub(r"&[a-zA-Z]+;", " ", clean)
        return clean

    @staticmethod
    def remove_boilerplate(paragraphs: List[str]) -> List[str]:
        """Removes short boilerplate paragraphs like share buttons, ads, and newsletter calls."""
        cleaned = []
        for p in paragraphs:
            p_strip = p.strip()
            if not p_strip:
                continue
            is_boilerplate = False
            for pattern in BOILERPLATE_PATTERNS:
                if re.search(pattern, p_strip) and len(p_strip) < 150:
                    is_boilerplate = True
                    break
            if not is_boilerplate:
                cleaned.append(p_strip)
        return cleaned

    @staticmethod
    def deduplicate_paragraphs(paragraphs: List[str]) -> List[str]:
        """Removes exact and near-exact duplicate paragraphs while maintaining original order."""
        seen = set()
        unique = []
        for p in paragraphs:
            key = p.strip().lower()
            if key not in seen and len(key) > 5:
                seen.add(key)
                unique.append(p)
        return unique

    @classmethod
    def clean(cls, raw_text: str) -> str:
        """Full cleaning pipeline returning normalized text."""
        if not raw_text or not raw_text.strip():
            return ""

        text = cls.normalize_unicode(raw_text)
        text = cls.strip_html(text)

        # Split into paragraphs and remove empty / duplicates / boilerplate
        raw_paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        paragraphs = cls.remove_boilerplate(raw_paragraphs)
        paragraphs = cls.deduplicate_paragraphs(paragraphs)

        # Normalize whitespace inside paragraphs
        normalized_paragraphs = [re.sub(r"\s+", " ", p).strip() for p in paragraphs]
        cleaned_text = "\n\n".join(normalized_paragraphs)
        return cleaned_text

    @staticmethod
    def segment_sentences(text: str) -> List[str]:
        """Splits text into coherent sentences handling standard punctuation and common abbreviations."""
        if not text or not text.strip():
            return []

        # Handle common abbreviations to avoid false sentence cuts
        abbr_map = {
            r"\bMr\.": "Mr__DOT__",
            r"\bMrs\.": "Mrs__DOT__",
            r"\bMs\.": "Ms__DOT__",
            r"\bDr\.": "Dr__DOT__",
            r"\bProf\.": "Prof__DOT__",
            r"\bInc\.": "Inc__DOT__",
            r"\bLtd\.": "Ltd__DOT__",
            r"\bCorp\.": "Corp__DOT__",
            r"\be\.g\.": "eg__DOT__",
            r"\bi\.e\.": "ie__DOT__",
            r"\bU\.S\.": "US__DOT__",
            r"\bU\.K\.": "UK__DOT__",
        }
        protected = text
        for pat, repl in abbr_map.items():
            protected = re.sub(pat, repl, protected)

        # Split on sentence boundaries: (. ! ?) followed by whitespace or newline
        raw_sentences = re.split(r"(?<=[.!?])\s+", protected)

        sentences = []
        for s in raw_sentences:
            s_clean = s
            for _, repl in abbr_map.items():
                s_clean = s_clean.replace(repl, repl.replace("__DOT__", "."))
            s_clean = re.sub(r"\s+", " ", s_clean).strip()
            if len(s_clean) > 8:
                sentences.append(s_clean)

        return sentences

    @staticmethod
    def detect_language(text: str) -> str:
        """Basic character-range language detector with Tamil, Hindi, and Latin script detection."""
        if not text:
            return "en"

        # Check for Tamil script (Unicode range U+0B80 - U+0BFF)
        if re.search(r"[\u0B80-\u0BFF]", text):
            return "ta"
        # Check for Devanagari script (Hindi/Marathi: U+0900 - U+097F)
        if re.search(r"[\u0900-\u097F]", text):
            return "hi"
        # Check for Arabic script (U+0600 - U+06FF)
        if re.search(r"[\u0600-\u06FF]", text):
            return "ar"
        # Check for CJK (Chinese/Japanese)
        if re.search(r"[\u4E00-\u9FFF]", text):
            return "zh"
        # Check for Cyrillic (Russian)
        if re.search(r"[\u0400-\u04FF]", text):
            return "ru"

        return "en"
