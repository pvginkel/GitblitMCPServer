"""Tests for gb_read_file tool."""

import pytest
from gitblit_mcp_server.client import GitblitClient
from gitblit_mcp_server.schemas import ErrorResponse, ReadFileResponse


def test_read_file_basic(client: GitblitClient, test_repo: str) -> None:
    """Test reading a file from repository."""
    # Try to read a common file that might exist
    result = client.read_file(repo=test_repo, path="License.txt")

    # May get error if repo/file doesn't exist - that's okay for MVP testing
    if isinstance(result, ErrorResponse):
        assert result.error.code in ("NOT_FOUND", "INVALID_REQUEST")
        pytest.skip(f"Test repository '{test_repo}' or file 'License.txt' not available")

    assert isinstance(result, ReadFileResponse)
    assert isinstance(result.content, str)

    # Content should have line number prefix format
    if result.content:
        lines = result.content.split("\n")
        # First line should start with "1: "
        if lines[0]:
            assert lines[0].startswith("1: ") or lines[0].startswith("1:")


def test_read_file_nonexistent(client: GitblitClient, test_repo: str) -> None:
    """Test reading nonexistent file."""
    result = client.read_file(repo=test_repo, path="nonexistent_file_xyz_123.txt")

    assert isinstance(result, ErrorResponse)
    assert result.error.code in ("NOT_FOUND", "INVALID_REQUEST")


def test_read_file_nonexistent_repo(client: GitblitClient) -> None:
    """Test reading file from nonexistent repository."""
    result = client.read_file(repo="nonexistent_repo_xyz.git", path="License.txt")

    assert isinstance(result, ErrorResponse)
    assert result.error.code == "NOT_FOUND"


def test_read_file_with_line_range(client: GitblitClient, test_repo: str) -> None:
    """Test reading file with line range."""
    result = client.read_file(repo=test_repo, path="License.txt", start_line=1, end_line=5)

    # May get error if repo/file doesn't exist
    if isinstance(result, ErrorResponse):
        pytest.skip(f"Test repository '{test_repo}' or file not available")

    assert isinstance(result, ReadFileResponse)
    assert isinstance(result.content, str)

    # Should have at most 5 lines
    if result.content:
        lines = [line for line in result.content.split("\n") if line]
        assert len(lines) <= 5


def test_read_file_with_revision(client: GitblitClient, test_repo: str) -> None:
    """Test reading file at specific revision."""
    result = client.read_file(repo=test_repo, path="License.txt", revision="HEAD")

    # May get error if repo/file doesn't exist
    if isinstance(result, ErrorResponse):
        pytest.skip(f"Test repository '{test_repo}' or file not available")

    assert isinstance(result, ReadFileResponse)
    assert isinstance(result.content, str)
