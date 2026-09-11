import os
from pathlib import Path
from typing import Any

from app.schemas.retrieval import QuestionType, ClassificationResult
from app.services.file_discovery_service import discover_source_files
from app.services.code_analysis_service import analyze_files
from app.services.project_info_service import detect_project_info
from app.services.graph_service import generate_graphs
from app.services.module_detector import detect_modules
from app.services.code_reader import read_function_code, read_file_code
from app.services.search_service import search_codebase


REPOSITORIES_DIR = Path("repositories")


def get_repository_path(project_id: str) -> Path | None:
    """
    Locates the local clone path for a given project_id.
    """
    repo_path = REPOSITORIES_DIR / project_id
    if repo_path.exists():
        return repo_path
    return None


def get_project_overview_context(project_id: str) -> dict[str, Any]:
    """
    Retrieval strategy for PROJECT_OVERVIEW questions.
    Gathers project metadata (Feature 2) and high-level module structure (Feature 5).
    """
    repo_path = get_repository_path(project_id)
    if not repo_path:
        return {"error": f"Repository not found for project_id: {project_id}"}

    project_info = detect_project_info(str(repo_path))
    source_files = discover_source_files(str(repo_path))
    analysis_results = analyze_files(source_files)
    modules = detect_modules(analysis_results, str(repo_path))

    return {
        "project_id": project_id,
        "language": project_info.get("language", "Unknown"),
        "framework": project_info.get("framework", "Unknown"),
        "package_manager": project_info.get("package_manager", "Unknown"),
        "total_source_files": len(source_files),
        "modules": [
            {
                "name": m["name"],
                "path": m["path"],
                "file_count": len(m["files"])
            }
            for m in modules
        ]
    }


def get_architecture_context(project_id: str) -> dict[str, Any]:
    """
    Retrieval strategy for ARCHITECTURE questions.
    Combines module structure (Feature 5) with dependency graph and call graph statistics (Feature 4).
    """
    repo_path = get_repository_path(project_id)
    if not repo_path:
        return {"error": f"Repository not found for project_id: {project_id}"}

    source_files = discover_source_files(str(repo_path))
    analysis_results = analyze_files(source_files)
    modules = detect_modules(analysis_results, str(repo_path))
    graph_data = generate_graphs(analysis_results)

    dep_graph = graph_data.get("dependency_graph", {})
    call_graph = graph_data.get("function_call_graph", {})

    # Extract high-level inter-module dependencies
    dependencies_summary = [
        {"from": edge.get("source"), "to": edge.get("target")}
        for edge in dep_graph.get("edges", [])[:15]
    ]

    return {
        "project_id": project_id,
        "modules": [
            {"name": m["name"], "path": m["path"], "file_count": len(m["files"])}
            for m in modules
        ],
        "total_dependencies": len(dep_graph.get("edges", [])),
        "total_function_calls": len(call_graph.get("edges", [])),
        "key_dependencies": dependencies_summary
    }


def get_function_context(project_id: str, function_name: str | None) -> dict[str, Any]:
    """
    Retrieval strategy for FUNCTION questions.
    Locates the target function in AST analysis, extracts its parameters, line numbers,
    and reads the exact raw source code from disk.
    """
    if not function_name:
        return {"error": "No function name specified for function retrieval."}

    repo_path = get_repository_path(project_id)
    if not repo_path:
        return {"error": f"Repository not found for project_id: {project_id}"}

    source_files = discover_source_files(str(repo_path))
    analysis_results = analyze_files(source_files)

    matches = []
    target_lower = function_name.lower().strip()

    for file_res in analysis_results:
        fpath = file_res.get("file_path", "")
        for func in file_res.get("functions", []):
            name = func.get("name", "")
            if name.lower() == target_lower:
                code = read_function_code(fpath, func.get("line"), func.get("end_line"))
                rel_path = os.path.relpath(fpath, str(repo_path)).replace("\\", "/")
                matches.append({
                    "name": name,
                    "file_path": rel_path,
                    "language": file_res.get("language", "Code"),
                    "line": func.get("line"),
                    "end_line": func.get("end_line"),
                    "parameters": func.get("parameters", []),
                    "code": code
                })

    if not matches:
        return {
            "target_function": function_name,
            "found": False,
            "message": f"Function '{function_name}' was not found in the codebase AST."
        }

    return {
        "target_function": function_name,
        "found": True,
        "match_count": len(matches),
        "functions": matches
    }


