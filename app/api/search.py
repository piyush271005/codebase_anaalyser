from fastapi import APIRouter

from app.schemas.search import (
    IndexRequest,
    IndexResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.indexing_service import index_repository
from app.services.search_service import search_codebase

router = APIRouter()


@router.post(
    "/index",
    response_model=IndexResponse,
    summary="Index a GitHub repository into ChromaDB",
    description="Clones the repo, performs AST analysis, extracts structure-aware code chunks, generates vector embeddings, and stores them in ChromaDB."
)
def index_repo(request: IndexRequest):
    """
    Endpoint to trigger codebase indexing for Feature 6.
    """
    result = index_repository(
        repo_url=request.repo_url,
        project_id=request.project_id,
        include_summaries=request.include_summaries,
        provider=request.provider,
        model=request.model,
        api_key=request.api_key
    )
    return result


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic code search across an indexed repository",
    description="Embeds natural language query using Gemini and performs vector similarity search in ChromaDB, isolated by project_id."
)
def search_repo(request: SearchRequest):
    """
    Endpoint for semantic code search.
    """
    result = search_codebase(
        query=request.query,
        project_id=request.project_id,
        top_k=request.top_k
    )
    return result
