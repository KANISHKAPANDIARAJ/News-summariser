"""API schemas package export."""

from app.api.schemas.common import ApiResponse, ErrorDetail
from app.api.schemas.article import ArticleExtractRequest, ArticleResponse
from app.api.schemas.summary import SummarizeRequest, SummaryResponse
from app.api.schemas.analysis import (
    AnalyzeRequest,
    TranslateRequest,
    TTSRequest,
    CompareRequest,
    MultiSourceRequest,
)

__all__ = [
    "ApiResponse",
    "ErrorDetail",
    "ArticleExtractRequest",
    "ArticleResponse",
    "SummarizeRequest",
    "SummaryResponse",
    "AnalyzeRequest",
    "TranslateRequest",
    "TTSRequest",
    "CompareRequest",
    "MultiSourceRequest",
]
