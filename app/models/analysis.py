"""Analysis Result Database Model."""

import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class AnalysisResult(Base, TimestampMixin):
    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    article_id: Mapped[str] = mapped_column(String(36), ForeignKey("articles.id", ondelete="CASCADE"), unique=True, index=True)
    
    sentiment_label: Mapped[str] = mapped_column(String(32))
    sentiment_score: Mapped[float] = mapped_column(Float)
    sentiment_distribution: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    key_points: Mapped[List[Any]] = mapped_column(JSON, default=list)
    keywords: Mapped[List[str]] = mapped_column(JSON, default=list)
    entities: Mapped[List[Any]] = mapped_column(JSON, default=list)

    # Relationships
    article: Mapped["Article"] = relationship("Article", back_populates="analysis")

    def to_dict(self):
        return {
            "id": self.id,
            "article_id": self.article_id,
            "sentiment": {
                "label": self.sentiment_label,
                "score": self.sentiment_score,
                "distribution": self.sentiment_distribution,
            },
            "key_points": self.key_points,
            "keywords": self.keywords,
            "entities": self.entities,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
