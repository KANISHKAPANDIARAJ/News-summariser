"""Pydantic schemas for Summarization requests and responses."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SummarizeRequest(BaseModel):
    url: Optional[str] = Field(None, description="Web article URL")
    text: Optional[str] = Field(None, description="Raw text content to summarize")
    length_profile: str = Field("medium", description="Length profile: short, medium, detailed")
    language: str = Field("en", description="Target translation language code (e.g. en, ta, hi, fr)")
    async_mode: bool = Field(False, description="Whether to queue as background job")

class SummaryResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    summary_id: str
    article_id: str
    summary: str
    length_profile: str
    compression_ratio: float
    processing_time_ms: float
    model_name: str
    language: str
    original_title: Optional[str] = None
    original_url: Optional[str] = None
