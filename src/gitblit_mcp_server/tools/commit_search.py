"""Commit search MCP tool."""


from ..client import get_client
from ..schemas import CommitSearchResponse, ErrorResponse


def gb_commit_search(
    query: str,
    repos: list[str],
    authors: list[str] | None = None,
    branch: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> CommitSearchResponse | ErrorResponse:
    """Search commit history across repositories.

    Searches for commits by message content, author, or code changes.
    Use this to find when changes were made, who made them, or track down
    specific commits.

    Args:
        query: Search query. Supports Lucene syntax: exact phrases ("foo bar"),
               wildcards (foo*), AND/OR operators.
        repos: Repository names to search (required)
        authors: Filter by author names. Multiple authors use OR logic.
        branch: Filter by branch (e.g., 'refs/heads/main'). If omitted, searches
            only each repository's default branch.
        limit: Maximum number of results. Defaults to 25.
        offset: Number of results to skip for pagination. Defaults to 0.

    Returns:
        CommitSearchResponse with commits array, totalCount, and limitHit.
    """
    client = get_client()
    return client.search_commits(
        query=query,
        repos=repos,
        authors=authors,
        branch=branch,
        limit=limit,
        offset=offset,
    )
