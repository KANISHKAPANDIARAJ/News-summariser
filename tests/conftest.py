import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from app import create_app
from app.config import TestingConfig
from app.db import init_db, engine
from app.models.base import Base

SAMPLE_ARTICLE = """
Artificial intelligence research laboratories around the world have accelerated the deployment of production-grade news analysis systems. The latest models combine neural extractive keypoint discovery with abstractive hierarchical summarization to handle documents of arbitrary length.

Dr. Elena Vance, lead researcher at the Global Tech Institute in Geneva, announced the breakthrough during the European Technology Summit on October 12, 2026. The new architecture achieves an 85% compression ratio while eliminating the context truncation penalties that plagued earlier systems.

Investors have poured $15 billion into scalable natural language processing infrastructure this fiscal year. Financial analysts note that the return on investment will be driven by real-time automated media synthesis. However, regulatory bodies emphasize that ethical safeguards and bias detection mechanisms remain mandatory prerequisites for commercial rollouts.
"""

@pytest.fixture(scope="session")
def app():
    """Application fixture with in-memory SQLite database."""
    app = create_app(config_class=TestingConfig)
    with app.app_context():
        init_db()
        yield app
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()

@pytest.fixture
def sample_article():
    return SAMPLE_ARTICLE
