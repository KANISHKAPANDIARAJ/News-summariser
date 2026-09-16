"""API schemas package export."""

from __future__ import annotations

from app.api.schemas.analysis import (
    AnalyzeRequest,
    CompareRequest,
    MultiSourceRequest,
    TTSRequest,
    TranslateRequest,
)
from app.api.schemas.article import ArticleExtractRequest, ArticleResponse
from app.api.schemas.common import ApiResponse, ErrorDetail
from app.api.schemas.summary import SummarizeRequest, SummaryResponse

__all__ = [
    "AnalyzeRequest",
    "ApiResponse",
    "ArticleExtractRequest",
    "ArticleResponse",
    "CompareRequest",
    "ErrorDetail",
    "MultiSourceRequest",
    "SummarizeRequest",
    "SummaryResponse",
    "TTSRequest",
    "TranslateRequest",
]
