import uuid
from app.services.clone_service import clone_repository
from app.services.file_discovery_service import discover_source_files
from app.services.code_analysis_service import analyze_files
from app.services.function_summarizer import summarize_functions
from app.services.file_summarizer import summarize_files
from app.services.code_chunker import extract_code_chunks
from app.services.document_enricher import enrich_code_chunks
from app.services.embedding_service import generate_document_embeddings
from app.services.vector_store import (
    get_chroma_client,
    add_chunks_to_vector_store,
    delete_project_chunks
)


def index_repository(
    repo_url: str,
    project_id: str | None = None,
    include_summaries: bool = True,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None
) -> dict:
    """
    Complete Indexing Orchestrator for Feature 6.

    Execution Pipeline:
      1. Clone / Locate repository on disk (Feature 1)
      2. Discover source files (Feature 2)
      3. Perform AST structure analysis (Feature 3)
      4. Optionally generate semantic summaries (Feature 5)
      5. Extract structure-aware code chunks (Part 3)
      6. Enrich chunks with summaries and metadata (Part 4)
      7. Generate vector embeddings via Gemini text-embedding-004 (Part 5)
      8. Persist vectors and metadata in ChromaDB (Part 2)

    Args:
        repo_url: GitHub repository URL to index.
        project_id: Optional unique project ID. Generated if not provided.
        include_summaries: Whether to generate Feature 5 summaries for enrichment.

    Returns:
        Dictionary matching IndexResponse schema.
    """
    # 1. Resolve project_id
    project_id = project_id or str(uuid.uuid4())
    print(f"\n[IndexingService] Starting indexing for project: {project_id} ({repo_url})")

    # 2. Clone repository (Feature 1)
    clone_result = clone_repository(repo_url, project_id)
    clone_path = str(clone_result["clone_path"])
    repository_name = clone_result.get("repository_name", "repository")
    print(f"[IndexingService] Repository ready at: {clone_path}")

    # 3. Discover source files (Feature 2)
    source_files = discover_source_files(clone_path)
    print(f"[IndexingService] Discovered {len(source_files)} source files.")

    # 4. AST Structure Analysis (Feature 3)
    analysis_results = analyze_files(source_files)
    print(f"[IndexingService] Analyzed {len(analysis_results)} files with tree-sitter.")

    # 5. Semantic Summaries (Feature 5 - optional/graceful)
    func_summaries = []
    file_summaries = []
    if include_summaries:
        print(f"[IndexingService] Generating semantic summaries for enrichment using {provider or 'default'}...")
        func_summaries = summarize_functions(
            analysis_results,
            provider=provider,
            model=model,
            api_key=api_key
        )
        file_summaries = summarize_files(
            analysis_results,
            func_summaries,
            provider=provider,
            model=model,
            api_key=api_key
        )

    # 6. Structure-Aware Chunking (Part 3)
    print("[IndexingService] Extracting structure-aware code chunks...")
    raw_chunks = extract_code_chunks(analysis_results, clone_path)
    print(f"[IndexingService] Extracted {len(raw_chunks)} code chunks (functions, classes, file setup).")

    # 7. Document Enrichment (Part 4)
    print("[IndexingService] Enriching chunks with summaries and metadata headers...")
    enriched_chunks = enrich_code_chunks(raw_chunks, func_summaries, file_summaries)

    # 8. Generate Vector Embeddings (Part 5)
    print("[IndexingService] Generating vector embeddings via Gemini gemini-embedding-001...")
    texts_to_embed = [chunk["content"] for chunk in enriched_chunks]
    embeddings = generate_document_embeddings(texts_to_embed, batch_size=20)
    print(f"[IndexingService] Successfully generated {len(embeddings)} embedding vectors.")

    # 9. Store in ChromaDB (Part 2)
    print("[IndexingService] Storing vectors and metadata in ChromaDB...")
    client = get_chroma_client()
    # Clean any previous index for this project to ensure no stale duplicates
    delete_project_chunks(client, project_id)
    total_added = add_chunks_to_vector_store(client, enriched_chunks, embeddings, project_id)
    print(f"[IndexingService] Indexing complete! Total chunks in ChromaDB: {total_added}")

    return {
        "project_id": project_id,
        "repository_name": repository_name,
        "total_chunks": total_added,
        "status": "indexed",
        "message": f"Successfully indexed {total_added} code chunks into ChromaDB."
    }
