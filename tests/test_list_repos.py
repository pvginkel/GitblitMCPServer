"""Tests for gb_list_repos tool."""


from gitblit_mcp_server.client import GitblitClient
from gitblit_mcp_server.schemas import ListReposResponse


def test_list_repos_no_filters(client: GitblitClient) -> None:
    """Test listing repositories without any filters."""
    result = client.list_repos()

    assert isinstance(result, ListReposResponse)
    assert isinstance(result.repositories, list)
    assert isinstance(result.totalCount, int)
    assert isinstance(result.limitHit, bool)

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
    assert result.totalCount >= 0


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
    assert result.totalCount == 0
    assert result.limitHit is False


def test_list_repos_with_offset(client: GitblitClient) -> None:
    """Test listing repositories with offset parameter."""
    # Get first page
    result1 = client.list_repos(limit=5, offset=0)
    assert isinstance(result1, ListReposResponse)

    # Get second page
    result2 = client.list_repos(limit=5, offset=5)
    assert isinstance(result2, ListReposResponse)

    # If there are enough repos, pages should be different
    if result1.totalCount > 5:
        # First repo of page 2 should not be in page 1
        if result2.repositories:
            page1_names = {r.name for r in result1.repositories}
            assert result2.repositories[0].name not in page1_names
