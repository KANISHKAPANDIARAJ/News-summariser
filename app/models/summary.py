"""Summary Database Model."""

import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.article import Article
    from app.models.translation import Translation

class Summary(Base, TimestampMixin):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    summary_type: Mapped[str] = mapped_column(
        String(32), default="hierarchical_map_reduce"
    )
    length_profile: Mapped[str] = mapped_column(String(32), default="medium")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    compression_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    processing_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_name: Mapped[str] = mapped_column(String(128))

    # Relationships
    article: Mapped["Article"] = relationship("Article", back_populates="summaries")
    translations: Mapped[List["Translation"]] = relationship(
        "Translation", back_populates="summary", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "article_id": self.article_id,
            "summary_type": self.summary_type,
            "length_profile": self.length_profile,
            "text": self.text,
            "compression_ratio": self.compression_ratio,
            "processing_time_ms": self.processing_time_ms,
            "model_name": self.model_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
