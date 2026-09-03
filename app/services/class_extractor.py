from tree_sitter import Node


CLASS_NODE_TYPES = {
    "Python": {
        "class_definition",
    },

    "JavaScript": {
        "class_declaration",
    },

    "TypeScript": {
        "class_declaration",
    },

    "C++": {
        "class_specifier",
        "struct_specifier",
    },

    "Java": {
        "class_declaration",
    },
}

def extract_methods(
    class_node: Node,
    language: str
) -> list[str]:

    methods = []

    for node in class_node.named_children:

        if node.type in {
            "function_definition",
            "method_declaration"
        }:

            name_node = node.child_by_field_name("name")

            if name_node:

                name = name_node.text.decode("utf-8")

                methods.append(name)

    return methods

def extract_class_info(
    node: Node,
    language: str
) -> dict | None:

    name_node = node.child_by_field_name("name")

    if name_node is None:
        return None

    name = name_node.text.decode("utf-8")

    methods = extract_methods(
        node,
        language
    )

    return {
        "name": name,
        "language": language,
        "line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "methods": methods,
    }

def extract_classes(
    root_node: Node,
    language: str
) -> list[dict]:

    class_types = CLASS_NODE_TYPES.get(language, set())

    classes = []

    def traverse(node: Node):

        if node.type in class_types:

            class_info = extract_class_info(
                node,
                language
            )

            if class_info:
                classes.append(class_info)

        for child in node.children:
            traverse(child)

    traverse(root_node)

    return classes