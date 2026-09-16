"""Article Comparison Database Model."""

import uuid
from typing import List
from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class ArticleComparison(Base, TimestampMixin):
    __tablename__ = "article_comparisons"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    article_1_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    article_2_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    similarity_score: Mapped[float] = mapped_column(Float)
    common_topics: Mapped[List[str]] = mapped_column(JSON, default=list)
    unique_to_first: Mapped[List[str]] = mapped_column(JSON, default=list)
    unique_to_second: Mapped[List[str]] = mapped_column(JSON, default=list)

    def to_dict(self):
        return {
            "id": self.id,
            "article_1_id": self.article_1_id,
            "article_2_id": self.article_2_id,
            "similarity_score": self.similarity_score,
            "common_topics": self.common_topics,
            "unique_to_first": self.unique_to_first,
            "unique_to_second": self.unique_to_second,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
