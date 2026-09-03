def build_dependency_graph(resolved_imports):

    nodes = {}
    edges = []

    for import_info in resolved_imports:

        source_file = import_info.get("source")
        target_file = import_info.get("target")

        if not source_file or not target_file:
            continue

        # Add source node
        nodes[source_file] = {
            "id": source_file,
            "type": "file",
            "label": source_file
        }

        # Add target node
        nodes[target_file] = {
            "id": target_file,
            "type": "file",
            "label": target_file
        }

        # Add dependency relationship
        edges.append({
            "source": source_file,
            "target": target_file,
            "type": "imports",
            "line": import_info.get("line")
        })

    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }