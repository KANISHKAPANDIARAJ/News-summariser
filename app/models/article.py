"""Article Database Model."""

import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Article(Base, TimestampMixin):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    published_date: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    summaries: Mapped[List["Summary"]] = relationship("Summary", back_populates="article", cascade="all, delete-orphan")
    analysis: Mapped[Optional["AnalysisResult"]] = relationship("AnalysisResult", back_populates="article", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "content_hash": self.content_hash,
            "title": self.title,
            "author": self.author,
            "publisher": self.publisher,
            "published_date": self.published_date,
            "image_url": self.image_url,
            "language": self.language,
            "word_count": self.word_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
