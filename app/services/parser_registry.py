from tree_sitter import Language, Parser

import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_cpp
import tree_sitter_java


LANGUAGE_REGISTRY = {
    "Python": Language(tree_sitter_python.language()),
    "JavaScript": Language(tree_sitter_javascript.language()),
    "C++": Language(tree_sitter_cpp.language()),
    "Java": Language(tree_sitter_java.language()),
}


def get_parser(language_name: str) -> Parser | None:
    """
    Return a Tree-sitter parser configured
    for the requested programming language.
    """

    language = LANGUAGE_REGISTRY.get(language_name)

    if language is None:
        return None

    parser = Parser()
    parser.language = language

    return parser