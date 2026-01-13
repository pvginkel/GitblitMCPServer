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
