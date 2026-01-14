"""Commit search MCP tool."""


from ..client import get_client
from ..schemas import CommitSearchResponse, ErrorResponse


def gb_commit_search(
    query: str,
    repos: list[str],
    authors: list[str] | None = None,
    branch: str | None = None,
    count: int = 25,
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
        branch: Filter by branch (e.g., 'refs/heads/main'). If omitted, searches only each repository's default branch.
        count: Maximum number of results. Defaults to 25.

    Returns:
        CommitSearchResponse with commits array, or ErrorResponse on error.
    """
    client = get_client()
    return client.search_commits(
        query=query, repos=repos, authors=authors, branch=branch, count=count
    )
