from pydantic import BaseModel, Field


class CodeChunk(BaseModel):
    """
    Represents an extracted and enriched code chunk ready for indexing.
    """
    chunk_id: str
    content: str = Field(description="Enriched searchable text (Summary + Code)")
    code: str = Field(description="Raw source code extracted from disk")
    file_path: str
    language: str
    chunk_type: str = Field(description="'function' | 'class' | 'file'")
    name: str = Field(description="Name of the function, class, or file component")
    line: int | None = None
    end_line: int | None = None
    summary: str | None = None


class IndexRequest(BaseModel):
    """
    Request model to index a repository into ChromaDB.
    """
    repo_url: str
    project_id: str | None = None
    include_summaries: bool = True
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None


class IndexResponse(BaseModel):
    """
    Response model returning indexing results.
    """
    project_id: str
    repository_name: str
    total_chunks: int
    status: str = "indexed"
    message: str


class SearchRequest(BaseModel):
    """
    Request model for semantic code search.
    """
    query: str = Field(description="Natural language question or search query")
    project_id: str = Field(description="Target repository/project ID to search within")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of relevant chunks to retrieve")


class SearchResult(BaseModel):
    """
    A single retrieved code chunk match.
    """
    chunk_id: str
    file_path: str
    chunk_type: str
    name: str
    code: str
    summary: str | None = None
    line: int | None = None
    end_line: int | None = None
    score: float = Field(description="Similarity score (higher means more relevant)")


class SearchResponse(BaseModel):
    """
    Response model containing semantic search results.
    """
    query: str
    project_id: str
    total_results: int
    results: list[SearchResult]
