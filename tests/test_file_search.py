"""Tests for gb_file_search tool."""

import pytest
from gitblit_mcp_server.client import GitblitClient
from gitblit_mcp_server.schemas import ErrorResponse, FileSearchResponse


def test_file_search_basic(client: GitblitClient) -> None:
    """Test basic file content search."""
    # Search for a common term that might exist in many repos
    result = client.search_files(query="test")

    # May get error or no results depending on indexed content
    if isinstance(result, ErrorResponse):
        assert result.error.code in ("INVALID_REQUEST", "INTERNAL_ERROR")
        pytest.skip("File search not available or query failed")

    assert isinstance(result, FileSearchResponse)
    # Query may be transformed by Search API Plugin (e.g., "type:blob AND (test)")
    assert "test" in result.query
    assert isinstance(result.totalCount, int)
    assert isinstance(result.limitHit, bool)
    assert isinstance(result.results, list)

    # Validate result structure if results exist
    if result.results:
        search_result = result.results[0]
        assert search_result.repository
        assert search_result.path
        assert isinstance(search_result.chunks, list)

        if search_result.chunks:
            chunk = search_result.chunks[0]
            assert isinstance(chunk.startLine, int)
            assert isinstance(chunk.endLine, int)
            assert isinstance(chunk.content, str)
            assert chunk.startLine > 0  # Should be 1-indexed
            assert chunk.endLine >= chunk.startLine


def test_file_search_no_results(client: GitblitClient) -> None:
    """Test file search with query that matches nothing."""
    result = client.search_files(query="nonexistent_unique_string_xyz_123")

    # Should return empty results
    if isinstance(result, ErrorResponse):
        pytest.skip("Search not available")

    assert isinstance(result, FileSearchResponse)
    assert len(result.results) == 0
    assert result.totalCount == 0


def test_file_search_with_repos_filter(client: GitblitClient, test_repo: str) -> None:
    """Test file search filtered to specific repositories."""
    result = client.search_files(query="test", repos=[test_repo])

    # May get error or no results
    if isinstance(result, ErrorResponse):
        pytest.skip("Search not available or repo not indexed")

    assert isinstance(result, FileSearchResponse)
    assert isinstance(result.results, list)

    # All results should be from the specified repo
    for search_result in result.results:
        assert search_result.repository == test_repo


def test_file_search_with_path_pattern(client: GitblitClient) -> None:
    """Test file search with path pattern filter."""
    result = client.search_files(query="test", path_pattern="*.md")

    # May get error or no results
    if isinstance(result, ErrorResponse):
        pytest.skip("Search not available")

    assert isinstance(result, FileSearchResponse)

    # All results should match the path pattern
    for search_result in result.results:
        assert search_result.path.endswith(".md")


def test_file_search_with_limit(client: GitblitClient) -> None:
    """Test file search with result limit."""
    result = client.search_files(query="test", limit=3)

    # May get error or no results
    if isinstance(result, ErrorResponse):
        pytest.skip("Search not available")

    assert isinstance(result, FileSearchResponse)
    # Should return at most 3 results
    assert len(result.results) <= 3


def test_file_search_exact_phrase(client: GitblitClient) -> None:
    """Test file search with exact phrase query."""
    result = client.search_files(query='"test case"')

    # May get error or no results
    if isinstance(result, ErrorResponse):
        pytest.skip("Search not available")

    assert isinstance(result, FileSearchResponse)
    assert isinstance(result.results, list)


def test_file_search_boolean_operators(client: GitblitClient) -> None:
    """Test file search with boolean operators."""
    result = client.search_files(query="test AND case")

    # May get error or no results
    if isinstance(result, ErrorResponse):
        pytest.skip("Search not available")

    assert isinstance(result, FileSearchResponse)
    assert isinstance(result.results, list)


def test_file_search_wildcard_query(client: GitblitClient, test_repo: str) -> None:
    """Test file search with wildcard query (browse mode)."""
    # Wildcard query requires at least one filter (repos or pathPattern)
    result = client.search_files(query="*", repos=[test_repo], limit=10)

    assert isinstance(result, FileSearchResponse)
    assert isinstance(result.totalCount, int)
    assert isinstance(result.results, list)

    # Should return results for the repo
    assert result.totalCount > 0
    assert len(result.results) > 0

    # Validate result structure
    for search_result in result.results:
        assert search_result.repository == test_repo
        assert search_result.path
        # Wildcard queries return empty chunks (file listing mode)
        assert isinstance(search_result.chunks, list)


def test_file_search_wildcard_with_path_pattern(client: GitblitClient, test_repo: str) -> None:
    """Test wildcard file search with path pattern filter."""
    result = client.search_files(query="*", repos=[test_repo], path_pattern="*.cs", limit=10)

    assert isinstance(result, FileSearchResponse)
    assert isinstance(result.results, list)

    # All results should match the path pattern
    for search_result in result.results:
        assert search_result.path.endswith(".cs")


def test_file_search_with_offset(client: GitblitClient, test_repo: str) -> None:
    """Test file search with offset pagination."""
    # Get first page
    result1 = client.search_files(query="*", repos=[test_repo], limit=5, offset=0)
    assert isinstance(result1, FileSearchResponse)

    # Get second page
    result2 = client.search_files(query="*", repos=[test_repo], limit=5, offset=5)
    assert isinstance(result2, FileSearchResponse)

    # If there are enough results, pages should be different
    if result1.totalCount > 5 and result2.results:
        page1_paths = {r.path for r in result1.results}
        assert result2.results[0].path not in page1_paths
