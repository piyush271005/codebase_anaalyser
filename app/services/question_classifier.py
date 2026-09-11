import json
import re

from app.schemas.retrieval import QuestionType, ClassificationResult
from app.prompts.classifier_prompt import build_classification_prompt
from app.services.llm_client import call_llm


def sanitize_target_name(target_name: str | None, question_type: QuestionType) -> str | None:
    """
    Part 5: Sanitizes and normalizes extracted target entity names.

    Rules:
      - Strips whitespace, quotes, and backticks.
      - Converts empty, 'null', 'none', 'n/a' strings to None.
      - For FUNCTION: Strips trailing parentheses (e.g. 'loginUser()' -> 'loginUser')
        and drops keywords like 'function', 'def', 'const'.
      - For FILE: Strips leading/trailing slashes and normalizes Windows backslashes.
    """
    if not target_name:
        return None

    cleaned = str(target_name).strip().strip("\"'`")

    if cleaned.lower() in ("null", "none", "n/a", "", "undefined"):
        return None

    if question_type == QuestionType.FUNCTION:
        # Strip trailing parentheses: e.g. loginUser() -> loginUser
        cleaned = re.sub(r"\(\s*\)$", "", cleaned).strip()
        # Strip common leading prefixes: e.g. "function loginUser" or "def loginUser"
        cleaned = re.sub(r"^(?:function|def|method|const|let|var)\s+", "", cleaned, flags=re.IGNORECASE).strip()
        # If it still contains non-identifier characters (like spaces), take the last valid token
        tokens = re.findall(r"[a-zA-Z_]\w*", cleaned)
        if tokens:
            cleaned = tokens[-1]

    elif question_type == QuestionType.FILE:
        # Normalize Windows backslashes to forward slashes
        cleaned = cleaned.replace("\\", "/")
        # Strip leading ./ or /
        cleaned = re.sub(r"^\.?/", "", cleaned)

    return cleaned if cleaned else None


def _extract_json(text: str) -> dict | None:
    """
    Extracts a JSON object from text, handling markdown fences or extra wrapper text.
    """
    if not text:
        return None

    cleaned = text.strip()

    # Remove markdown code blocks if the LLM included them
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Search for first { ... } block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def classify_question(
    question: str,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None
) -> ClassificationResult:
    """
    Classifies a user's question into one of the 5 QuestionType categories
    and extracts & sanitizes any target entity name.
    Raises exceptions directly on any failure without silent fallbacks.

    Args:
        question: The natural language question to classify.
        provider: Optional LLM provider name.
        model: Optional model identifier.
        api_key: Optional API key override.

    Returns:
        ClassificationResult object.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    prompt = build_classification_prompt(question)
    llm_output = call_llm(prompt, model=model, provider=provider, api_key=api_key)

    parsed_json = _extract_json(llm_output)

    if parsed_json and isinstance(parsed_json, dict):
        raw_type = parsed_json.get("question_type", "").strip().upper()
        raw_target = parsed_json.get("target_name")
        reasoning = parsed_json.get("reasoning", "Classified via LLM.")

        # Validate against QuestionType enum
        if raw_type in QuestionType.__members__:
            q_type = QuestionType(raw_type)
            # Part 5: Sanitize and clean the extracted target
            cleaned_target = sanitize_target_name(raw_target, q_type)

            return ClassificationResult(
                question_type=q_type,
                target_name=cleaned_target,
                reasoning=reasoning
            )

        raise RuntimeError(
            f"LLM Question classification returned unrecognized category '{raw_type}'. "
            f"Allowed categories: {[m.value for m in QuestionType]}"
        )

    raise RuntimeError(
        f"LLM Question classification failed to return valid JSON. Output received:\n{llm_output}"
    )
