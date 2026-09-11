import re
from pathlib import Path

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
                f"LLM batch response missing summary for module [{i}]. "
                f"Got {len(summaries)} summaries, expected {expected_count}."
            )
        result.append(summaries[i])

    return result


def summarize_modules(
    modules: list[dict],
    file_summaries: list[dict],
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None
) -> list[dict]:
    """
    Generate a summary for each module using batched LLM requests.
    Combines file summaries for context.

    Returns a list of modules with summaries attached.
    """

    # Create a lookup dictionary for file summaries by file_path
    file_lookup = {}
    for fs in file_summaries:
        file_lookup[fs["file_path"]] = fs

    # 1. Collect all modules with their context
    all_modules = []

    for module in modules:
        module_name = module.get("name")
        module_path = module.get("path")
        module_files = module.get("files", [])

        if not module_name or not module_files:
            continue

        # Build file context for this module
        file_context = "Files:\n"
        file_names = []

        for file_path in module_files:
            file_name = Path(file_path).name
            file_names.append(file_name)

            fs = file_lookup.get(file_path)
            if fs:
                file_summary = fs.get("summary", "No summary available.")
                functions = fs.get("functions", [])
                file_context += f"  - {file_name}: {file_summary}\n"
                if functions:
                    file_context += f"    Functions: {', '.join(functions)}\n"
            else:
                file_context += f"  - {file_name}: No summary available.\n"

        all_modules.append({
            "name": module_name,
            "path": module_path,
            "files": module_files,
            "file_names": file_names,
            "file_context": file_context,
        })

    if not all_modules:
        return []

    # 2. Process in batches
    module_summaries = []
    total_batches = (len(all_modules) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(all_modules), BATCH_SIZE):
        batch = all_modules[batch_idx : batch_idx + BATCH_SIZE]
        batch_num = (batch_idx // BATCH_SIZE) + 1
        count = len(batch)

        print(f"Summarizing modules batch {batch_num}/{total_batches} ({count} modules) using {provider or 'default'}...")

        # 3. Build the batch prompt
        prompt = f"""You are an expert code analyst.
Summarize the purpose and responsibilities of each of the following {count} modules/directories in 1-3 sentences.
A module is a group of related source files inside the same directory.

Return your response in EXACTLY this format, one line per module:
[1] <summary for module 1>
[2] <summary for module 2>
... and so on up to [{count}]

Return ONLY the numbered summaries, with no markdown formatting, no extra text.

"""
        for i, m in enumerate(batch, start=1):
            prompt += f"""=== Module {i}: {m['name']} (path: {m['path']}, {len(m['files'])} files) ===
{m['file_context']}
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
                f"LLM returned empty response for module batch {batch_num}/{total_batches}."
            )

        # 5. Parse the batch response
        summaries = _parse_batch_response(response, count)

        # 6. Map summaries back to modules
        for m, summary in zip(batch, summaries):
            module_summaries.append({
                "name": m["name"],
                "path": m["path"],
                "summary": summary,
                "files": m["file_names"],
            })

    return module_summaries
