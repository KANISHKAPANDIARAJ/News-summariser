"""Pydantic schemas for Article requests and responses."""

from __future__ import annotations

from pydantic import BaseModel, Field

class ArticleExtractRequest(BaseModel):
    url: str = Field(..., description="Target web article URL to scrape")

class ArticleResponse(BaseModel):
    id: str | None = None
    url: str | None = None
    title: str | None = None
    author: str | None = None
    publisher: str | None = None
    published_date: str | None = None
    image_url: str | None = None
    raw_text: str
    cleaned_text: str
    language: str
    word_count: int
