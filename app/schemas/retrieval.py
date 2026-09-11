from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """
    The 5 core question types for Feature 7 Question Classification.
    """
    PROJECT_OVERVIEW = "PROJECT_OVERVIEW"
    ARCHITECTURE = "ARCHITECTURE"
    FUNCTION = "FUNCTION"
    FILE = "FILE"
    SEMANTIC_SEARCH = "SEMANTIC_SEARCH"


class ClassificationResult(BaseModel):
    """
    Structured output from the question classifier.
    """
    question_type: QuestionType = Field(description="The classified category of the question")
    target_name: str | None = Field(
        default=None,
        description="Target entity name if question_type is FUNCTION or FILE (e.g. 'loginUser', 'user.controller.js')"
    )
    reasoning: str | None = Field(
        default=None,
        description="Brief reasoning explaining why this category was chosen"
    )


class RetrievalRequest(BaseModel):
    """
    Incoming request to classify a question and retrieve targeted codebase context.
    """
    question: str = Field(description="The user's question about the repository")
    project_id: str = Field(description="The ID of the target indexed repository")
    top_k: int = Field(default=5, ge=1, le=20, description="Max chunks to retrieve if routed to SEMANTIC_SEARCH")
    provider: str | None = Field(default=None, description="Optional LLM provider name")
    model: str | None = Field(default=None, description="Optional model name override")
    api_key: str | None = Field(default=None, description="Optional API key override")


class RetrievalResponse(BaseModel):
    """
    Response model containing classification details and the retrieved context.
    """
    question: str
    project_id: str
    classification: ClassificationResult
    retrieval_strategy: str = Field(description="The name of the retrieval strategy used")
    context: dict[str, Any] = Field(description="The structured context gathered from Features 3-6")
