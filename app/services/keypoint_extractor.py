"""Extractive Key-Point Extraction using Maximal Marginal Relevance (MMR)."""

import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.text_cleaner import TextCleaner
from app.utils.logger import logger


class KeypointExtractor:
    def __init__(self, diversity_lambda: float = 0.65):
        """
        diversity_lambda: Balance parameter between query/doc relevance (1.0) and diversity (0.0).
        0.65 gives high topical relevance while actively suppressing redundant sentences.
        """
        self.diversity_lambda = diversity_lambda

    def extract_key_points(self, text: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """Extracts top N non-redundant salient sentences using Maximal Marginal Relevance (MMR)."""
        sentences = TextCleaner.segment_sentences(text)
        if not sentences:
            return []

        # Filter out overly short sentences (e.g. headers or table cells)
        candidates = [s for s in sentences if len(s.split()) >= 6]
        if not candidates:
            candidates = sentences

        if len(candidates) <= top_n:
            return [{"text": s, "score": 1.0} for s in candidates]

        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                max_features=2000,
                sublinear_tf=True,
            )
            sentence_vectors = vectorizer.fit_transform(candidates)
            # Document centroid vector representing the entire text theme
            doc_vector = np.asarray(sentence_vectors.mean(axis=0))

            # Relevance to entire document: Sim(sentence, document)
            doc_sims = cosine_similarity(sentence_vectors, doc_vector).flatten()

            # Pairwise similarity between sentences for redundancy penalty
            pairwise_sims = cosine_similarity(sentence_vectors)

            selected_indices: List[int] = []
            candidate_indices = list(range(len(candidates)))

            # Pick the sentence with highest relevance to start
            first_idx = int(np.argmax(doc_sims))
            selected_indices.append(first_idx)
            candidate_indices.remove(first_idx)

            # Iteratively pick remaining candidates using MMR formula
            while len(selected_indices) < top_n and candidate_indices:
                mmr_scores = []
                for cand_idx in candidate_indices:
                    relevance = doc_sims[cand_idx]
                    # Max similarity to any already selected sentence
                    redundancy = max(
                        pairwise_sims[cand_idx][sel_idx] for sel_idx in selected_indices
                    )
                    score = (
                        self.diversity_lambda * relevance
                        - (1.0 - self.diversity_lambda) * redundancy
                    )
                    mmr_scores.append(score)

                best_cand_idx = candidate_indices[int(np.argmax(mmr_scores))]
                selected_indices.append(best_cand_idx)
                candidate_indices.remove(best_cand_idx)

            results = [
                {"text": candidates[idx], "score": round(float(doc_sims[idx]), 4)}
                for idx in selected_indices
            ]
            return results

        except Exception as e:
            logger.error(
                f"MMR key-point extraction error: {e}. Falling back to length-filtered sentences."
            )
            return [{"text": s, "score": 0.5} for s in candidates[:top_n]]
