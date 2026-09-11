from pathlib import Path


def enrich_code_chunks(
    chunks: list[dict],
    function_summaries: list[dict] | None = None,
    file_summaries: list[dict] | None = None
) -> list[dict]:
    """
    Enriches raw code chunks with Feature 5 semantic summaries.

    Combines:
      - Function Summary (for function chunks)
      - File Summary (for file-level / top-level chunks)
      - Component Metadata (Name, File, Type, Language)
      - Actual Raw Code

    This enriched text is what gets converted into a vector embedding,
    significantly boosting retrieval accuracy during semantic search.

    Args:
        chunks: List of code chunks from Part 3 (extract_code_chunks).
        function_summaries: Optional list of function summaries from Feature 5.
        file_summaries: Optional list of file summaries from Feature 5.

    Returns:
        List of enriched chunk dictionaries ready for embedding and ChromaDB storage.
    """
    function_summaries = function_summaries or []
    file_summaries = file_summaries or []

    # 1. Build lookup dictionaries for O(1) matching
    # Map (file_basename, function_name) -> summary text
    func_lookup = {}
    for fs in function_summaries:
        fname = fs.get("name")
        fpath = fs.get("file_path")
        summary = fs.get("summary")
        if fname and fpath and summary and summary != "No summary available.":
            basename = Path(fpath).name
            func_lookup[(basename, fname)] = summary
            # Also index by full path string if available
            func_lookup[(fpath.replace("\\", "/"), fname)] = summary

    # Map file_basename -> summary text
    file_lookup = {}
    for fls in file_summaries:
        fpath = fls.get("file_path")
        summary = fls.get("summary")
        if fpath and summary and summary != "No summary available.":
            basename = Path(fpath).name
            file_lookup[basename] = summary
            file_lookup[fpath.replace("\\", "/")] = summary

    # 2. Enrich each chunk
    enriched_chunks = []

    for chunk in chunks:
        chunk_copy = dict(chunk)
        chunk_type = chunk_copy.get("chunk_type", "function")
        name = chunk_copy.get("name", "")
        file_path = chunk_copy.get("file_path", "")
        language = chunk_copy.get("language", "Code")
        code = chunk_copy.get("code", "")

        file_basename = Path(file_path).name
        matched_summary = None

        # Try to find matching summary
        if chunk_type == "function":
            matched_summary = (
                func_lookup.get((file_path, name)) or
                func_lookup.get((file_basename, name))
            )
        elif chunk_type == "file":
            matched_summary = (
                file_lookup.get(file_path) or
                file_lookup.get(file_basename)
            )

        # Store summary in chunk metadata
        chunk_copy["summary"] = matched_summary

        # 3. Format the final enriched searchable document content
        header_lines = [
            f"Type: {chunk_type.capitalize()}",
            f"Name: {name}",
            f"File: {file_path}",
            f"Language: {language}"
        ]

        if matched_summary:
            header_lines.append(f"Summary: {matched_summary}")

        header_text = "\n".join(header_lines)

        # The searchable content fuses semantic intent (summary) with syntax (code)
        chunk_copy["content"] = f"{header_text}\n\nCode:\n{code}"

        enriched_chunks.append(chunk_copy)

    return enriched_chunks
