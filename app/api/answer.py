from fastapi import APIRouter

from app.schemas.answer import AskRequest, AskResponse
from app.services.answer_service import generate_answer

router = APIRouter()


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="AI-Powered Question Answering (Feature 8)",
    description="Analyzes the repository context retrieved across Features 3-7 and generates an accurate, grounded technical answer with source citations."
)
def ask_codebase(request: AskRequest):
    """
    Main entry point for AI-Powered Question Answering.

    Execution Pipeline:
      1. Receive user question and project_id (Feature 8 Part 1 & 2)
      2. Classify question and extract target (Feature 7 Parts 4 & 5)
      3. Retrieve targeted repository context (Feature 7 Parts 6 & 7)
      4. Early anti-hallucination check (Feature 8 Part 7)
      5. Extract structured source references (Feature 8 Part 7)
      6. Format context into clean text blocks (Feature 8 Part 4)
      7. Build 4-tier grounded prompt (Feature 8 Part 5)
      8. Call LLM to generate answer (Feature 8 Part 6)
      9. Return structured response matching AskResponse schema
    """
    result = generate_answer(
        question=request.question,
        project_id=request.project_id,
        top_k=request.top_k,
        provider=request.provider,
        model=request.model,
        api_key=request.api_key
    )
    return result
