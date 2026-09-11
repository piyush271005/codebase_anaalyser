from typing import Any


def format_project_overview_context(context: dict[str, Any]) -> str:
    """
    Formats PROJECT_OVERVIEW context into LLM-readable text.
    """
    lines = []
    lines.append("===== PROJECT OVERVIEW =====")
    lines.append(f"Language: {context.get('language', 'Unknown')}")
    lines.append(f"Framework: {context.get('framework', 'Unknown')}")
    lines.append(f"Package Manager: {context.get('package_manager', 'Unknown')}")
    lines.append(f"Total Source Files: {context.get('total_source_files', 0)}")

    modules = context.get("modules", [])
    if modules:
        lines.append(f"\nModules ({len(modules)}):")
        for m in modules:
            lines.append(f"  - {m.get('name', 'unknown')} ({m.get('path', '')}) — {m.get('file_count', 0)} files")

    return "\n".join(lines)


def format_architecture_context(context: dict[str, Any]) -> str:
    """
    Formats ARCHITECTURE context into LLM-readable text.
    """
    lines = []
    lines.append("===== ARCHITECTURE =====")

    modules = context.get("modules", [])
    if modules:
        lines.append(f"\nModules ({len(modules)}):")
        for m in modules:
            lines.append(f"  - {m.get('name', 'unknown')} ({m.get('path', '')}) — {m.get('file_count', 0)} files")

    lines.append(f"\nTotal File Dependencies: {context.get('total_dependencies', 0)}")
    lines.append(f"Total Function Calls: {context.get('total_function_calls', 0)}")

    deps = context.get("key_dependencies", [])
    if deps:
        lines.append(f"\nKey Dependencies ({len(deps)}):")
        for dep in deps:
            lines.append(f"  {dep.get('from', '?')} → {dep.get('to', '?')}")

    return "\n".join(lines)


def format_function_context(context: dict[str, Any]) -> str:
    """
    Formats FUNCTION context into LLM-readable text.
    """
    lines = []
    target = context.get("target_function", "unknown")

    if not context.get("found", False):
        lines.append(f"===== FUNCTION: {target} =====")
        lines.append(f"Status: NOT FOUND")
        lines.append(context.get("message", "Function was not found in the codebase."))
        return "\n".join(lines)

    functions = context.get("functions", [])
    for i, func in enumerate(functions):
        lines.append(f"===== FUNCTION: {func.get('name', target)} =====")
        lines.append(f"File: {func.get('file_path', 'unknown')}")
        lines.append(f"Language: {func.get('language', 'Code')}")
        lines.append(f"Lines: {func.get('line', '?')} - {func.get('end_line', '?')}")

        params = func.get("parameters", [])
        if params:
            lines.append(f"Parameters: {', '.join(params)}")

        code = func.get("code", "")
        if code:
            lines.append(f"\nCode:\n{code}")

        if i < len(functions) - 1:
            lines.append("\n" + "-" * 40)

    return "\n".join(lines)


def format_file_context(context: dict[str, Any]) -> str:
    """
    Formats FILE context into LLM-readable text.
    """
    lines = []
    target = context.get("target_file", "unknown")

    if not context.get("found", False):
        lines.append(f"===== FILE: {target} =====")
        lines.append(f"Status: NOT FOUND")
        lines.append(context.get("message", "File was not found in the codebase."))
        return "\n".join(lines)

    lines.append(f"===== FILE: {context.get('file_path', target)} =====")
    lines.append(f"Language: {context.get('language', 'Code')}")

    functions = context.get("functions", [])
    if functions:
        lines.append(f"\nFunctions ({len(functions)}):")
        for f in functions:
            lines.append(f"  - {f}")

    classes = context.get("classes", [])
    if classes:
        lines.append(f"\nClasses ({len(classes)}):")
        for c in classes:
            lines.append(f"  - {c}")

    imports = context.get("imports", [])
    if imports:
        lines.append(f"\nImports ({len(imports)}):")
        for imp in imports:
            lines.append(f"  - {imp}")

    code = context.get("code", "")
    if code:
        lines.append(f"\nFull Source Code:\n{code}")

    return "\n".join(lines)


def format_semantic_search_context(context: dict[str, Any]) -> str:
    """
    Formats SEMANTIC_SEARCH context into LLM-readable text.
    """
    lines = []
    total = context.get("total_results", 0)
    lines.append(f"===== SEMANTIC SEARCH RESULTS ({total} chunks) =====")

    chunks = context.get("chunks", [])
    if not chunks:
        lines.append("No relevant code chunks were found for this query.")
        return "\n".join(lines)

    for i, chunk in enumerate(chunks, 1):
        lines.append(f"\n--- Chunk {i}/{len(chunks)} (Score: {chunk.get('score', '?')}) ---")
        lines.append(f"Name: {chunk.get('name', 'unknown')}")
        lines.append(f"Type: {chunk.get('chunk_type', 'unknown')}")
        lines.append(f"File: {chunk.get('file_path', 'unknown')}")
        lines.append(f"Lines: {chunk.get('line', '?')} - {chunk.get('end_line', '?')}")

        code = chunk.get("code", "")
        if code:
            lines.append(f"\nCode:\n{code}")

    return "\n".join(lines)


def format_context(question_type: str, context: dict[str, Any]) -> str:
    """
    Master dispatcher: routes the context to the correct formatter based on question type.
    """
    formatters = {
        "PROJECT_OVERVIEW": format_project_overview_context,
        "ARCHITECTURE": format_architecture_context,
        "FUNCTION": format_function_context,
        "FILE": format_file_context,
        "SEMANTIC_SEARCH": format_semantic_search_context,
    }

    formatter = formatters.get(question_type, format_semantic_search_context)
    return formatter(context)
