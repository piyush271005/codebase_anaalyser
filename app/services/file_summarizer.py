from app.services.llm_client import call_llm


def summarize_files(
    analysis_results: list[dict],
    function_summaries: list[dict]
) -> list[dict]:
    """
    Generate a summary for each source file by combining function summaries,
    class info, and imports.

    Returns a list of dictionaries with file metadata and the summary.
    """
    file_summaries = []

    # Create a quick lookup dictionary for function summaries by file_path
    # This avoids nested looping, making it O(N) instead of O(N^2)
    func_lookup = {}
    for fs in function_summaries:
        fp = fs["file_path"]
        if fp not in func_lookup:
            func_lookup[fp] = []
        func_lookup[fp].append(fs)

    for file_result in analysis_results:
        file_path = file_result.get("file_path")
        language = file_result.get("language", "Code")

        if not file_path:
            continue

        # Extract classes, imports, and functions specific to this file
        classes = [c.get("name") for c in file_result.get("classes", []) if c.get("name")]
        imports_count = len(file_result.get("imports", []))
        
        # Get the pre-generated function summaries for this file
        file_funcs = func_lookup.get(file_path, [])
        function_names = [f["name"] for f in file_funcs]

        # 1. Build the list of function summaries for the prompt
        function_context = ""
        if file_funcs:
            function_context = "Functions in this file:\n"
            for f in file_funcs:
                function_context += f"- {f['name']}: {f['summary']}\n"
        else:
            function_context = "No functions defined in this file.\n"

        # 2. Build the class context for the prompt
        class_context = ""
        if classes:
            class_context = f"Classes defined: {', '.join(classes)}\n"

        # 3. Build the prompt
        prompt = f"""You are an expert code analyst.
Summarize the overall purpose and responsibilities of this source file in 1-3 sentences.
Base your summary on the provided metadata and function descriptions.

File: {file_path}
Language: {language}
Number of imports: {imports_count}

{class_context}
{function_context}

Return ONLY the summary text, with no markdown formatting, no conversational filler, and no introduction."""

        # 4. Call the LLM (Part 2)
        print(f"Summarizing file: {file_path.split('/')[-1]}...")
        summary = call_llm(prompt)

        # 5. Handle LLM failures gracefully
        if not summary:
            summary = "No summary available."
        else:
            summary = summary.strip().replace("```", "")

        # 6. Store the result
        file_summaries.append({
            "file_path": file_path,
            "language": language,
            "summary": summary,
            "functions": function_names,
            "classes": classes,
            "imports_count": imports_count
        })

    return file_summaries
