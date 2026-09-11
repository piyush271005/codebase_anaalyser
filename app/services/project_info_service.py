import json
from collections import Counter
from pathlib import Path
from app.services.language_detector import detect_language


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
}


def _find_config_files(repo_path: Path, filename: str) -> list[Path]:
    """
    Finds config files at root or in immediate 1st/2nd level subdirectories (monorepo support).
    """
    matches = []
    root_match = repo_path / filename
    if root_match.exists():
        matches.append(root_match)

    # Search depth 1 and 2
    for child in repo_path.iterdir():
        if child.is_dir() and child.name not in IGNORE_DIRECTORIES and not child.name.startswith('.'):
            sub = child / filename
            if sub.exists():
                matches.append(sub)
            for subchild in child.iterdir():
                if subchild.is_dir() and subchild.name not in IGNORE_DIRECTORIES and not subchild.name.startswith('.'):
                    sub2 = subchild / filename
                    if sub2.exists():
                        matches.append(sub2)
    return matches


def _count_source_languages(repo_path: Path) -> dict[str, int]:
    """
    Counts actual source files by language across the repository.
    """
    lang_counts = Counter()
    try:
        for path in repo_path.rglob("*"):
            if path.is_file():
                if any(ignored in path.parts for ignored in IGNORE_DIRECTORIES):
                    continue
                lang = detect_language(str(path))
                if lang:
                    lang_counts[lang] += 1
    except Exception:
        pass
    return dict(lang_counts)


def detect_project_info(clone_path: str) -> dict:
    """
    Detects detailed information about the cloned project using both
    configuration files and actual source code file distributions.

    Returns:
        {
            "language": "...",
            "framework": "...",
            "package_manager": "...",
            "build_tool": "...",
            "has_readme": True/False,
            "has_docker": True/False,
            "has_gitignore": True/False,
            "language_distribution": { ... }
        }
    """
    repo_path = Path(clone_path)

    project_info = {
        "language": "Unknown",
        "framework": "Unknown",
        "package_manager": "Unknown",
        "build_tool": "Unknown",
        "has_readme": False,
        "has_docker": False,
        "has_gitignore": False,
    }

    # 1. Basic Files Check
    project_info["has_readme"] = (repo_path / "README.md").exists() or (repo_path / "readme.md").exists()
    project_info["has_docker"] = (repo_path / "Dockerfile").exists() or (repo_path / "docker-compose.yml").exists()
    project_info["has_gitignore"] = (repo_path / ".gitignore").exists()

    # 2. Count actual source files by language
    lang_dist = _count_source_languages(repo_path)
    project_info["language_distribution"] = lang_dist

    # 3. Check for Python
    requirements_files = _find_config_files(repo_path, "requirements.txt")
    pyproject_files = _find_config_files(repo_path, "pyproject.toml")

    if requirements_files or pyproject_files:
        project_info["package_manager"] = "pip"
        for req in requirements_files:
            try:
                text = req.read_text(encoding="utf-8", errors="ignore").lower()
                if "fastapi" in text:
                    project_info["framework"] = "FastAPI"
                elif "django" in text:
                    project_info["framework"] = "Django"
                elif "flask" in text:
                    project_info["framework"] = "Flask"
            except Exception:
                pass

        if pyproject_files:
            for pyp in pyproject_files:
                if (pyp.parent / "poetry.lock").exists():
                    project_info["package_manager"] = "Poetry"

    # 4. Check for JavaScript / TypeScript
    package_json_files = _find_config_files(repo_path, "package.json")
    has_tsconfig = bool(_find_config_files(repo_path, "tsconfig.json"))

    if package_json_files:
        for pkg_path in package_json_files:
            try:
                with open(pkg_path, "r", encoding="utf-8", errors="ignore") as f:
                    package = json.load(f)

                dependencies = {}
                dependencies.update(package.get("dependencies", {}))
                dependencies.update(package.get("devDependencies", {}))

                if "typescript" in dependencies or has_tsconfig:
                    has_tsconfig = True

                if "react" in dependencies or "react-dom" in dependencies:
                    project_info["framework"] = "React"
                elif "next" in dependencies:
                    project_info["framework"] = "Next.js"
                elif "express" in dependencies:
                    project_info["framework"] = "Express"
                elif "vue" in dependencies:
                    project_info["framework"] = "Vue"
                elif "@angular/core" in dependencies:
                    project_info["framework"] = "Angular"
                elif "nest" in dependencies or "@nestjs/core" in dependencies:
                    project_info["framework"] = "NestJS"

                parent = pkg_path.parent
                if (parent / "package-lock.json").exists():
                    project_info["package_manager"] = "npm"
                elif (parent / "yarn.lock").exists():
                    project_info["package_manager"] = "Yarn"
                elif (parent / "pnpm-lock.yaml").exists():
                    project_info["package_manager"] = "pnpm"
                elif (parent / "bun.lockb").exists() or (parent / "bun.lock").exists():
                    project_info["package_manager"] = "Bun"
            except Exception:
                pass

    # 5. Check Java
    pom_files = _find_config_files(repo_path, "pom.xml")
    gradle_files = _find_config_files(repo_path, "build.gradle")
    if pom_files:
        project_info["build_tool"] = "Maven"
    elif gradle_files:
        project_info["build_tool"] = "Gradle"

    # 6. Check C#
    if list(repo_path.glob("*.csproj")) or list(repo_path.rglob("*.csproj")):
        project_info["build_tool"] = ".NET"

    # 7. Check C++
    if (repo_path / "CMakeLists.txt").exists():
        project_info["build_tool"] = "CMake"
    elif (repo_path / "Makefile").exists():
        project_info["build_tool"] = "Make"

    # 8. Check Go
    go_mod_files = _find_config_files(repo_path, "go.mod")
    if go_mod_files:
        project_info["package_manager"] = "go modules"

    # 9. Check Rust
    cargo_files = _find_config_files(repo_path, "Cargo.toml")
    if cargo_files:
        project_info["package_manager"] = "cargo"

    # 10. DETERMINE PRIMARY LANGUAGE
    # If we have actual source files, the dominant source file language wins!
    if lang_dist:
        # Sort languages by file count descending
        sorted_langs = sorted(lang_dist.items(), key=lambda x: x[1], reverse=True)
        dominant_lang = sorted_langs[0][0]

        # If TypeScript and JavaScript both exist, prioritize TypeScript if tsconfig exists or ts >= js
        if has_tsconfig or lang_dist.get("TypeScript", 0) > 0:
            if lang_dist.get("TypeScript", 0) >= lang_dist.get("JavaScript", 0):
                dominant_lang = "TypeScript"

        project_info["language"] = dominant_lang
    elif package_json_files:
        project_info["language"] = "TypeScript" if has_tsconfig else "JavaScript"
    elif requirements_files or pyproject_files:
        project_info["language"] = "Python"
    elif pom_files or gradle_files:
        project_info["language"] = "Java"
    elif go_mod_files:
        project_info["language"] = "Go"
    elif cargo_files:
        project_info["language"] = "Rust"

    return project_info