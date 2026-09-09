"""Unit tests for MMR keypoint extraction, keywords, and NER."""

from app.services.keypoint_extractor import KeypointExtractor
from app.services.keyword_extractor import KeywordExtractor
from app.services.entity_extractor import EntityExtractor
from app.services.comparison_service import ArticleComparisonService

def test_keypoint_extractor_mmr():
    extractor = KeypointExtractor(diversity_lambda=0.65)
    text = (
        "Global economies are recovering from the financial downturn. "
        "Central banks around the world have raised interest rates steadily. "
        "Employment numbers in major cities reached historic highs. "
        "Supply chain disruptions have finally started easing this quarter. "
        "Consumer spending continues to show resilience despite inflation."
    )
    kps = extractor.extract_key_points(text, top_n=3)
    assert len(kps) == 3
    for kp in kps:
        assert "text" in kp
        assert "score" in kp
        assert len(kp["text"]) > 10

def test_keyword_extractor():
    extractor = KeywordExtractor(max_keywords=5)
    text = (
        "Deep learning and transformer models have transformed natural language processing. "
        "Researchers in artificial intelligence are fine-tuning large language models."
    )
    keywords = extractor.extract_keywords(text)
    assert len(keywords) > 0
    assert any("learning" in k or "transformer" in k or "language" in k for k in keywords)

def test_entity_extractor():
    extractor = EntityExtractor()
    text = "On October 12, 2026, Google announced in California that it invested $10 billion."
    entities = extractor.extract_entities(text)
    labels = {e["label"] for e in entities}
    assert "ORGANIZATION" in labels or "LOCATION" in labels or "DATE" in labels

def test_article_comparison():
    service = ArticleComparisonService()
    text_a = "Renewable energy production reached record levels as solar and wind installations grew."
    text_b = "Solar and wind energy installations expanded rapidly, breaking previous power generation records."
    res = service.compare(text_a, text_b)
    assert "similarity_score" in res
    assert res["similarity_score"] > 0.1
    assert "common_keywords" in res
