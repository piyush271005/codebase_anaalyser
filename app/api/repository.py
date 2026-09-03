from fastapi import APIRouter

from app.schemas.repository import (
    RepositoryRequest,
    RepositoryAnalysisResponse,
)

from app.services.project_service import analyze_repository

router = APIRouter()




@router.post(
    "/analyze",
    response_model=RepositoryAnalysisResponse,
)
def analyze(request: RepositoryRequest):

    return analyze_repository(request.repo_url)