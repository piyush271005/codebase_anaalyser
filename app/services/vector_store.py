import os
from typing import Any


COLLECTION_NAME = "codebase_analyzer"


def get_chroma_client() -> Any:
    """
    Initializes and returns a ChromaDB client.

    Supports:
      1. Chroma Cloud / Hosted Online:
         - Set CHROMA_API_KEY (and optionally CHROMA_TENANT, CHROMA_DATABASE)
      2. Remote Self-Hosted Chroma:
         - Set CHROMA_HOST (and optionally CHROMA_PORT, CHROMA_SSL)
      3. Local Fallback:
         - If no remote credentials are provided, falls back to
           persistent local storage under ./chroma_db
    """
    import chromadb

    api_key = os.environ.get("CHROMA_API_KEY")
    tenant = os.environ.get("CHROMA_TENANT", "default_tenant")
    database = os.environ.get("CHROMA_DATABASE", "default_database")
    host = os.environ.get("CHROMA_HOST")
    port = int(os.environ.get("CHROMA_PORT", "8000"))
    ssl = os.environ.get("CHROMA_SSL", "false").lower() == "true"
    persist_dir = os.environ.get("CHROMA_PERSIST_DIR", "chroma_db")

    # 1. Chroma Cloud / Hosted with API Key
    if api_key:
        print(f"[VectorStore] Connecting to Chroma Cloud (tenant={tenant}, db={database})...")
        try:
            # Newer chromadb versions have CloudClient
            if hasattr(chromadb, "CloudClient"):
                return chromadb.CloudClient(
                    tenant=tenant,
                    database=database,
                    api_key=api_key
                )
            else:
                # Fallback via HttpClient with authorization header
                return chromadb.HttpClient(
                    host="api.trychroma.com",
                    ssl=True,
                    headers={"x-chroma-token": api_key},
                    tenant=tenant,
                    database=database
                )
        except Exception as e:
            print(f"[VectorStore] Error connecting to Chroma Cloud: {e}. Falling back to persistent client.")

    # 2. Remote Self-Hosted Chroma instance
    if host:
        print(f"[VectorStore] Connecting to remote ChromaDB at {host}:{port} (ssl={ssl})...")
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            return chromadb.HttpClient(
                host=host,
                port=port,
                ssl=ssl,
                headers=headers
            )
        except Exception as e:
            print(f"[VectorStore] Error connecting to remote Chroma: {e}. Falling back to persistent client.")

    # 3. Local Persistent Client (Fallback / Offline Dev)
    print(f"[VectorStore] Using local persistent ChromaDB storage in '{persist_dir}'.")
    return chromadb.PersistentClient(path=persist_dir)


def get_or_create_collection(client: Any, collection_name: str = COLLECTION_NAME) -> Any:
    """
    Gets or creates a collection in ChromaDB.
    Cosine similarity is used for code vector search.
    """
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )


def add_chunks_to_vector_store(
    client: Any,
    chunks: list[dict],
    embeddings: list[list[float]],
    project_id: str
) -> int:
    """
    Inserts or updates code chunks and their embeddings in ChromaDB.

    Args:
        client: ChromaDB client instance
        chunks: List of chunk dictionaries (with chunk_id, content, code, metadata)
        embeddings: List of embedding vectors corresponding to each chunk
        project_id: The ID of the repository/project

    Returns:
        Number of chunks added.
    """
    if not chunks:
        return 0

    collection = get_or_create_collection(client)

    ids = []
    documents = []
    metadatas = []
    vectors = []

    for chunk, vector in zip(chunks, embeddings):
        chunk_id = chunk["chunk_id"]
        # In ChromaDB, each ID must be unique. Prefix with project_id if not already
        if not chunk_id.startswith(project_id):
            full_id = f"{project_id}::{chunk_id}"
        else:
            full_id = chunk_id

        # Chroma metadata must be flat (str, int, float, bool)
        metadata = {
            "project_id": str(project_id),
            "file_path": str(chunk.get("file_path", "")),
            "language": str(chunk.get("language", "")),
            "chunk_type": str(chunk.get("chunk_type", "function")),
            "name": str(chunk.get("name", "")),
            "line": int(chunk.get("line") or 0),
            "end_line": int(chunk.get("end_line") or 0),
            # Store the raw code in metadata so we can return it during search
            "code": str(chunk.get("code", "")),
            "summary": str(chunk.get("summary", "") or "")
        }

        ids.append(full_id)
        # Searchable enriched text
        documents.append(chunk["content"])
        metadatas.append(metadata)
        vectors.append(vector)

    # Upsert in ChromaDB (adds new or updates existing)
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=vectors,
        metadatas=metadatas
    )

    return len(ids)


def query_similar_chunks(
    client: Any,
    query_embedding: list[float],
    project_id: str,
    top_k: int = 5
) -> list[dict]:
    """
    Queries ChromaDB for the most semantically similar code chunks
    belonging to the given project_id.

    Returns:
        List of result dictionaries containing chunk metadata, code, and similarity score.
    """
    collection = get_or_create_collection(client)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"project_id": str(project_id)}
    )

    parsed_results = []

    if not results or not results.get("ids") or not results["ids"][0]:
        return parsed_results

    matched_ids = results["ids"][0]
    matched_metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(matched_ids)
    matched_distances = results["distances"][0] if results.get("distances") else [0.0] * len(matched_ids)

    for chunk_id, meta, distance in zip(matched_ids, matched_metadatas, matched_distances):
        # Convert cosine distance to cosine similarity: similarity = 1.0 - distance
        similarity_score = round(max(0.0, 1.0 - float(distance)), 4)

        parsed_results.append({
            "chunk_id": chunk_id,
            "file_path": meta.get("file_path", ""),
            "chunk_type": meta.get("chunk_type", "function"),
            "name": meta.get("name", ""),
            "code": meta.get("code", ""),
            "summary": meta.get("summary") or None,
            "line": meta.get("line") or None,
            "end_line": meta.get("end_line") or None,
            "score": similarity_score
        })

    return parsed_results


def delete_project_chunks(client: Any, project_id: str) -> None:
    """
    Deletes all vector chunks belonging to a project_id from ChromaDB.
    """
    collection = get_or_create_collection(client)
    collection.delete(where={"project_id": str(project_id)})
