"""Read file MCP tool."""


from ..client import get_client
from ..schemas import ErrorResponse, ReadFileResponse


def gb_read_file(
    repo: str,
    path: str,
    revision: str | None = None,
    startLine: int | None = None,
    endLine: int | None = None,
) -> ReadFileResponse | ErrorResponse:
    """Read the content of a file from a repository.

    Reads and returns the content of a file at a specific path and revision.
    Supports line range parameters for large files. Files larger than 128KB
    will return an error.

    Args:
        repo: Repository name (e.g., 'team/project.git')
        path: File path within the repository
        revision: Branch, tag, or commit SHA. Defaults to HEAD of default branch.
        startLine: 1-based line number to start reading from
        endLine: 1-based line number to stop reading at (inclusive)

    Returns:
        ReadFileResponse with file content (line-numbered), or ErrorResponse on error.
    """
    client = get_client()
    return client.read_file(
        repo=repo, path=path, revision=revision, start_line=startLine, end_line=endLine
    )
