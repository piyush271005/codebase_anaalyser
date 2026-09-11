import os
from pathlib import Path


def build_dependency_graph(resolved_imports: list[dict], all_files: list[dict] | list[str] | None = None) -> dict:

    nodes = {}
    edges = []

    # Collect all paths to compute common repository root for clean labels
    all_file_paths = []
    if all_files:
        for f in all_files:
            fp = f.get("file_path") if isinstance(f, dict) else f
            if fp:
                all_file_paths.append(os.path.normpath(fp))

    for imp in resolved_imports:
        if imp.get("source"):
            all_file_paths.append(os.path.normpath(imp["source"]))
        if imp.get("target"):
            all_file_paths.append(os.path.normpath(imp["target"]))

    try:
        repo_root = os.path.commonpath(all_file_paths) if all_file_paths else None
        if repo_root and os.path.isfile(repo_root):
            repo_root = os.path.dirname(repo_root)
    except Exception:
        repo_root = None

    def get_clean_label(fp: str) -> str:
        norm = os.path.normpath(fp)
        if repo_root:
            try:
                rel = os.path.relpath(norm, repo_root)
                return rel.replace("\\", "/")
            except Exception:
                pass
        return Path(norm).name

    # 1. Pre-populate all repository files as nodes
    if all_files:
        for f in all_files:
            fp = f.get("file_path") if isinstance(f, dict) else f
            if not fp:
                continue
            norm_fp = os.path.normpath(fp)
            nodes[norm_fp] = {
                "id": norm_fp,
                "type": "file",
                "label": get_clean_label(norm_fp),
                "file_path": norm_fp
            }

    # 2. Add source & target nodes and import edges
    for import_info in resolved_imports:

        source_file = import_info.get("source")
        target_file = import_info.get("target")

        if not source_file or not target_file:
            continue

        norm_source = os.path.normpath(source_file)
        norm_target = os.path.normpath(target_file)

        # Add source node if not already present
        if norm_source not in nodes:
            nodes[norm_source] = {
                "id": norm_source,
                "type": "file",
                "label": get_clean_label(norm_source),
                "file_path": norm_source
            }

        # Add target node if not already present
        if norm_target not in nodes:
            nodes[norm_target] = {
                "id": norm_target,
                "type": "file",
                "label": get_clean_label(norm_target),
                "file_path": norm_target
            }

        # Add dependency relationship
        edges.append({
            "source": norm_source,
            "target": norm_target,
            "type": "imports",
            "line": import_info.get("line")
        })

    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }