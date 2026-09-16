"""Extractive Semantic Q&A service answering questions using article evidence."""

from typing import Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.text_cleaner import TextCleaner
from app.utils.logger import logger


class ArticleQAService:
    @classmethod
    def answer_question(
        cls, article_text: str, question: str, top_k: int = 3
    ) -> Dict[str, Any]:
        """Answers factual questions using semantic sentence retrieval over the article."""
        if not article_text or not article_text.strip():
            return {
                "answer": "No article content provided to answer question.",
                "evidence_sentences": [],
                "confidence": 0.0,
            }

        if not question or not question.strip():
            return {
                "answer": "Please ask a question about the article.",
                "evidence_sentences": [],
                "confidence": 0.0,
            }

        sentences = TextCleaner.segment_sentences(article_text)
        if not sentences:
            return {
                "answer": "Unable to segment article sentences.",
                "evidence_sentences": [],
                "confidence": 0.0,
            }

        try:
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 2), max_features=2500, sublinear_tf=True
            )
            tfidf_matrix = vectorizer.fit_transform(sentences)
            q_vec = vectorizer.transform([question.strip()])

            sims = cosine_similarity(q_vec, tfidf_matrix).flatten()
            top_indices = sims.argsort()[::-1]

            relevant_sentences = []
            for idx in top_indices[:top_k]:
                score = float(sims[idx])
                if score > 0.05:
                    relevant_sentences.append(
                        {"sentence": sentences[idx], "relevance_score": round(score, 3)}
                    )

            if not relevant_sentences:
                return {
                    "answer": "The article does not contain sufficient direct information to answer this specific question.",
                    "evidence_sentences": [],
                    "confidence": 0.20,
                }

            # Synthesize direct extractive answer from top matching evidence
            answer_text = " ".join(
                [item["sentence"] for item in relevant_sentences[:2]]
            )
            top_score = relevant_sentences[0]["relevance_score"]

            return {
                "question": question,
                "answer": answer_text,
                "evidence_sentences": relevant_sentences,
                "confidence": min(0.95, round(top_score * 1.5, 2)),
            }

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "answer": f"Error answering question: {str(e)}",
                "evidence_sentences": [],
                "confidence": 0.0,
            }
