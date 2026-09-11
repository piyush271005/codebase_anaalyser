from pathlib import Path
from git import Repo


REPOSITORIES_DIR = Path("repositories")


def clone_repository(repo_url: str, project_id: str) -> str:
    """
    Clone a GitHub repository into the repositories folder.

    Returns:
        Local path of cloned repository.
    """

    # Create repositories directory if it doesn't exist
    REPOSITORIES_DIR.mkdir(exist_ok=True)

    clone_path = REPOSITORIES_DIR / project_id

    if not clone_path.exists():
        Repo.clone_from(
            repo_url,
            clone_path
        )

    repository_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    return {"project_id": project_id, "clone_path": clone_path, "repository_name": repository_name}