import json
from pathlib import Path


def detect_project_info(clone_path: str) -> dict:
    """
    Detects basic information about the cloned project.

    Returns:
        {
            "language": "...",
            "framework": "...",
            "package_manager": "...",
            "build_tool": "...",
            "has_readme": True/False,
            "has_docker": True/False,
            "has_gitignore": True/False
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

    # -----------------------------------------------------
    # Basic Files
    # -----------------------------------------------------

    project_info["has_readme"] = (
        repo_path / "README.md"
    ).exists()

    project_info["has_docker"] = (
        repo_path / "Dockerfile"
    ).exists()

    project_info["has_gitignore"] = (
        repo_path / ".gitignore"
    ).exists()

    # -----------------------------------------------------
    # Python Projects
    # -----------------------------------------------------

    requirements = repo_path / "requirements.txt"

    if requirements.exists():

        project_info["language"] = "Python"
        project_info["package_manager"] = "pip"

        text = requirements.read_text(
            encoding="utf-8",
            errors="ignore"
        ).lower()

        if "fastapi" in text:
            project_info["framework"] = "FastAPI"

        elif "django" in text:
            project_info["framework"] = "Django"

        elif "flask" in text:
            project_info["framework"] = "Flask"

    # Poetry

    if (repo_path / "pyproject.toml").exists():

        project_info["language"] = "Python"

        if (repo_path / "poetry.lock").exists():
            project_info["package_manager"] = "Poetry"

    # -----------------------------------------------------
    # JavaScript / TypeScript
    # -----------------------------------------------------

    package_json = repo_path / "package.json"

    if package_json.exists():

        project_info["language"] = "JavaScript"

        with open(
            package_json,
            "r",
            encoding="utf-8"
        ) as f:

            package = json.load(f)

        dependencies = {}

        dependencies.update(
            package.get("dependencies", {})
        )

        dependencies.update(
            package.get("devDependencies", {})
        )

        if "react" in dependencies:
            project_info["framework"] = "React"

        elif "next" in dependencies:
            project_info["framework"] = "Next.js"

        elif "express" in dependencies:
            project_info["framework"] = "Express"

        elif "vue" in dependencies:
            project_info["framework"] = "Vue"

        elif "@angular/core" in dependencies:
            project_info["framework"] = "Angular"

        if (repo_path / "package-lock.json").exists():
            project_info["package_manager"] = "npm"

        elif (repo_path / "yarn.lock").exists():
            project_info["package_manager"] = "Yarn"

        elif (repo_path / "pnpm-lock.yaml").exists():
            project_info["package_manager"] = "pnpm"

    # -----------------------------------------------------
    # Java
    # -----------------------------------------------------

    if (repo_path / "pom.xml").exists():

        project_info["language"] = "Java"
        project_info["build_tool"] = "Maven"

    elif (repo_path / "build.gradle").exists():

        project_info["language"] = "Java"
        project_info["build_tool"] = "Gradle"

    # -----------------------------------------------------
    # C#
    # -----------------------------------------------------

    if list(repo_path.glob("*.csproj")):

        project_info["language"] = "C#"
        project_info["build_tool"] = ".NET"

    # -----------------------------------------------------
    # C++
    # -----------------------------------------------------

    if (repo_path / "CMakeLists.txt").exists():

        project_info["language"] = "C++"
        project_info["build_tool"] = "CMake"

    elif (repo_path / "Makefile").exists():

        project_info["language"] = "C++"
        project_info["build_tool"] = "Make"

    return project_info