def get_file_context(project_id: str, file_target: str | None) -> dict[str, Any]:
    """
    Retrieval strategy for FILE questions.
    Locates the specific file, retrieves its AST elements (functions, classes, imports),
    and extracts its raw source code.
    """
    if not file_target:
        return {"error": "No file name or path specified for file retrieval."}

    repo_path = get_repository_path(project_id)
    if not repo_path:
        return {"error": f"Repository not found for project_id: {project_id}"}

    source_files = discover_source_files(str(repo_path))
    analysis_results = analyze_files(source_files)

    normalized_target = file_target.replace("\\", "/").lower().strip()
    target_basename = Path(file_target).name.lower()

    matched_result = None
    for file_res in analysis_results:
        fpath = file_res.get("file_path", "").replace("\\", "/")
        rel_path = os.path.relpath(fpath, str(repo_path)).replace("\\", "/")

        if rel_path.lower() == normalized_target or Path(fpath).name.lower() == target_basename:
            matched_result = file_res
            break

    if not matched_result:
        return {
            "target_file": file_target,
            "found": False,
            "message": f"File '{file_target}' was not found in the codebase."
        }

    abs_path = matched_result.get("file_path", "")
    rel_path = os.path.relpath(abs_path, str(repo_path)).replace("\\", "/")
    full_code = read_file_code(abs_path)

    return {
        "target_file": file_target,
        "file_path": rel_path,
        "found": True,
        "language": matched_result.get("language", "Code"),
        "functions_count": len(matched_result.get("functions", [])),
        "functions": [f.get("name") for f in matched_result.get("functions", [])],
        "classes": [c.get("name") for c in matched_result.get("classes", [])],
        "imports": [i.get("module") for i in matched_result.get("imports", [])],
        "code": full_code
    }


def get_semantic_search_context(project_id: str, query: str, top_k: int = 5) -> dict[str, Any]:
    """
    Retrieval strategy for SEMANTIC_SEARCH questions (Part 7).
    Executes Feature 6 semantic search across ChromaDB vector store.
    """
    search_res = search_codebase(query=query, project_id=project_id, top_k=top_k)

    return {
        "project_id": project_id,
        "query": query,
        "total_results": search_res.get("total_results", 0),
        "chunks": search_res.get("results", [])
    }


def retrieve_context(
    classification: ClassificationResult,
    project_id: str,
    top_k: int = 5,
    question: str = ""
) -> tuple[str, dict[str, Any]]:
    """
    Context Retrieval Router for Feature 7.
    Routes the classified question to the specialized retrieval strategy.

    Returns:
        tuple of (strategy_name: str, context_data: dict)
    """
    q_type = classification.question_type
    target = classification.target_name

    if q_type == QuestionType.PROJECT_OVERVIEW:
        return "project_overview_context", get_project_overview_context(project_id)

    elif q_type == QuestionType.ARCHITECTURE:
        return "architecture_context", get_architecture_context(project_id)

    elif q_type == QuestionType.FUNCTION:
        return "function_context", get_function_context(project_id, target)

    elif q_type == QuestionType.FILE:
        return "file_context", get_file_context(project_id, target)

    # SEMANTIC_SEARCH (Part 7)
    return "semantic_search_context", get_semantic_search_context(
        project_id=project_id,
        query=question,
        top_k=top_k
    )
