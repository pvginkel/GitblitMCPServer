"""Find files MCP tool."""


from ..client import get_client
from ..schemas import ErrorResponse, FindFilesResponse


def gb_find_files(
    pathPattern: str,
    repos: list[str] | None = None,
    revision: str | None = None,
    limit: int = 50,
) -> FindFilesResponse | ErrorResponse:
    """Find files matching a glob pattern across repositories.

    Uses Git tree walking (not Lucene) for efficient path-based file discovery.

    Args:
        pathPattern: Glob pattern to match file paths (e.g., '*.java', '**/Dockerfile').
        repos: Repository names to search. Omit to search all accessible repositories.
        revision: Branch, tag, or commit SHA. Omit to use HEAD of default branch.
        limit: Maximum number of files to return. Defaults to 50.

    Returns:
        FindFilesResponse with matching files grouped by repository.
    """
    client = get_client()
    return client.find_files(
        path_pattern=pathPattern,
        repos=repos,
        revision=revision,
        limit=limit,
    )
