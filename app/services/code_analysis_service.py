from app.services.language_detector import detect_language
from app.services.ast_parser_service import parse_file
from app.services.function_extractor import extract_functions
from app.services.class_extractor import extract_classes
from app.services.import_extractor import extract_imports
from app.services.call_extractor import extract_function_calls


def analyze_file(file_path: str) -> dict | None:

    # Part 1
    language = detect_language(file_path)

    if language is None:
        return None

    # Part 2 + Part 3
    tree = parse_file(
        file_path,
        language
    )

    if tree is None:
        return None

    root_node = tree.root_node

    # Part 4
    functions = extract_functions(
        root_node,
        language
    )

    # Part 5
    classes = extract_classes(
        root_node,
        language
    )

    # Part 6
    imports = extract_imports(
        root_node,
        language
    )

    # Part 7
    calls = extract_function_calls(
        root_node,
        language
    )

    # Part 8
    return {
        "file_path": file_path,
        "language": language,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "calls": calls,
    }

def analyze_files(file_paths: list[str]) -> list[dict]:

    analysis_results = []

    for file_path in file_paths:

        result = analyze_file(file_path)

        if result is not None:
            analysis_results.append(result)

    return analysis_results