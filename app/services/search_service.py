from app.services.embedding_service import generate_query_embedding
from app.services.vector_store import get_chroma_client, query_similar_chunks


def search_codebase(
    query: str,
    project_id: str,
    top_k: int = 5
) -> dict:
    """
    Performs semantic code search on an indexed repository.

    Execution Pipeline:
      1. Validate and sanitize query and top_k parameters.
      2. Convert natural language query into a 768-dim vector via Gemini
         models/text-embedding-004 with task_type='retrieval_query' (Part 5).
      3. Perform Cosine Similarity KNN search in ChromaDB, isolated by project_id (Part 2).
      4. Format matching chunks with file path, line range, raw code, and similarity score.

    Args:
        query: User's natural language search prompt.
        project_id: The ID of the target indexed repository.
        top_k: Maximum number of relevant code chunks to retrieve (1-20, default 5).

    Returns:
        Dictionary conforming to SearchResponse schema.
    """
    query_clean = query.strip()
    if not query_clean:
        return {
            "query": query,
            "project_id": project_id,
            "total_results": 0,
            "results": []
        }

    # Constrain top_k between 1 and 20
    top_k = max(1, min(top_k, 20))

    print(f"[SearchService] Searching project '{project_id}' for: '{query_clean}' (top_k={top_k})")

    # 1. Generate query vector embedding via Gemini (Part 5)
    query_vector = generate_query_embedding(query_clean)

    # 2. Query ChromaDB vector store (Part 2)
    client = get_chroma_client()
    matching_chunks = query_similar_chunks(
        client=client,
        query_embedding=query_vector,
        project_id=project_id,
        top_k=top_k
    )

    print(f"[SearchService] Found {len(matching_chunks)} relevant code chunk(s).")

    return {
        "query": query_clean,
        "project_id": project_id,
        "total_results": len(matching_chunks),
        "results": matching_chunks
    }
