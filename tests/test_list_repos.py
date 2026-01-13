"""Tests for gb_list_repos tool."""


from gitblit_mcp_server.client import GitblitClient
from gitblit_mcp_server.schemas import ListReposResponse


def test_list_repos_no_filters(client: GitblitClient) -> None:
    """Test listing repositories without any filters."""
    result = client.list_repos()

    assert isinstance(result, ListReposResponse)
    assert isinstance(result.repositories, list)
    assert isinstance(result.pagination.totalCount, int)
    assert isinstance(result.pagination.hasNextPage, bool)

    # If repositories exist, validate structure
    if result.repositories:
        repo = result.repositories[0]
        assert repo.name
        assert repo.description is not None
        assert isinstance(repo.hasCommits, bool)


def test_list_repos_with_query(client: GitblitClient) -> None:
    """Test listing repositories with search query."""
    # Search for any repository - this should work even if no matches
    result = client.list_repos(query="test")

    assert isinstance(result, ListReposResponse)
    assert isinstance(result.repositories, list)
    assert result.pagination.totalCount >= 0


def test_list_repos_with_limit(client: GitblitClient) -> None:
    """Test listing repositories with limit parameter."""
    result = client.list_repos(limit=5)

    assert isinstance(result, ListReposResponse)
    # Should return at most 5 repositories
    assert len(result.repositories) <= 5


def test_list_repos_nonexistent_query(client: GitblitClient) -> None:
    """Test listing repositories with query that matches nothing."""
    result = client.list_repos(query="nonexistent_repo_xyz_123")

    assert isinstance(result, ListReposResponse)
    # Should return empty list with totalCount=0
    assert len(result.repositories) == 0
    assert result.pagination.totalCount == 0
    assert result.pagination.hasNextPage is False
