import uuid

from fastapi import APIRouter

from app.schemas.graph import GraphRequest, GraphResponse
from app.utils.validator import validate_github_url
from app.services.github_service import check_repository_access
from app.services.clone_service import clone_repository
from app.services.file_discovery_service import discover_source_files
from app.services.code_analysis_service import analyze_files
from app.services.graph_service import generate_graphs


router = APIRouter()


@router.post(
    "/graphs",
    response_model=GraphResponse,
)
def get_graphs(request: GraphRequest):
    """
    Endpoint that takes a GitHub repo URL and returns
    the Function Call Graph and Dependency Graph.

    Flow:
        repo_url
            → validate
            → clone
            → discover source files
            → analyze all files (Feature 3)
            → generate graphs (Feature 4 Parts 1-7)
            → return graph response
    """

    # 1. Validate URL
    validate_github_url(request.repo_url)

    # 2. Check repository accessibility
    check_repository_access(request.repo_url)

    # 3. Clone repository
    project_id = str(uuid.uuid4())
    clone_result = clone_repository(request.repo_url, project_id)
    clone_path = clone_result["clone_path"]

    # 4. Discover source files
    source_files = discover_source_files(clone_path)

    # 5. Analyze all files (Feature 3)
    analysis_results = analyze_files(source_files)

    # 6. Generate graphs (Feature 4 Parts 1-7)
    graph_response = generate_graphs(analysis_results)

    return graph_response
