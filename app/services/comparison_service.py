"""Semantic article comparison service computing cosine similarity and topic overlap."""

import numpy as np
from typing import Dict, Any, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.text_cleaner import TextCleaner

class ArticleComparisonService:
    """Compares two articles semantically, highlighting common and unique information."""

    def compare(self, text_a: str, text_b: str) -> Dict[str, Any]:
        if not text_a or not text_b:
            raise ValueError("Both articles must have valid text content.")

        clean_a = TextCleaner.clean(text_a)
        clean_b = TextCleaner.clean(text_b)

        sentences_a = TextCleaner.segment_sentences(clean_a)
        sentences_b = TextCleaner.segment_sentences(clean_b)

        if not sentences_a or not sentences_b:
            return {
                "similarity_score": 0.0,
                "common_topics": [],
                "unique_to_first": sentences_a,
                "unique_to_second": sentences_b,
                "disclaimer": "Semantic comparison identifies textual overlap; it does not evaluate factual veracity."
            }

        # Vectorize both articles together
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=1500)
        tfidf_docs = vectorizer.fit_transform([clean_a, clean_b])

        # Overall document similarity
        overall_sim = float(cosine_similarity(tfidf_docs[0:1], tfidf_docs[1:2])[0][0])

        # Sentence-level cross similarity
        vec_a = vectorizer.transform(sentences_a)
        vec_b = vectorizer.transform(sentences_b)
        cross_sims = cosine_similarity(vec_a, vec_b)  # shape (len(a), len(b))

        common_points = []
        unique_a = []
        unique_b = []

        # Thresholds
        match_thresh = 0.45

        matched_b_indices = set()
        for idx_a, sent_a in enumerate(sentences_a):
            max_sim_idx = int(np.argmax(cross_sims[idx_a]))
            max_sim_val = float(cross_sims[idx_a, max_sim_idx])

            if max_sim_val >= match_thresh:
                common_points.append({
                    "topic_theme": sent_a[:120] + ("..." if len(sent_a) > 120 else ""),
                    "similarity": round(max_sim_val, 3)
                })
                matched_b_indices.add(max_sim_idx)
            else:
                if len(sent_a.split()) > 5:
                    unique_a.append(sent_a)

        for idx_b, sent_b in enumerate(sentences_b):
            if idx_b not in matched_b_indices and len(sent_b.split()) > 5:
                unique_b.append(sent_b)

        # Extract top common keywords
        terms = vectorizer.get_feature_names_out()
        shared_weights = np.asarray(tfidf_docs[0].multiply(tfidf_docs[1]).todense()).flatten()
        top_term_indices = shared_weights.argsort()[::-1]
        common_keywords = [terms[i] for i in top_term_indices[:6] if shared_weights[i] > 0]

        return {
            "similarity_score": round(overall_sim, 3),
            "common_keywords": common_keywords,
            "common_points": common_points[:5],
            "unique_to_first": unique_a[:5],
            "unique_to_second": unique_b[:5],
            "disclaimer": "Semantic comparison identifies textual overlap; it does not evaluate factual veracity."
        }
