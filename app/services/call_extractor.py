from tree_sitter import Node


CALL_NODE_TYPES = {
    "Python": {
        "call",
    },

    "JavaScript": {
        "call_expression",
    },

    "TypeScript": {
        "call_expression",
    },

    "C++": {
        "call_expression",
    },

    "Java": {
        "method_invocation",
    },
}

FUNCTION_NODE_TYPES = {
    "Python": {
        "function_definition",
    },

    "JavaScript": {
        "function_declaration",
        "function",
        "arrow_function",
    },

    "TypeScript": {
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


def extract_function_calls(
    root_node: Node,
    language: str
) -> list[dict]:

    call_types = CALL_NODE_TYPES.get(
        language,
        set()
    )

    function_types = FUNCTION_NODE_TYPES.get(
        language,
        set()
    )

    calls = []

    def traverse(
        node: Node,
        current_function: str | None = None
    ):

        if node.type in function_types:

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

            if name_node:
                current_function = (
                    name_node.text.decode("utf-8")
                )

        if node.type in call_types:

            function_node = node.child_by_field_name(
                "function"
            )

            if function_node:

                callee = function_node.text.decode(
                    "utf-8"
                )

                # For member expressions like "User.findById",
                # extract just the method name "findById"
                if "." in callee:
                    callee = callee.split(".")[-1]

                calls.append({
                    "language": language,
                    "caller": current_function,
                    "callee": callee,
                    "line": node.start_point[0] + 1,
                })

        for child in node.children:
            traverse(
                child,
                current_function
            )

    traverse(root_node)

    return calls