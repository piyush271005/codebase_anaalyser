from app.services.function_summarizer import summarize_functions
from app.services.file_summarizer import summarize_files
from app.services.module_detector import detect_modules
from app.services.module_summarizer import summarize_modules
from app.services.project_summarizer import summarize_project


def generate_understanding(
    repository_name: str,
    clone_path: str,
    project_info: dict,
    analysis_results: list[dict],
    graph_response: dict
) -> dict:
    """
    Orchestrator for Feature 5: AI-Powered Repository Understanding.
    Runs hierarchical summarization from functions to project level.

    Steps:
      1. Summarize all functions (Part 3)
      2. Summarize all files using function summaries (Part 4)
      3. Group files into modules based on directories (Part 5)
      4. Summarize all modules using file summaries (Part 6)
      5. Summarize the overall project using module summaries, metadata, and graph stats (Part 7)
      6. Assemble and return the complete repository understanding context.
    """

    # Level 1: Function-level understanding
    print("--- [Feature 5] Step 1/5: Summarizing functions... ---")
    function_summaries = summarize_functions(analysis_results)

    # Level 2: File-level understanding
    print("--- [Feature 5] Step 2/5: Summarizing files... ---")
    file_summaries = summarize_files(analysis_results, function_summaries)

    # Grouping: Directory-based module detection
    print("--- [Feature 5] Step 3/5: Detecting modules... ---")
    modules = detect_modules(analysis_results, clone_path)

    # Level 3: Module-level understanding
    print("--- [Feature 5] Step 4/5: Summarizing modules... ---")
    module_summaries = summarize_modules(modules, file_summaries)

    # Level 4: Project-level understanding
    print("--- [Feature 5] Step 5/5: Summarizing project... ---")
    project_summary = summarize_project(
        repository_name=repository_name,
        project_info=project_info,
        module_summaries=module_summaries,
        graph_response=graph_response
    )

    # Assemble the final repository context
    return {
        "repository_name": repository_name,
        "project_summary": project_summary,
        "modules": module_summaries,
        "file_summaries": file_summaries,
        "function_summaries": function_summaries
    }
