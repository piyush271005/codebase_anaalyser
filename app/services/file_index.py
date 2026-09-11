import os
from pathlib import Path


def build_file_index(analysis_results):

    file_index = {}

    valid_paths = [
        os.path.normpath(r.get("file_path"))
        for r in analysis_results
        if r.get("file_path")
    ]
    if not valid_paths:
        return file_index

    # Determine common repository root
    try:
        repo_root = os.path.commonpath(valid_paths)
        if os.path.isfile(repo_root):
            repo_root = os.path.dirname(repo_root)
    except Exception:
        repo_root = None

    for file_result in analysis_results:

        file_path = file_result.get("file_path")

        if not file_path:
            continue

        norm_fp = os.path.normpath(file_path)
        path = Path(norm_fp)

        # 1. Full/legacy path as module key for fallback compatibility
        full_mod = path.with_suffix("").as_posix().replace("/", ".")
        file_index[full_mod] = file_path

        # 2. Relative module path from repository root
        rel_path = os.path.relpath(norm_fp, repo_root) if repo_root else os.path.basename(norm_fp)
        rel_posix = Path(rel_path).with_suffix("").as_posix()
        parts = rel_posix.split("/")

        # Direct dotted relative path: e.g. "backend.api.router"
        dotted_full = ".".join(parts)
        file_index[dotted_full] = file_path
        file_index[rel_posix] = file_path
        file_index[Path(rel_path).as_posix()] = file_path

        # 3. Sub-paths / suffixes: e.g. "api.router", "router"
        for i in range(1, len(parts)):
            sub_dotted = ".".join(parts[i:])
            if sub_dotted not in file_index:
                file_index[sub_dotted] = file_path
            sub_slash = "/".join(parts[i:])
            if sub_slash not in file_index:
                file_index[sub_slash] = file_path

        # 4. Handle Python __init__.py package imports
        if parts[-1] == "__init__":
            pkg_name = ".".join(parts[:-1])
            if pkg_name not in file_index:
                file_index[pkg_name] = file_path

    return file_index