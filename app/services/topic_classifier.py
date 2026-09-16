"""Topic classification service categorizing articles into journalistic domains."""

import re
from typing import Dict, Any

TOPIC_KEYWORDS = {
    "Technology": [
        "software",
        "hardware",
        "apple",
        "google",
        "microsoft",
        "cyber",
        "digital",
        "internet",
        "chip",
        "semiconductor",
        "cloud",
    ],
    "AI": [
        "artificial intelligence",
        "machine learning",
        "neural",
        "llm",
        "openai",
        "deep learning",
        "transformer",
        "chatgpt",
        "algorithm",
    ],
    "Business": [
        "market",
        "economy",
        "stock",
        "shares",
        "revenue",
        "investor",
        "banking",
        "fiscal",
        "inflation",
        "gdp",
        "profit",
        "merger",
    ],
    "Politics": [
        "government",
        "parliament",
        "election",
        "president",
        "minister",
        "senate",
        "policy",
        "congress",
        "vote",
        "bill",
        "campaign",
    ],
    "Sports": [
        "football",
        "cricket",
        "tournament",
        "match",
        "championship",
        "player",
        "olympics",
        "league",
        "score",
        "stadium",
    ],
    "Health": [
        "medical",
        "health",
        "hospital",
        "doctor",
        "disease",
        "vaccine",
        "treatment",
        "virus",
        "patient",
        "clinical",
        "pharma",
    ],
    "Science": [
        "physics",
        "astronomy",
        "space",
        "nasa",
        "biology",
        "chemistry",
        "quantum",
        "researchers",
        "study",
        "laboratory",
    ],
    "Environment": [
        "climate",
        "emissions",
        "carbon",
        "renewable",
        "solar",
        "wind",
        "conservation",
        "wildlife",
        "warming",
        "pollution",
    ],
    "Local News": [
        "power cut",
        "shutdown",
        "electricity",
        "maintenance",
        "district",
        "collector",
        "traffic",
        "road",
        "bus",
        "water supply",
        "மின்தடை",
        "மின்சாரம்",
    ],
    "Entertainment": [
        "movie",
        "cinema",
        "actor",
        "actress",
        "film",
        "music",
        "song",
        "box office",
        "director",
        "hollywood",
        "bollywood",
    ],
}


class TopicClassifier:
    @classmethod
    def classify(cls, text: str) -> Dict[str, Any]:
        """Classifies text into primary journalistic category based on lexical frequency and saliency."""
        if not text or len(text.strip()) < 20:
            return {"category": "Other", "confidence": 0.50}

        text_lower = text.lower()
        scores = {}

        for category, keywords in TOPIC_KEYWORDS.items():
            count = 0
            for kw in keywords:
                matches = len(re.findall(rf"\b{re.escape(kw)}\b", text_lower))
                count += matches * (2 if " " in kw else 1)
            if count > 0:
                scores[category] = count

        if not scores:
            return {"category": "General News", "confidence": 0.60}

        total_matches = sum(scores.values())
        best_category = max(scores, key=scores.get)
        confidence = round(
            min(0.98, max(0.65, scores[best_category] / max(1, total_matches) + 0.3)), 2
        )

        return {"category": best_category, "confidence": confidence}
