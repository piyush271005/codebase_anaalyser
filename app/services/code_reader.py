from pathlib import Path


def read_function_code(
    file_path: str,
    start_line: int,
    end_line: int
) -> str | None:
    """
    Read a source file and return the function code
    from start_line to end_line (1-indexed, inclusive).

    Returns None if the file doesn't exist or lines are out of range.
    """

    path = Path(file_path)

    if not path.exists():
        return None

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return None

    # Validate line range (1-indexed)
    if start_line < 1 or end_line < start_line:
        return None

    if start_line > len(lines):
        return None

    # Convert to 0-indexed and extract
    code_lines = lines[start_line - 1 : end_line]

    return "\n".join(code_lines)


def read_file_code(file_path: str) -> str | None:
    """
    Read the entire source file and return its content as a string.

    Returns None if the file doesn't exist.
    """

    path = Path(file_path)

    if not path.exists():
        return None

    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None
