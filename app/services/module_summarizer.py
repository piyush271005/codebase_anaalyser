from pathlib import Path

from app.services.llm_client import call_llm


def summarize_modules(
    modules: list[dict],
    file_summaries: list[dict]
) -> list[dict]:
    """
    Generate a summary for each module by combining its
    file summaries and sending them to the LLM.

    Returns a list of modules with summaries attached.
    """

    module_summaries = []

    # Create a lookup dictionary for file summaries by file_path
    # Key: file_path, Value: the file summary dict
    file_lookup = {}
    for fs in file_summaries:
        file_lookup[fs["file_path"]] = fs

    for module in modules:

        module_name = module.get("name")
        module_path = module.get("path")
        module_files = module.get("files", [])

        if not module_name or not module_files:
            continue

        # 1. Collect the file summaries that belong to this module
        file_context = "Files in this module:\n"
        file_names = []

        for file_path in module_files:

            file_name = Path(file_path).name
            file_names.append(file_name)

            # Look up the pre-generated file summary (from Part 4)
            fs = file_lookup.get(file_path)

            if fs:
                file_summary = fs.get("summary", "No summary available.")
                functions = fs.get("functions", [])

                file_context += f"- {file_name}: {file_summary}\n"

                # Also include the function names for extra context
                if functions:
                    func_list = ", ".join(functions)
                    file_context += f"  Functions: {func_list}\n"
            else:
                file_context += f"- {file_name}: No summary available.\n"

        # 2. Build the prompt
        prompt = f"""You are an expert code analyst.
Summarize the purpose and responsibilities of this module/directory in 1-3 sentences.
A module is a group of related source files inside the same directory.

Module name: {module_name}
Directory path: {module_path}
Number of files: {len(module_files)}

{file_context}

Return ONLY the summary text, with no markdown formatting, no conversational filler, and no introduction."""

        # 3. Call the LLM (Part 2)
        print(f"Summarizing module: {module_name}...")
        summary = call_llm(prompt)

        # 4. Handle LLM failures gracefully
        if not summary:
            summary = "No summary available."
        else:
            summary = summary.strip().replace("```", "")

        # 5. Store the result
        module_summaries.append({
            "name": module_name,
            "path": module_path,
            "summary": summary,
            "files": file_names
        })

    return module_summaries
