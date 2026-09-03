import os
from pathlib import Path


def detect_modules(
    analysis_results: list[dict],
    clone_path: str
) -> list[dict]:
    """
    Group source files into modules based on their directory structure.

    For example, files inside src/controllers/ become the "controllers" module,
    files inside src/utils/ become the "utils" module, and files at the
    root level (e.g., src/app.js) become the "root" module.

    Returns a list of modules, each with a name, path, and list of files.
    """

    # Normalize the clone path for consistent comparison
    clone_path_normalized = os.path.normpath(clone_path)

    # Dictionary to group files by their parent directory
    # Key: relative directory path (e.g., "src/controllers")
    # Value: list of file paths
    module_groups = {}

    for file_result in analysis_results:

        file_path = file_result.get("file_path")

        if not file_path:
            continue

        # Normalize the file path
        file_path_normalized = os.path.normpath(file_path)

        # Calculate the relative path from the clone root
        # Example:
        #   clone_path = "D:\...\repositories\abc123"
        #   file_path  = "D:\...\repositories\abc123\src\controllers\user.controller.js"
        #   relative   = "src\controllers\user.controller.js"
        try:
            relative_path = os.path.relpath(
                file_path_normalized,
                clone_path_normalized
            )
        except ValueError:
            # On Windows, relpath fails if paths are on different drives
            relative_path = file_path_normalized

        # Get the parent directory of the file
        # Example: "src\controllers\user.controller.js" → "src\controllers"
        parent_dir = str(Path(relative_path).parent)

        # Normalize to forward slashes for consistency
        parent_dir = parent_dir.replace("\\", "/")

        # If the file is directly in the clone root, parent_dir will be "."
        # We rename this to "root" for clarity
        if parent_dir == ".":
            parent_dir = "root"

        # Group the file under its parent directory
        if parent_dir not in module_groups:
            module_groups[parent_dir] = []

        module_groups[parent_dir].append(file_path)

    # Convert the dictionary into a list of module dictionaries
    modules = []

    for dir_path, files in module_groups.items():

        # The module name is the last part of the directory path
        # Example: "src/controllers" → "controllers"
        #          "src/utils"       → "utils"
        #          "root"            → "root"
        if dir_path == "root":
            module_name = "root"
        else:
            module_name = dir_path.split("/")[-1]

        modules.append({
            "name": module_name,
            "path": dir_path,
            "files": files
        })

    # Sort modules alphabetically by name for consistent output
    modules.sort(key=lambda m: m["name"])

    return modules
