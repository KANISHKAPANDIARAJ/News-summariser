"""Configuration settings for News Intelligence Platform."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root if present
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class Config:
    """Base Configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key-1234567890abcdef")
    DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL", f"sqlite:///{ROOT_DIR / 'news_intelligence.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # Cache / Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

    # Models & ML
    MODEL_DEVICE = os.getenv("MODEL_DEVICE", "auto")
    SUMMARIZATION_MODEL = os.getenv(
        "SUMMARIZATION_MODEL", "sshleifer/distilbart-cnn-12-6"
    )
    SENTIMENT_MODEL = os.getenv(
        "SENTIMENT_MODEL", "distilbert-base-uncased-finetuned-sst-2-english"
    )
    DEFAULT_TRANSLATION_MODEL_TAMIL = os.getenv(
        "DEFAULT_TRANSLATION_MODEL_TAMIL", "suriya7/English-to-Tamil"
    )

    # Chunking & Processing
    MAX_CHUNK_TOKENS = int(os.getenv("MAX_CHUNK_TOKENS", "800"))
    CHUNK_OVERLAP_TOKENS = int(os.getenv("CHUNK_OVERLAP_TOKENS", "100"))
    MAX_ARTICLE_LENGTH_CHARS = int(os.getenv("MAX_ARTICLE_LENGTH_CHARS", "100000"))
    MIN_ARTICLE_LENGTH_CHARS = int(os.getenv("MIN_ARTICLE_LENGTH_CHARS", "30"))

    # Audio
    AUDIO_CACHE_DIR = ROOT_DIR / os.getenv("AUDIO_CACHE_DIR", "audio_cache")

    # Network & Security
    REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_ARTICLE_SIZE_BYTES", "1048576"))  # 1MB
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # Feature Flags
    ENABLE_MULTI_SOURCE = os.getenv("ENABLE_MULTI_SOURCE", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    ENABLE_COMPARISON = os.getenv("ENABLE_COMPARISON", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    ENABLE_TTS = os.getenv("ENABLE_TTS", "true").lower() in ("true", "1", "yes")
    ENABLE_TRANSLATION = os.getenv("ENABLE_TRANSLATION", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    ENABLE_BACKGROUND_JOBS = os.getenv("ENABLE_BACKGROUND_JOBS", "true").lower() in (
        "true",
        "1",
        "yes",
    )

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    # Enforce secure secret key in production
    if Config.SECRET_KEY == "dev-insecure-key-1234567890abcdef":
        # Generate or warn in production
        pass


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    DATABASE_URL = "sqlite:///:memory:"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CACHE_TTL_SECONDS = 10
    REQUEST_TIMEOUT_SECONDS = 5


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    return config_by_name.get(env, DevelopmentConfig)
