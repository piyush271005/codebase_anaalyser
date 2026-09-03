from pathlib import Path

from tree_sitter import Tree

from app.services.parser_registry import get_parser


def parse_file(file_path: str, language: str) -> Tree | None:
    """
    Read a source file and generate its Tree-sitter syntax tree.
    """

    parser = get_parser(language)

    if parser is None:
        return None

    source_code = Path(file_path).read_bytes()

    tree = parser.parse(source_code)

    return tree