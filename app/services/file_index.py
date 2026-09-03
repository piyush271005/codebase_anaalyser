from pathlib import Path


def build_file_index(analysis_results):

    file_index = {}

    for file_result in analysis_results:

        file_path = file_result.get("file_path")

        if not file_path:
            continue

        path = Path(file_path)

        # Remove extension
        module_name = path.with_suffix("").as_posix()

        # Convert path separators to Python module notation
        module_name = module_name.replace("/", ".")

        file_index[module_name] = file_path

    return file_index