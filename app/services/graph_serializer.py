def build_graph_response(call_graph, dependency_graph):

    return {
        "function_call_graph": call_graph,
        "dependency_graph": dependency_graph
    }