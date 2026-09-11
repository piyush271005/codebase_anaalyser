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

            # If index or __init__ file, allow resolving via directory path
            base_name = Path(fp).name
            if base_name in ("__init__.py", "index.js", "index.jsx", "index.ts", "index.tsx"):
                dir_posix = Path(os.path.dirname(os.path.normpath(fp))).as_posix()
                known_files[dir_posix] = fp

    resolved_imports = []

    for file_result in analysis_results:

        source_file = file_result.get("file_path")

        imports = file_result.get("imports", [])

        for import_info in imports:

            module_name = import_info.get("module")

            if not source_file or not module_name:
                continue

            target_file = None

            # 1. Relative imports
            if module_name.startswith("."):

                source_dir = os.path.dirname(os.path.normpath(source_file))

                # Python relative imports: e.g. ".router", "..config", "."
                if "/" not in module_name and "\\" not in module_name:
                    leading_dots = len(module_name) - len(module_name.lstrip("."))
                    remainder = module_name[leading_dots:]

                    target_dir = source_dir
                    for _ in range(leading_dots - 1):
                        target_dir = os.path.dirname(target_dir)

                    if remainder:
                        sub_parts = remainder.split(".")
                        combined = os.path.normpath(os.path.join(target_dir, *sub_parts))
                    else:
                        combined = os.path.normpath(target_dir)

                    resolved_posix = Path(combined).as_posix()
                    target_file = known_files.get(resolved_posix)

                    if target_file is None:
                        target_file = known_files.get(Path(combined + ".py").as_posix())
                    if target_file is None:
                        init_path = Path(os.path.join(combined, "__init__.py")).as_posix()
                        target_file = known_files.get(init_path)
                    if target_file is None and remainder:
                        target_file = file_index.get(remainder)

                else:
                    # JS/TS relative imports: ./utils/auth or ../db/index
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

            # 2. Dotted module lookup in file_index
            if target_file is None:
                target_file = file_index.get(module_name)

            # 3. Fallback: Check if module_name includes an imported function/class symbol
            if target_file is None and "." in module_name:
                parent_module = module_name.rsplit(".", 1)[0]
                target_file = file_index.get(parent_module)

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