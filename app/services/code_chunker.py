import os
import re
from pathlib import Path

from app.services.code_reader import read_function_code, read_file_code


def sanitize_id(text: str) -> str:
    """
    Sanitizes a string for use in a ChromaDB ID.
    Replaces non-alphanumeric characters with underscores.
    """
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", text).strip("_")


def get_relative_path(file_path: str, clone_path: str | None = None) -> str:
    """
    Computes a clean, forward-slashed relative path from clone_path if available.
    """
    if not file_path:
        return ""
    if clone_path:
        try:
            rel = os.path.relpath(os.path.normpath(file_path), os.path.normpath(clone_path))
            return rel.replace("\\", "/")
        except ValueError:
            pass
    return os.path.normpath(file_path).replace("\\", "/")


def extract_code_chunks(
    analysis_results: list[dict],
    clone_path: str | None = None
) -> list[dict]:
    """
    Extracts structure-aware code chunks from Feature 3 AST analysis:
      1. Function Chunks: Extracted using AST function start and end line ranges.
      2. Class Chunks: Extracted using AST class line ranges.
      3. File-Level Chunks: Top-level code outside functions/classes
         (such as routes, server setup, middleware config, constants).

    Args:
        analysis_results: Output from Feature 3 analyze_files().
        clone_path: Optional path to repository clone root for relative paths.

    Returns:
        List of chunk dictionaries ready for enrichment and indexing.
    """
    chunks = []

    for file_result in analysis_results:
        file_path = file_result.get("file_path")
        language = file_result.get("language", "Code")

        if not file_path:
            continue

        rel_path = get_relative_path(file_path, clone_path)
        path_slug = sanitize_id(rel_path)

        covered_line_ranges = []

        # -------------------------------------------------------------
        # 1. Extract Function Chunks
        # -------------------------------------------------------------
        functions = file_result.get("functions", [])
        for func in functions:
            name = func.get("name")
            line = func.get("line")
            end_line = func.get("end_line")

            if not name or not line or not end_line:
                continue

            covered_line_ranges.append((line, end_line))

            code = read_function_code(file_path, line, end_line)
            if not code or not code.strip():
                continue

            chunk_id = f"{path_slug}_func_{sanitize_id(name)}_{line}"

            chunks.append({
                "chunk_id": chunk_id,
                "name": name,
                "chunk_type": "function",
                "file_path": rel_path,
                "language": language,
                "line": line,
                "end_line": end_line,
                "code": code,
                "content": f"Function: {name}\nFile: {rel_path}\nLanguage: {language}\n\nCode:\n{code}"
            })

        # -------------------------------------------------------------
        # 2. Extract Class Chunks
        # -------------------------------------------------------------
        classes = file_result.get("classes", [])
        for cls in classes:
            name = cls.get("name")
            line = cls.get("line")
            end_line = cls.get("end_line")

            if not name or not line or not end_line:
                continue

            covered_line_ranges.append((line, end_line))

            code = read_function_code(file_path, line, end_line)
            if not code or not code.strip():
                continue

            chunk_id = f"{path_slug}_class_{sanitize_id(name)}_{line}"

            chunks.append({
                "chunk_id": chunk_id,
                "name": name,
                "chunk_type": "class",
                "file_path": rel_path,
                "language": language,
                "line": line,
                "end_line": end_line,
                "code": code,
                "content": f"Class: {name}\nFile: {rel_path}\nLanguage: {language}\n\nCode:\n{code}"
            })

        # -------------------------------------------------------------
        # 3. Extract File-Level / Top-Level Code
        # -------------------------------------------------------------
        full_content = read_file_code(file_path)
        if not full_content:
            continue

        file_lines = full_content.splitlines()

        if not covered_line_ranges:
            # The entire file has no functions or classes (e.g. constants.js or config.js)
            clean_code = "\n".join(file_lines).strip()
            if clean_code:
                chunk_id = f"{path_slug}_file"
                chunks.append({
                    "chunk_id": chunk_id,
                    "name": Path(rel_path).name,
                    "chunk_type": "file",
                    "file_path": rel_path,
                    "language": language,
                    "line": 1,
                    "end_line": len(file_lines),
                    "code": clean_code,
                    "content": f"File: {rel_path}\nLanguage: {language}\n\nCode:\n{clean_code}"
                })
        else:
            # Collect top-level lines outside any function or class
            top_level_lines = []
            for idx, line_text in enumerate(file_lines, start=1):
                # Check if this line number falls inside any function or class
                is_inside = any(start <= idx <= end for start, end in covered_line_ranges)
                if not is_inside:
                    top_level_lines.append(line_text)

            # Only create a top-level chunk if there is meaningful logic (not just blank lines)
            non_empty_lines = [l for l in top_level_lines if l.strip()]
            if len(non_empty_lines) >= 3:
                top_code = "\n".join(top_level_lines).strip()
                chunk_id = f"{path_slug}_top_level"
                chunks.append({
                    "chunk_id": chunk_id,
                    "name": f"{Path(rel_path).name} (top-level)",
                    "chunk_type": "file",
                    "file_path": rel_path,
                    "language": language,
                    "line": 1,
                    "end_line": len(file_lines),
                    "code": top_code,
                    "content": f"File Setup / Top-Level: {rel_path}\nLanguage: {language}\n\nCode:\n{top_code}"
                })

    return chunks
