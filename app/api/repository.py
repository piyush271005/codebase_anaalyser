from fastapi import APIRouter

from app.schemas.repository import RepositoryRequest
from app.services.project_service import analyze_repository
router = APIRouter()


@router.post("/analyze")
def analyze(request: RepositoryRequest):
     return analyze_repository(request.repo_url)