"""Multi-source news aggregator and synthesis engine."""

from typing import List, Dict, Any
from app.services.text_cleaner import TextCleaner
from app.services.summarizer import HierarchicalSummarizer
from app.services.keypoint_extractor import KeypointExtractor
from app.services.comparison_service import ArticleComparisonService


class MultiSourceAggregator:
    def __init__(self):
        self.summarizer = HierarchicalSummarizer()
        self.keypoint_extractor = KeypointExtractor(diversity_lambda=0.7)
        self.comparator = ArticleComparisonService()

    def analyze_sources(self, articles: List[Dict[str, str]]) -> Dict[str, Any]:
        """Performs multi-source synthesis across 2+ articles on a common topic."""
        if not articles or len(articles) < 2:
            raise ValueError("Multi-source analysis requires at least two articles.")

        cleaned_articles = []
        for a in articles:
            text = a.get("text", "")
            title = a.get("title", "Untitled Source")
            clean_text = TextCleaner.clean(text)
            if len(clean_text) > 50:
                cleaned_articles.append(
                    {"title": title, "url": a.get("url", ""), "text": clean_text}
                )

        if len(cleaned_articles) < 2:
            raise ValueError("At least two articles must contain substantive text.")

        # 1. Summarize individual sources
        individual_summaries = []
        combined_corpus = []

        for item in cleaned_articles:
            res = self.summarizer.summarize(item["text"], length_profile="short")
            individual_summaries.append(
                {
                    "source": item["title"],
                    "url": item["url"],
                    "summary": res["summary"],
                    "word_count": res["word_count"],
                }
            )
            combined_corpus.append(f"Source [{item['title']}]: {res['summary']}")

        # 2. Combined synthesis
        synthesis_input = "\n\n".join(combined_corpus)
        combined_summary_res = self.summarizer.summarize(
            synthesis_input, length_profile="medium"
        )

        # 3. Common points via MMR keypoints on synthesized corpus
        common_points = self.keypoint_extractor.extract_key_points(
            synthesis_input, top_n=4
        )

        # 4. Cross-source pairwise similarity
        pairwise_comparison = self.comparator.compare(
            cleaned_articles[0]["text"], cleaned_articles[1]["text"]
        )

        return {
            "overall_summary": combined_summary_res["summary"],
            "source_coverage": {
                "source_count": len(cleaned_articles),
                "sources": [s["title"] for s in cleaned_articles],
            },
            "individual_summaries": individual_summaries,
            "consensus_points": [p["text"] for p in common_points],
            "pairwise_similarity": pairwise_comparison["similarity_score"],
            "common_keywords": pairwise_comparison.get("common_keywords", []),
            "disclaimer": "Multi-source briefing aggregates reported claims; model interpretations are not verified facts.",
        }
