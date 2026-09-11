import re
from app.services.code_reader import read_function_code
from app.services.llm_client import call_llm

BATCH_SIZE = 10


def _truncate_code(code: str, max_first: int = 60, max_last: int = 30) -> str:
    """Truncate long function code to save LLM tokens in batch prompts."""
    code_lines = code.splitlines()
    if len(code_lines) > (max_first + max_last):
        return (
            "\n".join(code_lines[:max_first])
            + "\n\n... [CODE TRUNCATED] ...\n\n"
            + "\n".join(code_lines[-max_last:])
        )
    return code


def _parse_batch_response(response: str, expected_count: int) -> list[str]:
    """
    Parse a numbered response like:
        [1] Summary text here
        [2] Another summary
    Returns a list of summary strings in order.
    """
    summaries = {}
    # Match lines starting with [N] where N is a number
    pattern = re.compile(r"^\[(\d+)\]\s*(.+)", re.MULTILINE)
    for match in pattern.finditer(response):
        idx = int(match.group(1))
        text = match.group(2).strip().replace("```", "")
        summaries[idx] = text

    result = []
    for i in range(1, expected_count + 1):
        if i not in summaries or not summaries[i]:
            raise RuntimeError(
                f"LLM batch response missing summary for item [{i}]. "
                f"Got {len(summaries)} summaries, expected {expected_count}."
            )
        result.append(summaries[i])

    return result


def summarize_functions(
    analysis_results: list[dict],
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None
) -> list[dict]:
    """
    For each function in analysis_results, read its actual code and
    generate an LLM summary using batched requests (BATCH_SIZE functions per call).

    Returns a list of dictionaries with function details and the summary.
    """

    # 1. Collect all functions with their code into a flat list
    all_functions = []

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

            code = read_function_code(file_path, line, end_line)
            if not code:
                continue

            # Truncate for batch prompts (more aggressive than single-call)
            code = _truncate_code(code)

            all_functions.append({
                "name": name,
                "file_path": file_path,
                "language": language,
                "line": line,
                "end_line": end_line,
                "parameters": parameters,
                "code": code,
            })

    if not all_functions:
        return []

    # 2. Process in batches
    function_summaries = []
    total_batches = (len(all_functions) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(all_functions), BATCH_SIZE):
        batch = all_functions[batch_idx : batch_idx + BATCH_SIZE]
        batch_num = (batch_idx // BATCH_SIZE) + 1
        count = len(batch)

        print(f"Summarizing functions batch {batch_num}/{total_batches} ({count} functions) using {provider or 'default'}...")

        # 3. Build the batch prompt
        prompt = f"""You are an expert code analyst.
Analyze the following {count} functions and provide a concise 1-2 sentence summary for each.
Focus on what each function does, its inputs, and its outcomes.

Return your response in EXACTLY this format, one line per function:
[1] <summary for function 1>
[2] <summary for function 2>
... and so on up to [{count}]

Return ONLY the numbered summaries, with no markdown formatting, no extra text.

"""
        for i, func in enumerate(batch, start=1):
            prompt += f"""=== Function {i}: {func['name']} ({func['file_path']}) ===
```{func['language']}
{func['code']}
```

"""

        # 4. Call the LLM with higher max_tokens for batch response
        # Each summary is ~30-50 tokens, so N*60 tokens + buffer
        batch_max_tokens = max(500, count * 100)
        response = call_llm(
            prompt,
            model=model,
            provider=provider,
            api_key=api_key,
            max_tokens=batch_max_tokens
        )

        if not response or not response.strip():
            raise RuntimeError(
                f"LLM returned empty response for function batch {batch_num}/{total_batches}."
            )

        # 5. Parse the batch response
        summaries = _parse_batch_response(response, count)

        # 6. Map summaries back to functions
        for func, summary in zip(batch, summaries):
            function_summaries.append({
                "name": func["name"],
                "file_path": func["file_path"],
                "line": func["line"],
                "end_line": func["end_line"],
                "parameters": func["parameters"],
                "summary": summary,
            })

    return function_summaries
