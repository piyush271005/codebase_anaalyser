from app.services.code_reader import read_function_code
from app.services.llm_client import call_llm


def summarize_functions(analysis_results: list[dict]) -> list[dict]:
    """
    For each function in analysis_results, read its actual code and
    generate an LLM summary.

    Returns a list of dictionaries with function details and the summary.
    """
    function_summaries = []

    for file_result in analysis_results:
        file_path = file_result.get("file_path")
        language = file_result.get("language", "Code")
        functions = file_result.get("functions", [])

        if not file_path or not functions:
            continue

        for func in functions:
            name = func.get("name")
            line = func.get("line")
            end_line = func.get("end_line")
            parameters = func.get("parameters", [])

            if not name or not line or not end_line:
                continue

            # 1. Read the actual function code (Part 1)
            code = read_function_code(file_path, line, end_line)

            if not code:
                continue

            # 2. Truncate if the function is massively long to save LLM tokens
            code_lines = code.splitlines()
            if len(code_lines) > 200:
                # Keep first 100 and last 50 lines
                truncated_code = (
                    "\n".join(code_lines[:100]) +
                    "\n\n... [CODE TRUNCATED] ...\n\n" +
                    "\n".join(code_lines[-50:])
                )
                code = truncated_code

            # 3. Build the prompt
            prompt = f"""You are an expert code analyst.
Analyze the following {language} function and provide a concise 1-2 sentence summary of its purpose and behavior.
Focus on what it does, its inputs, and its outcomes.

Function: {name}
File: {file_path}

Code:
```{language}
{code}
```

Return ONLY the summary text, with no markdown formatting, no conversational filler, and no introduction."""

            # 4. Call the LLM (Part 2)
            print(f"Summarizing function: {name} in {file_path.split('/')[-1]}...")
            summary = call_llm(prompt)

            # 5. Handle LLM failures
            if not summary:
                summary = "No summary available."
            else:
                # Clean up any accidental markdown or whitespace the LLM might return
                summary = summary.strip().replace("```", "")

            # 6. Store the result
            function_summaries.append({
                "name": name,
                "file_path": file_path,
                "line": line,
                "end_line": end_line,
                "parameters": parameters,
                "summary": summary
            })

    return function_summaries
