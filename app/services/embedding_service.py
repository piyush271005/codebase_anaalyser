import os
import time
from google import genai
from google.genai import types

DEFAULT_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 768


def get_embedding_model_name() -> str:
    return os.environ.get("EMBEDDING_MODEL", DEFAULT_MODEL)


def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. "
            "An API key is required to generate vector embeddings."
        )

    return genai.Client(api_key=api_key)


def generate_query_embedding(query: str) -> list[float]:
    """
    Generate a 768-dimensional embedding for a search query.
    """

    try:
        client = get_client()

        response = client.models.embed_content(
            model=get_embedding_model_name(),
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=EMBEDDING_DIMENSION,
            ),
        )

        embedding = response.embeddings[0].values

        if len(embedding) != EMBEDDING_DIMENSION:
            raise RuntimeError(
                f"Expected {EMBEDDING_DIMENSION} dimensions, "
                f"got {len(embedding)}"
            )

        return embedding

    except Exception as e:
        raise RuntimeError(
            f"Gemini query embedding generation failed: {e}"
        )


def generate_document_embeddings(
    texts: list[str],
    batch_size: int = 20
) -> list[list[float]]:
    """
    Generate 768-dimensional embeddings for code chunks.
    """

    if not texts:
        return []

    try:
        client = get_client()
        model = get_embedding_model_name()

        all_embeddings = []

        total_batches = (
            len(texts) + batch_size - 1
        ) // batch_size

        for i in range(0, len(texts), batch_size):

            batch = texts[i:i + batch_size]

            batch_number = i // batch_size + 1

            print(
                f"[EmbeddingService] "
                f"Embedding batch {batch_number}/{total_batches} "
                f"({len(batch)} chunks)..."
            )

            try:
                response = client.models.embed_content(
                    model=model,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=EMBEDDING_DIMENSION,
                    ),
                )

                batch_embeddings = [
                    embedding.values
                    for embedding in response.embeddings
                ]

                # Safety check
                for embedding in batch_embeddings:
                    if len(embedding) != EMBEDDING_DIMENSION:
                        raise RuntimeError(
                            f"Expected {EMBEDDING_DIMENSION} dimensions, "
                            f"got {len(embedding)}"
                        )

                all_embeddings.extend(batch_embeddings)

            except Exception as batch_error:
                raise RuntimeError(
                    f"Gemini batch embedding error "
                    f"(batch index {i}): {batch_error}"
                )

            # Small delay between batches
            if i + batch_size < len(texts):
                time.sleep(0.5)

        return all_embeddings

    except Exception as e:
        raise RuntimeError(
            f"Gemini document embedding generation failed: {e}"
        )