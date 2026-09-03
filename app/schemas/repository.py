from pydantic import BaseModel


class RepositoryRequest(BaseModel):
    repo_url: str


class RepositoryInfo(BaseModel):
    name: str
    owner: str
    description: str | None
    default_branch: str
    clone_url: str


class ProjectInfo(BaseModel):
    language: str
    framework: str
    package_manager: str
    build_tool: str
    has_readme: bool
    has_docker: bool
    has_gitignore: bool


class RepositoryAnalysisResponse(BaseModel):
    success: bool
    project_id: str
    repository: RepositoryInfo
    project_info: ProjectInfo
    clone_path: str
    total_source_files: int         
    source_files: list[str]   