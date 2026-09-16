"""Aggregated multi-segment document sentiment analyzer."""

from typing import Dict, Any
from app.ml.model_manager import get_model_manager
from app.services.text_cleaner import TextCleaner
from app.utils.logger import logger


class SentimentAnalyzer:
    """Computes sentiment distribution across the full document by aggregating segment scores."""

    DISCLAIMER = "Sentiment analysis measures linguistic tone/polarity, not factual accuracy or journalistic bias."

    def __init__(self):
        self.model_manager = get_model_manager()

    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyzes full article sentiment across chunks and returns aggregated distribution."""
        if not text or len(text.strip()) < 10:
            return {
                "label": "neutral",
                "score": 1.0,
                "distribution": {"positive": 0.33, "neutral": 0.34, "negative": 0.33},
                "disclaimer": self.DISCLAIMER,
            }

        sentences = TextCleaner.segment_sentences(text)
        # Sample up to 10 representative sentences across the article (beginning, middle, end)
        if len(sentences) > 10:
            step = len(sentences) / 10.0
            sample_sentences = [sentences[int(i * step)] for i in range(10)]
        else:
            sample_sentences = sentences

        pipeline = self.model_manager.get_sentiment_pipeline()

        total_pos = 0.0
        total_neg = 0.0
        total_neu = 0.0
        count = 0

        for s in sample_sentences:
            truncated = s[:400].strip()
            if not truncated:
                continue
            try:
                raw_res = pipeline(truncated)
                # raw_res is a list of score dicts [{'label': 'POSITIVE', 'score': 0.9}, {'label': 'NEGATIVE', 'score': 0.1}]
                scores = {}
                if isinstance(raw_res, list):
                    items = raw_res[0] if isinstance(raw_res[0], list) else raw_res
                    for item in items:
                        scores[item["label"].upper()] = item["score"]

                pos = scores.get("POSITIVE", 0.0)
                neg = scores.get("NEGATIVE", 0.0)
                # If model is binary (POSITIVE/NEGATIVE), estimate neutral margin
                # When positive and negative are close (diff < 0.25), text is largely neutral
                diff = abs(pos - neg)
                if diff < 0.35:
                    neu = 0.60
                    pos = pos * 0.20
                    neg = neg * 0.20
                else:
                    neu = 0.10
                    pos = pos * 0.90
                    neg = neg * 0.90

                total_pos += pos
                total_neg += neg
                total_neu += neu
                count += 1
            except Exception as e:
                logger.warning(f"Sentiment segment scoring error: {e}")

        if count == 0:
            return {
                "label": "neutral",
                "score": 1.0,
                "distribution": {"positive": 0.33, "neutral": 0.34, "negative": 0.33},
                "disclaimer": self.DISCLAIMER,
            }

        avg_pos = total_pos / count
        avg_neg = total_neg / count
        avg_neu = total_neu / count

        # Normalize to sum to 1.0
        total = avg_pos + avg_neg + avg_neu
        norm_pos = round(avg_pos / total, 3)
        norm_neg = round(avg_neg / total, 3)
        norm_neu = round(1.0 - (norm_pos + norm_neg), 3)

        # Primary label
        if norm_pos > norm_neg and norm_pos > norm_neu:
            primary_label = "positive"
            confidence = norm_pos
        elif norm_neg > norm_pos and norm_neg > norm_neu:
            primary_label = "negative"
            confidence = norm_neg
        else:
            primary_label = "neutral"
            confidence = norm_neu

        return {
            "label": primary_label,
            "score": confidence,
            "distribution": {
                "positive": norm_pos,
                "neutral": norm_neu,
                "negative": norm_neg,
            },
            "disclaimer": self.DISCLAIMER,
        }
