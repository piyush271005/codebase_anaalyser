from tree_sitter import Node


IMPORT_NODE_TYPES = {
    "Python": {
        "import_statement",
        "import_from_statement",
    },

    "JavaScript": {
        "import_statement",
    },

    "TypeScript": {
        "import_statement",
    },

    "Java": {
        "import_declaration",
    },

    "C++": {
        "preproc_include",
    },
}

def extract_import_info(
    node: Node,
    language: str
) -> dict:

    module = None

    # JavaScript/TypeScript: import { x } from "module-path"
    # The "source" field contains the string literal
    if language in ("JavaScript", "TypeScript"):
        source_node = node.child_by_field_name("source")
        if source_node:
            module = source_node.text.decode("utf-8").strip("\"'")

    # Python: from module import name / import module
    elif language == "Python":
        if node.type == "import_from_statement":
            # from services.auth import login
            module_node = node.child_by_field_name("module_name")
            if module_node:
                module = module_node.text.decode("utf-8")
        else:
            # import os
            for child in node.named_children:
                if child.type == "dotted_name":
                    module = child.text.decode("utf-8")
                    break

    # Java: import com.example.MyClass;
    elif language == "Java":
        for child in node.named_children:
            if child.type == "scoped_identifier":
                module = child.text.decode("utf-8")
                break

    # C++: #include <header.h> or #include "header.h"
    elif language == "C++":
        for child in node.named_children:
            if child.type in ("string_literal", "system_lib_string"):
                module = child.text.decode("utf-8").strip("\"'<>")
                break

    # Fallback: use full text
    if not module:
        module = node.text.decode("utf-8")

    return {
        "language": language,
        "module": module,
        "line": node.start_point[0] + 1,
    }


def extract_imports(
    root_node: Node,
    language: str
) -> list[dict]:

    import_types = IMPORT_NODE_TYPES.get(
        language,
        set()
    )

    imports = []

    def traverse(node: Node):

        if node.type in import_types:

            import_info = extract_import_info(
                node,
                language
            )

            if import_info:
                imports.append(import_info)

        for child in node.children:
            traverse(child)

    traverse(root_node)

    return imports