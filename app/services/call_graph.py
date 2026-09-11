def build_function_call_graph(resolved_calls: list[dict], function_index: dict | None = None) -> dict:
    """
    Builds the function call graph.
    If function_index is provided, pre-populates all indexed functions as nodes
    so that even isolated functions are visible in the visualization.
    """
    nodes = {}
    edges = []

    # 1. Pre-populate all repository functions from function_index
    if function_index:
        for func_name, candidates in function_index.items():
            for c in candidates:
                node_id = f"{c.get('file_path', 'unknown')}::{func_name}"
                nodes[node_id] = {
                    "id": node_id,
                    "type": "function",
                    "label": func_name,
                    "file_path": c.get("file_path", ""),
                    "line": c.get("line")
                }

    # 2. Add caller and callee nodes & edges from resolved_calls
    for call in resolved_calls:
        caller = call.get("caller")
        callee = call.get("callee")

        if not caller or not callee:
            continue

        caller_id = f"{caller['file_path']}::{caller['name']}"
        callee_id = f"{callee['file_path']}::{callee['name']}"

        # Add caller node if not already present
        if caller_id not in nodes:
            nodes[caller_id] = {
                "id": caller_id,
                "type": "function",
                "label": caller["name"],
                "file_path": caller["file_path"],
                "line": caller.get("line")
            }

        # Add callee node if not already present
        if callee_id not in nodes:
            nodes[callee_id] = {
                "id": callee_id,
                "type": "external" if callee.get("file_path") == "external" else "function",
                "label": callee["name"],
                "file_path": callee["file_path"],
                "line": callee.get("line")
            }

        # Add call relationship
        edges.append({
            "source": caller_id,
            "target": callee_id,
            "type": "calls",
            "line": call.get("call_line")
        })

    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }