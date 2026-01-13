"""Tests for gb_commit_search tool."""

import pytest
from gitblit_mcp_server.client import GitblitClient
from gitblit_mcp_server.schemas import CommitSearchResponse, ErrorResponse


def test_commit_search_basic(client: GitblitClient, test_repo: str) -> None:
    """Test basic commit search with wildcard query."""
    # Search for all commits with wildcard
    result = client.search_commits(query="*", repos=[test_repo])

    assert isinstance(result, CommitSearchResponse)
    assert result.query
    assert isinstance(result.totalCount, int)
    assert isinstance(result.limitHit, bool)
    assert isinstance(result.commits, list)

    # Should have commits in the test repo
    assert result.totalCount > 0
    assert len(result.commits) > 0

    # Validate commit structure
    commit = result.commits[0]
    assert commit.repository == test_repo
    assert commit.commit  # SHA
    assert commit.author
    assert commit.date
    assert commit.title
    assert commit.message


def test_commit_search_with_query(client: GitblitClient, test_repo: str) -> None:
    """Test commit search with specific query."""
    result = client.search_commits(query="fix", repos=[test_repo])

    # May get error or no results
    if isinstance(result, ErrorResponse):
        pytest.skip("Commit search not available")

    assert isinstance(result, CommitSearchResponse)
    assert isinstance(result.commits, list)


def test_commit_search_no_results(client: GitblitClient, test_repo: str) -> None:
    """Test commit search with query that matches nothing."""
    result = client.search_commits(query="nonexistent_commit_xyz_123", repos=[test_repo])

    # May get error or no results
    if isinstance(result, ErrorResponse):
        pytest.skip("Commit search not available")

    assert isinstance(result, CommitSearchResponse)
    assert len(result.commits) == 0
    assert result.totalCount == 0


def test_commit_search_with_authors(client: GitblitClient, test_repo: str) -> None:
    """Test commit search filtered by authors."""
    # Use wildcard query with author filter
    result = client.search_commits(query="*", repos=[test_repo], authors=["Pieter"])

    assert isinstance(result, CommitSearchResponse)
    assert isinstance(result.commits, list)

    # All commits should be from specified authors
    for commit in result.commits:
        assert "Pieter" in commit.author


def test_commit_search_with_count_limit(client: GitblitClient, test_repo: str) -> None:
    """Test commit search with result count limit."""
    result = client.search_commits(query="*", repos=[test_repo], count=3)

    assert isinstance(result, CommitSearchResponse)
    # Should return at most 3 commits
    assert len(result.commits) <= 3
    # With wildcard on a repo with commits, should have results
    assert len(result.commits) > 0


def test_commit_search_multiple_repos(client: GitblitClient) -> None:
    """Test commit search across multiple repositories."""
    # Search in multiple known repos
    result = client.search_commits(
        query="*", repos=["netide/netide.git", "netide/netide-demo.git"], count=10
    )

    assert isinstance(result, CommitSearchResponse)
    assert isinstance(result.commits, list)
    assert len(result.commits) > 0


def test_commit_search_exact_phrase(client: GitblitClient, test_repo: str) -> None:
    """Test commit search with exact phrase query."""
    result = client.search_commits(query='"bug fix"', repos=[test_repo])

    # May get error or no results
    if isinstance(result, ErrorResponse):
        pytest.skip("Commit search not available")

    assert isinstance(result, CommitSearchResponse)
    assert isinstance(result.commits, list)


def test_commit_search_boolean_operators(client: GitblitClient, test_repo: str) -> None:
    """Test commit search with boolean operators."""
    result = client.search_commits(query="fix OR bug", repos=[test_repo])

    # May get error or no results
    if isinstance(result, ErrorResponse):
        pytest.skip("Commit search not available")

    assert isinstance(result, CommitSearchResponse)
    assert isinstance(result.commits, list)
