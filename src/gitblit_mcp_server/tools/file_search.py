"""File search MCP tool."""


from ..client import get_client
from ..schemas import ErrorResponse, FileSearchResponse


def gb_file_search(
    query: str,
    repos: list[str] | None = None,
    pathPattern: str | None = None,
    branch: str | None = None,
    count: int = 25,
    contextLines: int = 10,
) -> FileSearchResponse | ErrorResponse:
    """Search for content within files across repositories.

    Searches file contents (blobs) using Gitblit's Lucene index. Returns matching
    code snippets with surrounding context. Use this for finding code patterns,
    function definitions, or specific text in files.

    Args:
        query: Search query. Supports Lucene syntax: exact phrases ("foo bar"),
               wildcards (foo*), AND/OR operators.
        repos: Repository names to search. If empty, searches all accessible repositories.
        pathPattern: Filter by file path pattern (e.g., '*.java', 'src/*.py')
        branch: Filter by branch (e.g., 'refs/heads/main'). If omitted, searches only each repository's default branch.
        count: Maximum number of results to return. Defaults to 25.
        contextLines: Number of context lines to include around each match. Defaults to 10, max 200.

    Returns:
        FileSearchResponse with search results and chunks, or ErrorResponse on error.
    """
    client = get_client()
    return client.search_files(
        query=query,
        repos=repos,
        path_pattern=pathPattern,
        branch=branch,
        count=count,
        context_lines=contextLines,
    )
