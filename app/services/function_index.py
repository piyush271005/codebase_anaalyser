def build_function_index(analysis_results):
    function_index = {}

    for file_result in analysis_results:

        file_path = file_result.get("file_path")
        language = file_result.get("language")

        if not file_path:
            continue

        functions = file_result.get("functions", [])

        for function in functions:

            function_name = function.get("name")

            if not function_name:
                continue

            function_index.setdefault(function_name, []).append({
                "name": function_name,
                "file_path": file_path,
                "language": language,
                "line": function.get("line")
            })

    return function_index