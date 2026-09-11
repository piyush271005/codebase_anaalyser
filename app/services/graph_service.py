from app.services.function_index import build_function_index
from app.services.function_resolver import resolve_function_calls
from app.services.call_graph import build_function_call_graph
from app.services.file_index import build_file_index
from app.services.import_resolver import resolve_imports
from app.services.dependency_graph import build_dependency_graph
from app.services.graph_serializer import build_graph_response


def generate_graphs(analysis_results: list[dict]) -> dict:
    """
    Orchestrator that runs Feature 4 Parts 1-7 in sequence.

    Input: analysis_results from Feature 3 (list of analyzed files)
    Output: Combined graph response with function_call_graph and dependency_graph
    """

    # --- Function Call Graph Side (Parts 1-3) ---

    # Part 1: Build Function Index
    function_index = build_function_index(analysis_results)

    # Part 2: Resolve Function Calls
    resolved_calls = resolve_function_calls(analysis_results, function_index)

    # Part 3: Build Function Call Graph
    call_graph = build_function_call_graph(resolved_calls, function_index)

    # --- Dependency Graph Side (Parts 4-6) ---

    # Part 4: Build File/Module Index
    file_index = build_file_index(analysis_results)

    # Part 5: Resolve Imports
    resolved_imports = resolve_imports(analysis_results, file_index)

    # Part 6: Build Dependency Graph
    dep_graph = build_dependency_graph(resolved_imports, analysis_results)

    # --- Part 7: Combine into Graph Response ---

    graph_response = build_graph_response(call_graph, dep_graph)

    return graph_response
