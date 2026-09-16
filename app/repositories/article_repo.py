"""Repository for Article persistence."""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.article import Article


class ArticleRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, article_id: str) -> Optional[Article]:
        return self.session.query(Article).filter(Article.id == article_id).first()

    def get_by_content_hash(self, content_hash: str) -> Optional[Article]:
        return (
            self.session.query(Article)
            .filter(Article.content_hash == content_hash)
            .first()
        )

    def get_by_url(self, url: str) -> Optional[Article]:
        return self.session.query(Article).filter(Article.url == url).first()

    def create(self, article: Article) -> Article:
        self.session.add(article)
        self.session.flush()
        return article

    def list_recent(self, limit: int = 20) -> List[Article]:
        return (
            self.session.query(Article)
            .order_by(Article.created_at.desc())
            .limit(limit)
            .all()
        )
