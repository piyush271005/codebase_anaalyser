from fastapi import APIRouter

from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services.question_classifier import classify_question
from app.services.context_retriever import retrieve_context

router = APIRouter()


@router.post(
    "/retrieve-context",
    response_model=RetrievalResponse,
    summary="Classify question and retrieve targeted codebase context (Feature 7)",
    description="Analyzes user's question, classifies it into one of 5 categories, extracts any target function/file, and retrieves optimal context across Features 3-6."
)
def retrieve_codebase_context(request: RetrievalRequest):
    """
    Endpoint for Feature 7 Question Classification and Intelligent Retrieval.

    Execution Pipeline:
      1. Classify the question and extract target entity (Parts 3, 4, 5).
      2. Route the classification to the specialized retrieval strategy (Parts 6, 7).
      3. Package and return the structured context response.
    """
    # 1. Classify question and extract target (raises on error)
    classification = classify_question(
        request.question,
        provider=request.provider,
        model=request.model,
        api_key=request.api_key
    )

    # 2. Retrieve targeted context based on classification
    strategy_name, context = retrieve_context(
        classification=classification,
        project_id=request.project_id,
        top_k=request.top_k,
        question=request.question
    )

    # 3. Assemble response
    return {
        "question": request.question,
        "project_id": request.project_id,
        "classification": classification,
        "retrieval_strategy": strategy_name,
        "context": context
    }
