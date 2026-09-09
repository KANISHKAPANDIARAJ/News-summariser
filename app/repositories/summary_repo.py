"""Repository for Summary and Analysis persistence."""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.summary import Summary
from app.models.analysis import AnalysisResult
from app.models.translation import Translation

class SummaryRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, summary_id: str) -> Optional[Summary]:
        return self.session.query(Summary).filter(Summary.id == summary_id).first()

    def get_by_article_and_profile(self, article_id: str, length_profile: str) -> Optional[Summary]:
        return (
            self.session.query(Summary)
            .filter(Summary.article_id == article_id, Summary.length_profile == length_profile)
            .first()
        )

    def create_summary(self, summary: Summary) -> Summary:
        self.session.add(summary)
        self.session.flush()
        return summary

    def get_analysis_by_article_id(self, article_id: str) -> Optional[AnalysisResult]:
        return self.session.query(AnalysisResult).filter(AnalysisResult.article_id == article_id).first()

    def create_analysis(self, analysis: AnalysisResult) -> AnalysisResult:
        self.session.add(analysis)
        self.session.flush()
        return analysis

    def get_translation(self, summary_id: str, target_language: str) -> Optional[Translation]:
        return (
            self.session.query(Translation)
            .filter(Translation.summary_id == summary_id, Translation.target_language == target_language)
            .first()
        )

    def create_translation(self, translation: Translation) -> Translation:
        self.session.add(translation)
        self.session.flush()
        return translation

    def list_recent_summaries(self, limit: int = 10) -> List[Summary]:
        return self.session.query(Summary).order_by(Summary.created_at.desc()).limit(limit).all()

    def delete_summary(self, summary_id: str) -> bool:
        summary = self.get_by_id(summary_id)
        if summary:
            self.session.delete(summary)
            self.session.flush()
            return True
        return False
