import requests
from fastapi import HTTPException


def check_repository_access(repo_url: str):
    """
    Checks whether the GitHub repository exists and is publicly accessible.
    Returns the repository metadata if accessible.
    """

    # Convert GitHub URL to GitHub API URL
    # Example:
    # https://github.com/facebook/react
    # ->
    # https://api.github.com/repos/facebook/react

    api_url = repo_url.replace(
        "https://github.com/",
        "https://api.github.com/repos/"
    )

    response = requests.get(api_url)

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Repository not found."
        )

    if response.status_code == 403:
        raise HTTPException(
            status_code=403,
            detail="Repository is private or GitHub API rate limit exceeded."
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Unable to access repository."
        )

    return response.json()