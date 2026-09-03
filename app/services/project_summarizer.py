from app.services.llm_client import call_llm


def summarize_project(
    repository_name: str,
    project_info: dict,
    module_summaries: list[dict],
    graph_response: dict
) -> dict:
    """
    Generate the top-level project summary using module summaries,
    project metadata, and relationship data from Feature 4.

    Returns a dictionary with:
      - summary (str)
      - main_technologies (list[str])
      - main_features (list[str])
    """

    # 1. Build the module context from Part 6
    module_context = "Modules in this project:\n"

    for module in module_summaries:
        name = module.get("name", "unknown")
        summary = module.get("summary", "No summary available.")
        files = module.get("files", [])
        file_count = len(files)

        module_context += f"- {name} ({file_count} files): {summary}\n"

    # 2. Build the project info context from Feature 2
    language = project_info.get("language", "Unknown")
    framework = project_info.get("framework", "Unknown")
    package_manager = project_info.get("package_manager", "Unknown")

    project_context = f"""Project metadata:
- Language: {language}
- Framework: {framework}
- Package manager: {package_manager}
"""

    # 3. Build the graph stats from Feature 4
    call_graph = graph_response.get("function_call_graph", {})
    dep_graph = graph_response.get("dependency_graph", {})

    call_nodes = len(call_graph.get("nodes", []))
    call_edges = len(call_graph.get("edges", []))
    dep_nodes = len(dep_graph.get("nodes", []))
    dep_edges = len(dep_graph.get("edges", []))

    graph_context = f"""Codebase statistics:
- Function call graph: {call_nodes} functions, {call_edges} calls
- Dependency graph: {dep_nodes} files, {dep_edges} import relationships
"""

    # 4. Build the prompt
    prompt = f"""You are an expert code analyst.
Based on the following information about a GitHub repository, generate:
1. A comprehensive 3-5 sentence project summary describing what this project does, its architecture, and its main purpose.
2. A list of main technologies used (programming languages, frameworks, libraries).
3. A list of main features/capabilities of this project.

Repository name: {repository_name}

{project_context}

{module_context}

{graph_context}

Return your response in EXACTLY this format (no markdown, no extra text):
SUMMARY: <your 3-5 sentence summary here>
TECHNOLOGIES: <comma-separated list>
FEATURES: <comma-separated list>"""

    # 5. Call the LLM (Part 2)
    print(f"Generating project summary for: {repository_name}...")
    response = call_llm(prompt)

    # 6. Parse the LLM response
    if not response:
        return {
            "summary": "No summary available.",
            "main_technologies": [],
            "main_features": []
        }

    # Parse the structured response
    summary = "No summary available."
    technologies = []
    features = []

    for line in response.strip().splitlines():

        line = line.strip()

        if line.startswith("SUMMARY:"):
            summary = line[len("SUMMARY:"):].strip()

        elif line.startswith("TECHNOLOGIES:"):
            tech_text = line[len("TECHNOLOGIES:"):].strip()
            technologies = [
                t.strip()
                for t in tech_text.split(",")
                if t.strip()
            ]

        elif line.startswith("FEATURES:"):
            feat_text = line[len("FEATURES:"):].strip()
            features = [
                f.strip()
                for f in feat_text.split(",")
                if f.strip()
            ]

    return {
        "summary": summary,
        "main_technologies": technologies,
        "main_features": features
    }
