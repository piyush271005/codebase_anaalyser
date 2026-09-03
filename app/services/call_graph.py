def build_function_call_graph(resolved_calls):

    nodes = {}
    edges = []

    for call in resolved_calls:

        caller = call.get("caller")
        callee = call.get("callee")

        if not caller or not callee:
            continue

        caller_id = f"{caller['file_path']}::{caller['name']}"
        callee_id = f"{callee['file_path']}::{callee['name']}"

        # Add caller node
        nodes[caller_id] = {
            "id": caller_id,
            "type": "function",
            "label": caller["name"],
            "file_path": caller["file_path"],
            "line": caller.get("line")
        }

        # Add callee node
        nodes[callee_id] = {
            "id": callee_id,
            "type": "function",
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