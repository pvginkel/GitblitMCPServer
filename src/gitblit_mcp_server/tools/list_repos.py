"""List repositories MCP tool."""


from ..client import get_client
from ..schemas import ErrorResponse, ListReposResponse


def gb_list_repos(
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> ListReposResponse | ErrorResponse:
    """List repositories available in the Gitblit instance.

    Lists repositories that match a search query. Use this tool to discover
    repositories or resolve partial repository names to full names.

    Args:
        query: Optional search query to filter repositories by name. Uses substring matching.
        limit: Maximum number of repositories to return. Defaults to 50.
        offset: Number of results to skip for pagination. Defaults to 0.

    Returns:
        ListReposResponse with repositories array, totalCount, and limitHit.
    """
    client = get_client()
    return client.list_repos(query=query, limit=limit, offset=offset)
