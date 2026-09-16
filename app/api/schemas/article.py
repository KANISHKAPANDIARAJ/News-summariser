"""Pydantic schemas for Article requests and responses."""

from typing import Optional

from pydantic import BaseModel, Field

class ArticleExtractRequest(BaseModel):
    url: str = Field(..., description="Target web article URL to scrape")

class ArticleResponse(BaseModel):
    id: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    image_url: Optional[str] = None
    raw_text: str
    cleaned_text: str
    language: str
    word_count: int
