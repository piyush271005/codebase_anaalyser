import os
import uuid

from fastapi import HTTPException

from app.services.github_service import check_repository_access
from app.services.clone_service import clone_repository
from app.services.project_info_service import detect_project_info
from app.services.file_discovery_service import discover_source_files
from app.services.code_analysis_service import analyze_files
from app.utils.validator import validate_github_url


def analyze_repository(repo_url: str):
    # 1. Validate URL
    validate_github_url(repo_url)

    # 2. Check repository
    check_repository_access(repo_url)
    project_id = str(uuid.uuid4())

    clone_result = clone_repository(repo_url, project_id)

    project_id = clone_result["project_id"]
    clone_path = clone_result["clone_path"]
    repository_name = clone_result["repository_name"]

    project_info = detect_project_info(clone_path)

    # 5. Discover source files
    source_files = discover_source_files(clone_path)

    # Perform AST analysis on all discovered files
    analysis_results = analyze_files(source_files)

    total_functions = 0
    total_classes = 0
    for file_item in analysis_results:
        funcs = file_item.get("functions", [])
        clss = file_item.get("classes", [])
        total_functions += len(funcs)
        total_classes += len(clss)
        fp = file_item.get("file_path")
        if fp and os.path.exists(fp):
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    file_item["code"] = f.read()
            except Exception:
                file_item["code"] = ""

    owner = repo_url.rstrip("/").split("/")[-2]
    repo_metadata = check_repository_access(repo_url)

    # 6. Return response
    return {
        "success": True,
        "project_id": project_id,
        "repository": {
            "name": repository_name,
            "owner": owner,
            "description": repo_metadata.get("description"),
            "default_branch": repo_metadata.get("default_branch", "main"),
            "clone_url": repo_url,
        },
        "clone_path": str(clone_path),
        "project_info": project_info,
        "total_source_files": len(source_files),
        "source_files": source_files,
        "files": analysis_results,
        "total_functions": total_functions,
        "total_classes": total_classes,
    }