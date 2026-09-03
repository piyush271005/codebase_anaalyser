from pathlib import Path

IGNORE_DIRECTORIES = {
    ".git",
    "node_modules",
    "venv",
    "__pycache__",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".next",
    ".pytest_cache",
}

SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
}




def discover_source_files(clone_path: str):

        repository = Path(clone_path)

        files = []

        for path in repository.rglob("*"):

            
            if path.is_dir():
                continue

            
            if any(
                ignored in path.parts
                for ignored in IGNORE_DIRECTORIES
            ):
                continue

            
            if path.suffix in SUPPORTED_EXTENSIONS:
                files.append(str(path))

        return files