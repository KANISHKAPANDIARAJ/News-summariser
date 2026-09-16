"""Named Entity Recognition service extracting PERSON, ORG, LOC, DATE, MONEY, PERCENT."""

import re
from typing import List, Dict


class EntityExtractor:
    """Extracts structured entities across standard categories."""

    # Regex patterns for deterministic entity types
    PATTERNS = {
        "MONEY": r"(?:\$|€|£|₹|USD|EUR|GBP|INR)\s?\d+(?:,\d{3})*(?:\.\d+)?(?:\s?(?:million|billion|trillion|crore|lakh))?",
        "PERCENT": r"\b\d+(?:\.\d+)?%\b|\b\d+(?:\.\d+)?\s*(?:percent|percentage)\b",
        "DATE": r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s+\d{4})?|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}|\b(?:19|20)\d{2}\b",
    }

    # Well-known organizations for high-precision matching
    KNOWN_ORGS = {
        "Google",
        "Microsoft",
        "OpenAI",
        "Apple",
        "Amazon",
        "Meta",
        "Twitter",
        "Nvidia",
        "Tesla",
        "SpaceX",
        "Anthropic",
        "IBM",
        "Intel",
        "United Nations",
        "WHO",
        "European Union",
        "NASA",
        "NATO",
        "BBC",
        "Reuters",
        "CNN",
        "Federal Reserve",
    }

    # Well-known locations
    KNOWN_LOCS = {
        "United States",
        "US",
        "USA",
        "UK",
        "United Kingdom",
        "India",
        "China",
        "Russia",
        "Germany",
        "France",
        "Japan",
        "California",
        "New York",
        "London",
        "Paris",
        "Tokyo",
        "Beijing",
        "Washington",
        "San Francisco",
        "Delhi",
        "Mumbai",
        "Europe",
    }

    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extracts structured entities from text without exposing raw model tokens."""
        if not text or len(text.strip()) < 10:
            return []

        entities: List[Dict[str, str]] = []
        seen_entities = set()

        def add_entity(ent_text: str, label: str):
            clean_text = ent_text.strip(" ,.;:\"'()")
            key = (clean_text.lower(), label)
            if key not in seen_entities and len(clean_text) > 1:
                seen_entities.add(key)
                entities.append({"text": clean_text, "label": label})

        # 1. Regex extractions for MONEY, PERCENT, DATE
        for label, pattern in self.PATTERNS.items():
            matches = re.finditer(
                pattern, text, re.IGNORECASE if label != "DATE" else 0
            )
            for m in matches:
                add_entity(m.group(), label)

        # 2. Known organizations and locations
        for org in self.KNOWN_ORGS:
            if re.search(rf"\b{re.escape(org)}\b", text):
                add_entity(org, "ORGANIZATION")

        for loc in self.KNOWN_LOCS:
            if re.search(rf"\b{re.escape(loc)}\b", text):
                add_entity(loc, "LOCATION")

        # 3. Capitalized Proper Noun Entity Heuristic (Title Case phrases)
        # Finds 2-3 word capitalized proper nouns likely representing Persons or Orgs
        proper_nouns = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b", text)
        for pn in proper_nouns:
            if pn in self.KNOWN_ORGS or pn in self.KNOWN_LOCS:
                continue
            # Filter out common sentence start phrases
            if pn.lower() in (
                "the company",
                "in addition",
                "according to",
                "last year",
                "new york",
            ):
                continue
            # Typical person name check (no company suffix like Inc/Corp)
            if re.search(r"\b(?:Inc|Corp|Ltd|LLC|Group|Association|Board)\b", pn):
                add_entity(pn, "ORGANIZATION")
            else:
                add_entity(pn, "PERSON")

        return entities[:25]
