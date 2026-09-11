import uuid

from fastapi import APIRouter

from app.schemas.understanding import UnderstandingRequest, UnderstandingResponse
from app.utils.validator import validate_github_url
from app.services.github_service import check_repository_access
from app.services.clone_service import clone_repository
from app.services.project_info_service import detect_project_info
from app.services.file_discovery_service import discover_source_files
from app.services.code_analysis_service import analyze_files
from app.services.graph_service import generate_graphs
from app.services.understanding_service import generate_understanding


router = APIRouter()


@router.post(
    "/understand",
    response_model=UnderstandingResponse,
)
def understand_repository(request: UnderstandingRequest):
    """
    Endpoint that takes a GitHub repo URL and returns
    the complete AI-Powered Repository Understanding (Feature 5).

    Flow:
        repo_url
            → validate URL
            → check access
            → clone repository
            → detect project info (Feature 2)
            → discover source files (Feature 2)
            → analyze all files (Feature 3)
            → generate graphs (Feature 4)
            → generate hierarchical understanding (Feature 5)
            → return full understanding response
    """

    # 1. Validate URL
    validate_github_url(request.repo_url)

    # 2. Check repository accessibility
    check_repository_access(request.repo_url)

    # 3. Clone repository
    project_id = str(uuid.uuid4())
    clone_result = clone_repository(request.repo_url, project_id)
    clone_path = clone_result["clone_path"]
    repository_name = clone_result.get("repository_name", "repository")

    # 4. Project metadata & source file discovery (Feature 2)
    project_info = detect_project_info(clone_path)
    source_files = discover_source_files(clone_path)

    # 5. Code structure analysis (Feature 3)
    analysis_results = analyze_files(source_files)

    # 6. Relationship & graph analysis (Feature 4)
    graph_response = generate_graphs(analysis_results)

    # 7. AI-powered hierarchical understanding (Feature 5)
    understanding = generate_understanding(
        repository_name=repository_name,
        clone_path=str(clone_path),
        project_info=project_info,
        analysis_results=analysis_results,
        graph_response=graph_response,
        provider=request.provider,
        model=request.model,
        api_key=request.api_key
    )

    return understanding
