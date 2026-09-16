"""Translation Database Model."""

import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.summary import Summary

class Translation(Base, TimestampMixin):
    __tablename__ = "translations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    summary_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("summaries.id", ondelete="CASCADE"), index=True
    )
    source_language: Mapped[str] = mapped_column(String(10), default="en")
    target_language: Mapped[str] = mapped_column(String(10), index=True)
    translated_text: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Relationships
    summary: Mapped["Summary"] = relationship("Summary", back_populates="translations")

    def to_dict(self):
        return {
            "id": self.id,
            "summary_id": self.summary_id,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "translated_text": self.translated_text,
            "model_name": self.model_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
