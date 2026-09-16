"""Keyword extraction using TF-IDF n-gram scoring and saliency ranking."""

from typing import List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from app.utils.logger import logger


class KeywordExtractor:
    def __init__(self, max_keywords: int = 8):
        self.max_keywords = max_keywords

    def extract_keywords(self, text: str, top_n: Optional[int] = None) -> List[str]:
        """Extracts top salient n-gram keywords from text."""
        limit = top_n if top_n is not None else self.max_keywords
        if not text or len(text.strip()) < 30:
            return []

        try:
            # Extract unigrams and bigrams
            # Use Unicode word character pattern to support Indic, Arabic, CJK and other scripts
            vectorizer = TfidfVectorizer(
                stop_words=None,
                ngram_range=(1, 2),
                max_features=1000,
                token_pattern=r"(?u)\b[^\W\d_]{2,}\b",
            )
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]

            # Sort keywords by TF-IDF weight descending
            sorted_indices = scores.argsort()[::-1]

            keywords: List[str] = []
            seen_words = set()

            for idx in sorted_indices:
                if len(keywords) >= limit:
                    break
                word = feature_names[idx]
                # Filter out pure numbers or substrings of already selected phrases
                parts = set(word.lower().split())
                if not parts.intersection(seen_words):
                    keywords.append(word)
                    seen_words.update(parts)

            return keywords
        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")
            return []


Optional_int = int
