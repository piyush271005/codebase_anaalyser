from pydantic import BaseModel


class FunctionSummary(BaseModel):
    name: str
    file_path: str
    line: int | None = None
    end_line: int | None = None
    parameters: list[str] = []
    summary: str


class FileSummary(BaseModel):
    file_path: str
    language: str
    summary: str
    functions: list[str] = []
    classes: list[str] = []
    imports_count: int = 0


class ModuleSummary(BaseModel):
    name: str
    path: str
    summary: str
    files: list[str] = []


class ProjectSummary(BaseModel):
    summary: str
    main_technologies: list[str] = []
    main_features: list[str] = []


class UnderstandingRequest(BaseModel):
    repo_url: str


class UnderstandingResponse(BaseModel):
    repository_name: str
    project_summary: ProjectSummary
    modules: list[ModuleSummary]
    file_summaries: list[FileSummary]
    function_summaries: list[FunctionSummary]
