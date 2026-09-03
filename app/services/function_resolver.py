from pathlib import Path


def resolve_function_calls(analysis_results, function_index):

    resolved_calls = []

    for file_result in analysis_results:

        file_path = file_result.get("file_path")
        language = file_result.get("language")

        calls = file_result.get("calls", [])

        for call in calls:

            caller_name = call.get("caller")
            callee_name = call.get("callee")

            if not callee_name:
                continue

            # --- Resolve caller ---

            if caller_name:

                caller_candidates = function_index.get(caller_name, [])

                # Find the caller in the current file
                caller_info = None

                for candidate in caller_candidates:

                    if candidate["file_path"] == file_path:
                        caller_info = candidate
                        break

                # If not found in current file, use first candidate
                if caller_info is None and caller_candidates:
                    caller_info = caller_candidates[0]

                # If caller is not in the index at all,
                # still include it with the current file
                if caller_info is None:
                    caller_info = {
                        "name": caller_name,
                        "file_path": file_path,
                        "language": language,
                        "line": None
                    }

            else:
                # Top-level call (no enclosing function)
                # Use the file name as the caller
                file_label = Path(file_path).name if file_path else "unknown"

                caller_info = {
                    "name": file_label,
                    "file_path": file_path,
                    "language": language,
                    "line": None
                }

            # --- Resolve callee ---

            callee_candidates = function_index.get(callee_name, [])

            if callee_candidates:

                # Try to find callee in the same file first
                callee_info = None

                for candidate in callee_candidates:

                    if candidate["file_path"] == file_path:
                        callee_info = candidate
                        break

                # If not found in same file, use first candidate
                if callee_info is None:
                    callee_info = callee_candidates[0]

            else:
                # External/library function — not defined in the repo
                callee_info = {
                    "name": callee_name,
                    "file_path": "external",
                    "language": None,
                    "line": None
                }

            resolved_calls.append({
                "caller": caller_info,
                "callee": callee_info,
                "call_line": call.get("line")
            })

    return resolved_calls