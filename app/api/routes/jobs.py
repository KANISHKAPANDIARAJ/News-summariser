"""Processing Job status REST API route."""

from flask import Blueprint, jsonify
from app.api.schemas.common import ApiResponse
from app.db import get_db_session
from app.repositories.job_repo import JobRepository
from app.constants import ErrorCodes

jobs_bp = Blueprint("jobs_api", __name__)

@jobs_bp.route("/api/jobs/<job_id>", methods=["GET"])
def get_job_status(job_id: str):
    """Checks progress and result of an asynchronous processing job."""
    with get_db_session() as session:
        repo = JobRepository(session)
        job = repo.get_by_id(job_id)
        if not job:
            return jsonify(ApiResponse.fail(
                code=ErrorCodes.JOB_NOT_FOUND,
                message=f"Job with ID '{job_id}' not found."
            ).model_dump()), 404

        return jsonify(ApiResponse.ok(job.to_dict()).model_dump()), 200
