import re
from app.services.llm_client import call_llm

BATCH_SIZE = 10


def _parse_batch_response(response: str, expected_count: int) -> list[str]:
    """
    Parse a numbered response like:
        [1] Summary text here
        [2] Another summary
    Returns a list of summary strings in order.
    """
    summaries = {}
    pattern = re.compile(r"^\[(\d+)\]\s*(.+)", re.MULTILINE)
    for match in pattern.finditer(response):
        idx = int(match.group(1))
        text = match.group(2).strip().replace("```", "")
        summaries[idx] = text

    result = []
    for i in range(1, expected_count + 1):
        if i not in summaries or not summaries[i]:
            raise RuntimeError(
                f"LLM batch response missing summary for file [{i}]. "
                f"Got {len(summaries)} summaries, expected {expected_count}."
            )
        result.append(summaries[i])

    return result


def summarize_files(
    analysis_results: list[dict],
    function_summaries: list[dict],
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None
) -> list[dict]:
    """
    Generate a summary for each source file using batched LLM requests.
    Combines function summaries, class info, and imports for context.

    Returns a list of dictionaries with file metadata and the summary.
    """

    # Create a quick lookup dictionary for function summaries by file_path
    func_lookup = {}
    for fs in function_summaries:
        fp = fs["file_path"]
        if fp not in func_lookup:
            func_lookup[fp] = []
        func_lookup[fp].append(fs)

    # 1. Collect all files with their context
    all_files = []

    for file_result in analysis_results:
        file_path = file_result.get("file_path")
        language = file_result.get("language", "Code")

        if not file_path:
            continue

        classes = [c.get("name") for c in file_result.get("classes", []) if c.get("name")]
        imports_count = len(file_result.get("imports", []))
        file_funcs = func_lookup.get(file_path, [])
        function_names = [f["name"] for f in file_funcs]

        # Build context strings for this file
        function_context = ""
        if file_funcs:
            function_context = "Functions:\n"
            for f in file_funcs:
                function_context += f"  - {f['name']}: {f['summary']}\n"
        else:
            function_context = "No functions defined.\n"

        class_context = ""
        if classes:
            class_context = f"Classes: {', '.join(classes)}\n"

        all_files.append({
            "file_path": file_path,
            "language": language,
            "classes": classes,
            "imports_count": imports_count,
            "function_names": function_names,
            "function_context": function_context,
            "class_context": class_context,
        })

    if not all_files:
        return []

    # 2. Process in batches
    file_summaries = []
    total_batches = (len(all_files) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(all_files), BATCH_SIZE):
        batch = all_files[batch_idx : batch_idx + BATCH_SIZE]
        batch_num = (batch_idx // BATCH_SIZE) + 1
        count = len(batch)

        print(f"Summarizing files batch {batch_num}/{total_batches} ({count} files) using {provider or 'default'}...")

        # 3. Build the batch prompt
        prompt = f"""You are an expert code analyst.
Summarize the overall purpose and responsibilities of each of the following {count} source files in 1-3 sentences.
Base your summary on the provided metadata and function descriptions.

Return your response in EXACTLY this format, one line per file:
[1] <summary for file 1>
[2] <summary for file 2>
... and so on up to [{count}]

Return ONLY the numbered summaries, with no markdown formatting, no extra text.

"""
        for i, f in enumerate(batch, start=1):
            prompt += f"""=== File {i}: {f['file_path']} ===
Language: {f['language']}
Imports: {f['imports_count']}
{f['class_context']}{f['function_context']}
"""

        # 4. Call the LLM
        batch_max_tokens = max(500, count * 120)
        response = call_llm(
            prompt,
            model=model,
            provider=provider,
            api_key=api_key,
            max_tokens=batch_max_tokens
        )

        if not response or not response.strip():
            raise RuntimeError(
                f"LLM returned empty response for file batch {batch_num}/{total_batches}."
            )

        # 5. Parse the batch response
        summaries = _parse_batch_response(response, count)

        # 6. Map summaries back to files
        for f, summary in zip(batch, summaries):
            file_summaries.append({
                "file_path": f["file_path"],
                "language": f["language"],
                "summary": summary,
                "functions": f["function_names"],
                "classes": f["classes"],
                "imports_count": f["imports_count"],
            })

    return file_summaries
