from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """
    Incoming request to ask a question about an indexed repository.

    Data Flow:
      AskRequest → Feature 7 (classify + retrieve) → Feature 8 (format + prompt + LLM) → AskResponse
    """
    question: str = Field(description="The user's natural language question about the repository")
    project_id: str = Field(description="The ID of the target indexed repository")
    top_k: int = Field(default=5, ge=1, le=20, description="Max code chunks to retrieve if routed to SEMANTIC_SEARCH")
    provider: str | None = Field(default=None, description="LLM provider: groq, gemini, openai, ollama")
    model: str | None = Field(default=None, description="Optional model name override")
    api_key: str | None = Field(default=None, description="Optional user-provided API key from frontend")


class AnswerSource(BaseModel):
    """
    Tracks the origin of information used to generate the answer.
    """
    file_path: str = Field(description="Relative path of the source file")
    name: str | None = Field(default=None, description="Function, class, or module name if applicable")
    chunk_type: str | None = Field(default=None, description="Type: function, class, file, top-level")
    line: int | None = Field(default=None, description="Start line number in the source file")
    end_line: int | None = Field(default=None, description="End line number in the source file")


class AskResponse(BaseModel):
    """
    Structured response containing the LLM-generated answer, classification metadata, and source references.

    Contract:
      - answer: The grounded natural-language explanation based on repository context.
      - question_type: The category assigned by the Feature 7 classifier.
      - retrieval_strategy: Which data source strategy was used (e.g. function_context, semantic_search_context).
      - sources: List of files and entities that contributed to the answer.
    """
    question: str
    project_id: str
    question_type: str = Field(description="Classification category from Feature 7")
    retrieval_strategy: str = Field(description="Retrieval strategy used by Feature 7")
    answer: str = Field(description="The LLM-generated grounded answer")
    sources: list[AnswerSource] = Field(default_factory=list, description="Source files and entities used to generate the answer")
    provider: str | None = Field(default=None, description="The LLM provider that generated the answer")
    model: str | None = Field(default=None, description="The model name that generated the answer")
