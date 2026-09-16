"""Pydantic schemas for Analysis, Translation, and TTS."""

from __future__ import annotations

from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    text: str | None = None
    url: str | None = None
    num_key_points: int = 5

class TranslateRequest(BaseModel):
    text: str
    target_language: str
    source_language: str = "en"

class TTSRequest(BaseModel):
    text: str
    language: str = "en"

class CompareRequest(BaseModel):
    text_a: str
    text_b: str

class MultiSourceRequest(BaseModel):
    articles: list[dict[str, str]] = Field(
        ...,
        min_length=2,
        description="List of articles with 'text' and optional 'title'"
    )
