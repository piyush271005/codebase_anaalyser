from fastapi import HTTPException
import uuid

from app.utils.validator import validate_github_url
from app.services.github_service import check_repository_access
from app.services.clone_service import clone_repository


def analyze_repository(repo_url: str):

    is_valid, error = validate_github_url(repo_url)

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=error
        )
    repo_data = check_repository_access(repo_url)
    project_id = uuid.uuid4().hex[:8]
    clone_path = clone_repository(
        repo_url,
        project_id
    )

    return {
        "success": True,
        "project_id": project_id,
        "clone_path": clone_path,
        "repository": {
            "name": repo_data["name"],
            "owner": repo_data["owner"]["login"],
            "language": repo_data["language"]
        }
    }