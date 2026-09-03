from tree_sitter import Node


FUNCTION_NODE_TYPES = {
    "Python": {
        "function_definition",
    },

    "JavaScript": {
        "function_declaration",
        "function",
        "arrow_function",
    },

    "C++": {
        "function_definition",
    },

    "Java": {
        "method_declaration",
        "constructor_declaration",
    },
}

def extract_function_info(
    node: Node,
    language: str
) -> dict | None:

    name_node = node.child_by_field_name("name")

    # For arrow functions: const myFunc = () => {}
    # or wrapped: const myFunc = asynchandler(async () => {})
    # The name is on an ancestor variable_declarator
    if name_node is None and node.type == "arrow_function":
        ancestor = node.parent
        while ancestor is not None:
            if ancestor.type == "variable_declarator":
                name_node = ancestor.child_by_field_name("name")
                break
            ancestor = ancestor.parent

    if name_node is None:
        return None

    name = name_node.text.decode("utf-8")

    parameters_node = node.child_by_field_name("parameters")

    parameters = []

    if parameters_node is not None:

        for child in parameters_node.named_children:

            parameter_name = child.text.decode("utf-8")

            parameters.append(parameter_name)

    return {
    "name": name,
    "language": language,
    "parameters": parameters,
    "line": node.start_point[0] + 1,
    "end_line": node.end_point[0] + 1,
}


def extract_functions(
    root_node: Node,
    language: str
) -> list[dict]:

    function_types = FUNCTION_NODE_TYPES.get(language, set())

    functions = []

    def traverse(node: Node):

        if node.type in function_types:

            function_info = extract_function_info(node, language)

            if function_info:
                functions.append(function_info)

        for child in node.children:
            traverse(child)

    traverse(root_node)

    return functions