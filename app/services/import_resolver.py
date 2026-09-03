import os
from pathlib import Path


def resolve_imports(analysis_results, file_index):

    # Build a lookup of all known file paths
    # Maps normalized posix path -> original file_path
    known_files = {}

    for file_result in analysis_results:
        fp = file_result.get("file_path")
        if fp:
            norm_full = Path(os.path.normpath(fp)).as_posix()
            norm_no_ext = Path(os.path.normpath(fp)).with_suffix("").as_posix()

            known_files[norm_full] = fp
            known_files[norm_no_ext] = fp

    resolved_imports = []

    for file_result in analysis_results:

        source_file = file_result.get("file_path")

        imports = file_result.get("imports", [])

        for import_info in imports:

            module_name = import_info.get("module")

            if not source_file or not module_name:
                continue

            target_file = None

            # 1. For relative imports (JS/TS): ./utils/auth or ../db/index
            if module_name.startswith("."):

                source_dir = os.path.dirname(os.path.normpath(source_file))
                combined = os.path.normpath(os.path.join(source_dir, module_name))
                resolved_posix = Path(combined).as_posix()

                # Try with exact extension
                target_file = known_files.get(resolved_posix)

                # Try without extension
                if target_file is None:
                    no_ext = Path(combined).with_suffix("").as_posix()
                    target_file = known_files.get(no_ext)

                # Try adding /index (Node.js convention: import "./db" -> "./db/index.js")
                if target_file is None:
                    index_path = Path(os.path.join(combined, "index")).as_posix()
                    target_file = known_files.get(index_path)

            # 2. For Python dotted imports: try direct lookup in file_index
            if target_file is None:
                target_file = file_index.get(module_name)

            if not target_file:
                continue

            # Don't add self-imports
            if os.path.normpath(target_file) == os.path.normpath(source_file):
                continue

            resolved_imports.append({
                "source": source_file,
                "target": target_file,
                "module": module_name,
                "line": import_info.get("line")
            })

    return resolved_imports