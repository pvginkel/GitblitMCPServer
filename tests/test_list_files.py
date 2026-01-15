"""Tests for gb_list_files tool."""

import pytest
from gitblit_mcp_server.client import GitblitClient
from gitblit_mcp_server.schemas import ErrorResponse, ListFilesResponse


def test_list_files_root(client: GitblitClient, test_repo: str) -> None:
    """Test listing files in repository root."""
    result = client.list_files(repo=test_repo)

    # May get error if repo doesn't exist - that's okay for MVP testing
    if isinstance(result, ErrorResponse):
        assert result.error.code in ("NOT_FOUND", "INVALID_REQUEST")
        pytest.skip(f"Test repository '{test_repo}' not available on test server")

    assert isinstance(result, ListFilesResponse)
    assert isinstance(result.files, list)
    assert isinstance(result.totalCount, int)
    assert isinstance(result.limitHit, bool)

    # Validate structure if files exist
    if result.files:
        file = result.files[0]
        assert file.path
        assert isinstance(file.isDirectory, bool)
        # Directories should end with /
        if file.isDirectory:
            assert file.path.endswith("/")


def test_list_files_nonexistent_repo(client: GitblitClient) -> None:
    """Test listing files in nonexistent repository."""
    result = client.list_files(repo="nonexistent_fake_repo_xyz.git")

    assert isinstance(result, ErrorResponse)
    assert result.error.code == "NOT_FOUND"
    assert "not found" in result.error.message.lower() or "not" in result.error.message.lower()


def test_list_files_with_path(client: GitblitClient, test_repo: str) -> None:
    """Test listing files in specific directory path."""
    result = client.list_files(repo=test_repo, path="src")

    # May get error if repo doesn't exist or path doesn't exist
    if isinstance(result, ErrorResponse):
        pytest.skip(f"Test repository '{test_repo}' or path 'src' not available")

    assert isinstance(result, ListFilesResponse)
    assert isinstance(result.files, list)


def test_list_files_with_revision(client: GitblitClient, test_repo: str) -> None:
    """Test listing files at specific revision."""
    result = client.list_files(repo=test_repo, revision="HEAD")

    # May get error if repo doesn't exist
    if isinstance(result, ErrorResponse):
        pytest.skip(f"Test repository '{test_repo}' not available")

    assert isinstance(result, ListFilesResponse)
    assert isinstance(result.files, list)


def test_list_files_with_limit(client: GitblitClient, test_repo: str) -> None:
    """Test listing files with limit parameter."""
    result = client.list_files(repo=test_repo, limit=5)

    if isinstance(result, ErrorResponse):
        pytest.skip(f"Test repository '{test_repo}' not available")

    assert isinstance(result, ListFilesResponse)
    assert len(result.files) <= 5
    assert isinstance(result.totalCount, int)
    assert isinstance(result.limitHit, bool)

    # If totalCount > limit, limitHit should be True
    if result.totalCount > 5:
        assert result.limitHit is True


def test_list_files_with_offset(client: GitblitClient, test_repo: str) -> None:
    """Test listing files with offset parameter."""
    # Get first page
    result1 = client.list_files(repo=test_repo, limit=5, offset=0)

    if isinstance(result1, ErrorResponse):
        pytest.skip(f"Test repository '{test_repo}' not available")

    # Get second page
    result2 = client.list_files(repo=test_repo, limit=5, offset=5)

    if isinstance(result2, ErrorResponse):
        pytest.skip(f"Test repository '{test_repo}' not available")

    assert isinstance(result1, ListFilesResponse)
    assert isinstance(result2, ListFilesResponse)

    # If there are enough files, pages should be different
    if result1.totalCount > 5 and result2.files:
        page1_paths = {f.path for f in result1.files}
        assert result2.files[0].path not in page1_paths
