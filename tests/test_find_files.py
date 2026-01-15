"""Tests for gb_find_files tool."""

import pytest
from gitblit_mcp_server.client import GitblitClient
from gitblit_mcp_server.schemas import ErrorResponse, FindFilesResponse


def test_find_files_basic(client: GitblitClient) -> None:
    """Test finding files with a simple pattern."""
    result = client.find_files(path_pattern="*.txt")

    # May get empty results if no .txt files exist
    if isinstance(result, ErrorResponse):
        pytest.fail(f"Unexpected error: {result.error.message}")

    assert isinstance(result, FindFilesResponse)
    assert isinstance(result.pattern, str)
    assert result.pattern == "*.txt"
    assert isinstance(result.totalCount, int)
    assert isinstance(result.limitHit, bool)
    assert isinstance(result.results, list)


def test_find_files_recursive_pattern(client: GitblitClient) -> None:
    """Test finding files with recursive glob pattern."""
    result = client.find_files(path_pattern="**/*.txt")

    if isinstance(result, ErrorResponse):
        pytest.fail(f"Unexpected error: {result.error.message}")

    assert isinstance(result, FindFilesResponse)
    assert result.pattern == "**/*.txt"

    # All matching files should end with .txt
    for repo_result in result.results:
        for file_path in repo_result.files:
            assert file_path.endswith(".txt"), f"File {file_path} doesn't match pattern"


def test_find_files_specific_repo(client: GitblitClient, test_repo: str) -> None:
    """Test finding files in a specific repository."""
    result = client.find_files(path_pattern="**/*", repos=[test_repo], limit=10)

    if isinstance(result, ErrorResponse):
        pytest.skip(f"Test repository '{test_repo}' not available")

    assert isinstance(result, FindFilesResponse)

    # All results should be from the specified repository
    for repo_result in result.results:
        assert repo_result.repository == test_repo


def test_find_files_no_matches(client: GitblitClient) -> None:
    """Test pattern matching nothing returns empty results."""
    result = client.find_files(path_pattern="**/nonexistent_file_xyz_123_abc.nonexistent")

    if isinstance(result, ErrorResponse):
        pytest.fail(f"Unexpected error: {result.error.message}")

    assert isinstance(result, FindFilesResponse)
    assert result.totalCount == 0
    assert result.results == []


def test_find_files_limit(client: GitblitClient) -> None:
    """Test that limit parameter is respected."""
    result = client.find_files(path_pattern="**/*", limit=5)

    if isinstance(result, ErrorResponse):
        pytest.fail(f"Unexpected error: {result.error.message}")

    assert isinstance(result, FindFilesResponse)

    # Total files across all results should be at most 5 or limitHit should be True
    total_files = sum(len(r.files) for r in result.results)
    assert total_files <= 5 or result.limitHit


def test_find_files_response_structure(client: GitblitClient) -> None:
    """Test the response has correct structure."""
    result = client.find_files(path_pattern="**/*.md", limit=10)

    if isinstance(result, ErrorResponse):
        pytest.fail(f"Unexpected error: {result.error.message}")

    assert isinstance(result, FindFilesResponse)
    assert hasattr(result, "pattern")
    assert hasattr(result, "totalCount")
    assert hasattr(result, "limitHit")
    assert hasattr(result, "results")

    # Check result structure
    for repo_result in result.results:
        assert hasattr(repo_result, "repository")
        assert hasattr(repo_result, "files")
        assert isinstance(repo_result.repository, str)
        assert isinstance(repo_result.files, list)


def test_find_files_exact_filename(client: GitblitClient) -> None:
    """Test finding files by exact name."""
    # README.md is a common file
    result = client.find_files(path_pattern="**/README.md")

    if isinstance(result, ErrorResponse):
        pytest.fail(f"Unexpected error: {result.error.message}")

    assert isinstance(result, FindFilesResponse)

    # All matching files should be README.md
    for repo_result in result.results:
        for file_path in repo_result.files:
            assert file_path.endswith("README.md") or file_path == "README.md"


def test_find_files_with_revision(client: GitblitClient, test_repo: str) -> None:
    """Test finding files at specific revision."""
    result = client.find_files(
        path_pattern="**/*", repos=[test_repo], revision="HEAD", limit=5
    )

    if isinstance(result, ErrorResponse):
        pytest.skip(f"Test repository '{test_repo}' not available")

    assert isinstance(result, FindFilesResponse)
    # Just verify it returns successfully with revision parameter


def test_find_files_with_offset(client: GitblitClient, test_repo: str) -> None:
    """Test finding files with offset pagination."""
    # Get first page
    result1 = client.find_files(path_pattern="**/*", repos=[test_repo], limit=5, offset=0)

    if isinstance(result1, ErrorResponse):
        pytest.skip(f"Test repository '{test_repo}' not available")

    # Get second page
    result2 = client.find_files(path_pattern="**/*", repos=[test_repo], limit=5, offset=5)

    if isinstance(result2, ErrorResponse):
        pytest.skip(f"Test repository '{test_repo}' not available")

    assert isinstance(result1, FindFilesResponse)
    assert isinstance(result2, FindFilesResponse)

    # If there are enough files, pages should be different
    if result1.totalCount > 5 and result2.results:
        page1_files = set()
        for r in result1.results:
            page1_files.update(r.files)

        page2_files = set()
        for r in result2.results:
            page2_files.update(r.files)

        # Pages should not overlap
        if page2_files:
            assert not page1_files.intersection(page2_files)
