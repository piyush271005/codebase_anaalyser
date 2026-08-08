import re

GITHUB_REPO_PATTERN = re.compile(
    r"^https://github\.com/[\w.-]+/[\w.-]+/?$"
)


def validate_github_url(url: str) -> tuple[bool, str]:
    """
    Validates a GitHub repository URL.

    Returns:
        (True, "") if valid
        (False, error_message) if invalid
    """

    if not url:
        return False, "Repository URL cannot be empty."

    url = url.strip()

    if not GITHUB_REPO_PATTERN.match(url):
        return (
            False,
            "Invalid GitHub repository URL."
        )

    return True, ""