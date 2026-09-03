from pathlib import Path


LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".h": "C/C++",
    ".hpp": "C++",
    ".c": "C",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".rb": "Ruby",
    ".cs": "C#",
    ".kt": "Kotlin",
    ".swift": "Swift",
}


def detect_language(file_path: str) -> str | None:
    """
    Detect the programming language of a file
    using its file extension.
    """

    extension = Path(file_path).suffix.lower()

    return LANGUAGE_EXTENSIONS.get(extension)


def group_files_by_language(file_paths: list[str]) -> dict[str, list[str]]:
    """
    Group source files according to their programming language.
    """

    grouped_files = {}

    for file_path in file_paths:

        language = detect_language(file_path)

        if language is None:
            continue

        if language not in grouped_files:
            grouped_files[language] = []

        grouped_files[language].append(file_path)

    return grouped_files