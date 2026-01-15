"""List files MCP tool."""


from ..client import get_client
from ..schemas import ErrorResponse, ListFilesResponse


def gb_list_files(
    repo: str,
    path: str = "",
    revision: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> ListFilesResponse | ErrorResponse:
    """List files and directories in a repository path.

    Lists the files and subdirectories at a given path within a repository.
    Directories are indicated with a trailing slash. Use this to navigate
    repository structure.

    Args:
        repo: Repository name (e.g., 'team/project.git')
        path: Directory path within repository. Defaults to root if not specified.
        revision: Branch, tag, or commit SHA. Defaults to HEAD of default branch.
        limit: Maximum number of files to return. Defaults to 100.
        offset: Number of results to skip for pagination. Defaults to 0.

    Returns:
        ListFilesResponse with files array, totalCount, and limitHit.
    """
    client = get_client()
    return client.list_files(repo=repo, path=path, revision=revision, limit=limit, offset=offset)
