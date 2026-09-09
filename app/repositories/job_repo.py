"""Repository for ProcessingJob persistence."""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.job import ProcessingJob

class JobRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_job(self, job_id: Optional[str] = None) -> ProcessingJob:
        job = ProcessingJob(status="queued", progress=0, stage="initialized")
        if job_id:
            job.id = job_id
        self.session.add(job)
        self.session.flush()
        return job

    def get_by_id(self, job_id: str) -> Optional[ProcessingJob]:
        return self.session.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()

    def update_progress(self, job_id: str, progress: int, stage: str, status: str = "processing"):
        job = self.get_by_id(job_id)
        if job:
            job.progress = progress
            job.stage = stage
            job.status = status
            self.session.flush()

    def mark_completed(self, job_id: str, result_data: Dict[str, Any]):
        job = self.get_by_id(job_id)
        if job:
            job.progress = 100
            job.stage = "completed"
            job.status = "completed"
            job.result_data = result_data
            job.completed_at = datetime.now(timezone.utc)
            self.session.flush()

    def mark_failed(self, job_id: str, error_message: str):
        job = self.get_by_id(job_id)
        if job:
            job.status = "failed"
            job.stage = "failed"
            job.error_message = error_message
            job.completed_at = datetime.now(timezone.utc)
            self.session.flush()
