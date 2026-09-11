from pathlib import Path
from typing import Any

from app.schemas.answer import AnswerSource
from app.services.question_classifier import classify_question
from app.services.context_retriever import retrieve_context
from app.services.context_formatter import format_context
from app.prompts.answer_prompts import build_answer_prompt
from app.services.llm_client import call_llm


def extract_sources(
    question_type: str,
    context_data: dict[str, Any]
) -> list[AnswerSource]:
    """
    Part 7: Extracts structured AnswerSource objects from the retrieved context.
    """
    sources: list[AnswerSource] = []

    if question_type == "FUNCTION":
        if context_data.get("found", False):
            for f in context_data.get("functions", []):
                sources.append(AnswerSource(
                    file_path=f.get("file_path", ""),
                    name=f.get("name"),
                    chunk_type="function",
                    line=f.get("line"),
                    end_line=f.get("end_line")
                ))

    elif question_type == "FILE":
        if context_data.get("found", False):
            fpath = context_data.get("file_path", "")
            fname = Path(fpath).name if fpath else "file"
            sources.append(AnswerSource(
                file_path=fpath,
                name=fname,
                chunk_type="file",
                line=1,
                end_line=None
            ))

    elif question_type == "SEMANTIC_SEARCH":
        for chunk in context_data.get("chunks", []):
            sources.append(AnswerSource(
                file_path=chunk.get("file_path", ""),
                name=chunk.get("name"),
                chunk_type=chunk.get("chunk_type", "code"),
                line=chunk.get("line"),
                end_line=chunk.get("end_line")
            ))

    elif question_type == "ARCHITECTURE":
        seen_files = set()
        for dep in context_data.get("key_dependencies", []):
            for path in [dep.get("from"), dep.get("to")]:
                if path and path not in seen_files:
                    seen_files.add(path)
                    sources.append(AnswerSource(
                        file_path=path,
                        name=Path(path).name,
                        chunk_type="file"
                    ))

    elif question_type == "PROJECT_OVERVIEW":
        for mod in context_data.get("modules", []):
            sources.append(AnswerSource(
                file_path=mod.get("path", ""),
                name=mod.get("name"),
                chunk_type="module"
            ))

    return sources


def check_insufficient_context(
    question_type: str,
    context_data: dict[str, Any]
) -> tuple[bool, str]:
    """
    Part 7: Evaluates whether the retrieved context is provably insufficient
    or if an error occurred, preventing hallucinated LLM responses.

    Returns:
        tuple of (is_insufficient: bool, message: str)
    """
    if "error" in context_data:
        return True, f"Based on the available repository context, I cannot answer: {context_data['error']}"

    if question_type == "FUNCTION":
        if not context_data.get("found", False):
            target = context_data.get("target_function", "the requested function")
            return True, f"Based on the available repository context, I don't have enough information to answer: '{target}' was not found in the codebase AST."

    elif question_type == "FILE":
        if not context_data.get("found", False):
            target = context_data.get("target_file", "the requested file")
            return True, f"Based on the available repository context, I don't have enough information to answer: '{target}' was not found in the codebase."

    elif question_type == "SEMANTIC_SEARCH":
        chunks = context_data.get("chunks", [])
        if not chunks:
            return True, "Based on the available repository context, I don't have enough information to answer this question. No matching code chunks were found."

    return False, ""



def generate_answer(
    question: str,
    project_id: str,
    top_k: int = 5,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None
) -> dict[str, Any]:
    """
    Feature 8 Answer Generation Service.

    Execution Pipeline:
      1. Classify the question and extract target entity (Feature 7)
      2. Retrieve targeted repository context (Feature 7)
      3. Handle insufficient context early (Part 7)
      4. Extract structured sources (Part 7)
      5. Format context into clean, structured text (Part 4)
      6. Build 4-tier grounded prompt (Part 5)
      7. Invoke configured LLM via call_llm
      8. Return structured result conforming to AskResponse schema
    """
    # 1. Classify question (raises on error without fallback)
    classification = classify_question(
        question,
        provider=provider,
        model=model,
        api_key=api_key
    )
    q_type_str = classification.question_type.value

    # 2. Retrieve targeted context
    strategy_name, context_data = retrieve_context(
        classification=classification,
        project_id=project_id,
        top_k=top_k,
        question=question
    )

    # 3. Check for insufficient context early (prevents hallucinations and wasted LLM calls)
    is_insufficient, insufficient_msg = check_insufficient_context(q_type_str, context_data)
    if is_insufficient:
        print(f"[AnswerService] Insufficient context detected for '{question}'. Returning safe notice.")
        return {
            "question": question,
            "project_id": project_id,
            "question_type": q_type_str,
            "retrieval_strategy": strategy_name,
            "answer": insufficient_msg,
            "sources": [],
            "provider": provider,
            "model": model
        }

    # 4. Extract structured sources
    sources = extract_sources(q_type_str, context_data)

    # 5. Format context
    formatted_context = format_context(q_type_str, context_data)

    # 6. Build prompt
    prompt = build_answer_prompt(
        question=question,
        question_type=q_type_str,
        formatted_context=formatted_context
    )

    # 7. Call LLM
    active_provider = provider or "default"
    print(f"[AnswerService] Calling LLM (Provider: {active_provider}, Model: {model or 'default'}) for question: '{question}' (Type: {q_type_str})...")
    llm_answer = call_llm(prompt, model=model, provider=provider, api_key=api_key)

    if not llm_answer or not llm_answer.strip():
        raise RuntimeError(f"LLM returned an empty answer from provider '{active_provider}'.")

    return {
        "question": question,
        "project_id": project_id,
        "question_type": q_type_str,
        "retrieval_strategy": strategy_name,
        "answer": llm_answer.strip(),
        "sources": sources,
        "provider": provider,
        "model": model
    }
