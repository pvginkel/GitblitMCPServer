"""Unit tests for MCP tools with mocked backend.

These tests verify MCP tool behavior in isolation by mocking the GitblitClient,
allowing testing of tool logic, parameter handling, and error propagation.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client

from gitblit_mcp_server.schemas import (
    CommitSearchResponse,
    CommitSearchResult,
    ErrorDetail,
    ErrorResponse,
    FileInfo,
    FileSearchResponse,
    FileSearchResult,
    GitblitAPIError,
    ListFilesResponse,
    ListReposResponse,
    Pagination,
    ReadFileResponse,
    Repository,
    SearchChunk,
)
from gitblit_mcp_server.server import get_server


def create_mock_repos_response(
    repos: list[dict[str, Any]] | None = None,
) -> ListReposResponse:
    """Create a mock ListReposResponse."""
    if repos is None:
        repos = [
            {
                "name": "test/repo.git",
                "description": "Test repo",
                "lastChange": "2024-01-15T10:30:00Z",
                "hasCommits": True,
            }
        ]
    return ListReposResponse(
        repositories=[Repository(**r) for r in repos],
        pagination=Pagination(
            totalCount=len(repos), hasNextPage=False, endCursor=None
        ),
    )


def create_mock_files_response(
    files: list[dict[str, Any]] | None = None,
) -> ListFilesResponse:
    """Create a mock ListFilesResponse."""
    if files is None:
        files = [
            {"path": "src/", "isDirectory": True},
            {"path": "README.md", "isDirectory": False},
        ]
    return ListFilesResponse(files=[FileInfo(**f) for f in files])


def create_mock_file_content_response(content: str = "1: test") -> ReadFileResponse:
    """Create a mock ReadFileResponse."""
    return ReadFileResponse(content=content)


def create_mock_file_search_response(
    results: list[dict[str, Any]] | None = None, total: int = 0
) -> FileSearchResponse:
    """Create a mock FileSearchResponse."""
    if results is None:
        results = []
    return FileSearchResponse(
        query="test",
        totalCount=total or len(results),
        limitHit=False,
        results=[
            FileSearchResult(
                repository=r["repository"],
                path=r["path"],
                branch=r.get("branch"),
                commitId=r.get("commitId"),
                chunks=[SearchChunk(**c) for c in r.get("chunks", [])],
            )
            for r in results
        ],
    )


def create_mock_commit_search_response(
    commits: list[dict[str, Any]] | None = None, total: int = 0
) -> CommitSearchResponse:
    """Create a mock CommitSearchResponse."""
    if commits is None:
        commits = []
    return CommitSearchResponse(
        query="test",
        totalCount=total or len(commits),
        limitHit=False,
        commits=[CommitSearchResult(**c) for c in commits],
    )


@pytest.fixture
def mock_gitblit_client():
    """Create a mock GitblitClient.

    This patches the client module's get_client and _shared_client
    to return a mock client for all tool calls.
    """
    mock_client = MagicMock()

    with patch("gitblit_mcp_server.client.get_client", return_value=mock_client), \
         patch("gitblit_mcp_server.client._shared_client", mock_client):
        yield mock_client


@pytest.fixture
async def mcp_client_with_mock(mock_gitblit_client):
    """Create an MCP client with mocked backend."""
    # Patch at the tool module level where get_client is imported
    with patch("gitblit_mcp_server.tools.list_repos.get_client", return_value=mock_gitblit_client), \
         patch("gitblit_mcp_server.tools.list_files.get_client", return_value=mock_gitblit_client), \
         patch("gitblit_mcp_server.tools.read_file.get_client", return_value=mock_gitblit_client), \
         patch("gitblit_mcp_server.tools.file_search.get_client", return_value=mock_gitblit_client), \
         patch("gitblit_mcp_server.tools.commit_search.get_client", return_value=mock_gitblit_client):
        server = get_server()
        async with Client(server) as client:
            yield client, mock_gitblit_client


class TestListReposToolUnit:
    """Unit tests for list_repos tool."""

    async def test_returns_repositories(self, mcp_client_with_mock) -> None:
        """Test that list_repos returns repository data."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.list_repos.return_value = create_mock_repos_response()

        result = await client.call_tool("list_repos", {})

        assert len(result.content) > 0
        content = result.content[0].text
        assert "test/repo.git" in content

    async def test_passes_parameters(self, mcp_client_with_mock) -> None:
        """Test that list_repos passes parameters to client."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.list_repos.return_value = create_mock_repos_response([])

        await client.call_tool(
            "list_repos", {"query": "test", "limit": 10, "after": "cursor"}
        )

        mock_backend.list_repos.assert_called_once_with(
            query="test", limit=10, after="cursor"
        )

    async def test_error_response_raises_exception(self, mcp_client_with_mock) -> None:
        """Test that error responses are converted to exceptions."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.list_repos.return_value = ErrorResponse(
            error=ErrorDetail(code="INTERNAL_ERROR", message="Server error")
        )

        with pytest.raises(Exception) as exc_info:
            await client.call_tool("list_repos", {})

        assert "INTERNAL_ERROR" in str(exc_info.value)


class TestListFilesToolUnit:
    """Unit tests for list_files tool."""

    async def test_returns_files(self, mcp_client_with_mock) -> None:
        """Test that list_files returns file data."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.list_files.return_value = create_mock_files_response()

        result = await client.call_tool("list_files", {"repo": "test.git"})

        content = result.content[0].text
        assert "README.md" in content

    async def test_not_found_raises_exception(self, mcp_client_with_mock) -> None:
        """Test that NOT_FOUND errors are propagated."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.list_files.return_value = ErrorResponse(
            error=ErrorDetail(code="NOT_FOUND", message="Repository not found")
        )

        with pytest.raises(Exception) as exc_info:
            await client.call_tool("list_files", {"repo": "nonexistent.git"})

        assert "NOT_FOUND" in str(exc_info.value)


class TestReadFileToolUnit:
    """Unit tests for read_file tool."""

    async def test_returns_content(self, mcp_client_with_mock) -> None:
        """Test that read_file returns file content."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.read_file.return_value = create_mock_file_content_response(
            "1: Hello World\n2: Line two"
        )

        result = await client.call_tool(
            "read_file", {"repo": "test.git", "path": "file.txt"}
        )

        content = result.content[0].text
        assert "Hello World" in content

    async def test_passes_line_range(self, mcp_client_with_mock) -> None:
        """Test that line range parameters are passed."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.read_file.return_value = create_mock_file_content_response()

        await client.call_tool(
            "read_file",
            {"repo": "test.git", "path": "file.txt", "startLine": 5, "endLine": 10},
        )

        mock_backend.read_file.assert_called_once()
        # The client converts camelCase to snake_case internally
        call_args = mock_backend.read_file.call_args
        assert call_args.kwargs.get("start_line") == 5
        assert call_args.kwargs.get("end_line") == 10


class TestFileSearchToolUnit:
    """Unit tests for file_search tool."""

    async def test_returns_results(self, mcp_client_with_mock) -> None:
        """Test that file_search returns search results."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.search_files.return_value = create_mock_file_search_response(
            [
                {
                    "repository": "test.git",
                    "path": "src/main.py",
                    "chunks": [{"startLine": 10, "endLine": 15, "content": "10: test"}],
                }
            ],
            total=1,
        )

        result = await client.call_tool("file_search", {"query": "test"})

        content = result.content[0].text
        assert "src/main.py" in content

    async def test_passes_path_pattern(self, mcp_client_with_mock) -> None:
        """Test that pathPattern is passed to client."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.search_files.return_value = create_mock_file_search_response()

        await client.call_tool(
            "file_search", {"query": "test", "pathPattern": "*.py"}
        )

        mock_backend.search_files.assert_called_once()
        call_args = mock_backend.search_files.call_args
        # pathPattern should be passed (as pathPattern or path_pattern depending on mapping)
        assert call_args.kwargs.get("pathPattern") == "*.py" or \
               call_args.kwargs.get("path_pattern") == "*.py"

    async def test_passes_repos_filter(self, mcp_client_with_mock) -> None:
        """Test that repos filter is passed to client."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.search_files.return_value = create_mock_file_search_response()

        await client.call_tool(
            "file_search", {"query": "test", "repos": ["repo1.git", "repo2.git"]}
        )

        call_kwargs = mock_backend.search_files.call_args.kwargs
        assert call_kwargs["repos"] == ["repo1.git", "repo2.git"]


class TestCommitSearchToolUnit:
    """Unit tests for commit_search tool."""

    async def test_returns_commits(self, mcp_client_with_mock) -> None:
        """Test that commit_search returns commit data."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.search_commits.return_value = create_mock_commit_search_response(
            [
                {
                    "repository": "test.git",
                    "commit": "abc123",
                    "author": "John Doe",
                    "date": "2024-01-15T10:30:00Z",
                    "title": "Fix bug",
                    "message": "Fix bug in parser",
                }
            ],
            total=1,
        )

        result = await client.call_tool(
            "commit_search", {"query": "fix", "repos": ["test.git"]}
        )

        content = result.content[0].text
        assert "John Doe" in content
        assert "Fix bug" in content

    async def test_requires_repos_parameter(self, mcp_client_with_mock) -> None:
        """Test that repos parameter is required."""
        client, mock_backend = mcp_client_with_mock

        # FastMCP should validate required parameters
        with pytest.raises(Exception):
            await client.call_tool("commit_search", {"query": "test"})


class TestErrorPropagation:
    """Tests for error propagation through MCP layer."""

    async def test_not_found_error_propagates(self, mcp_client_with_mock) -> None:
        """Test that NOT_FOUND errors are properly propagated."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.read_file.return_value = ErrorResponse(
            error=ErrorDetail(code="NOT_FOUND", message="File not found")
        )

        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "read_file", {"repo": "test.git", "path": "missing.txt"}
            )

        error_str = str(exc_info.value)
        assert "NOT_FOUND" in error_str

    async def test_invalid_request_error_propagates(self, mcp_client_with_mock) -> None:
        """Test that INVALID_REQUEST errors are properly propagated."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.search_files.return_value = ErrorResponse(
            error=ErrorDetail(code="INVALID_REQUEST", message="Invalid query syntax")
        )

        with pytest.raises(Exception) as exc_info:
            await client.call_tool("file_search", {"query": "[invalid"})

        assert "INVALID_REQUEST" in str(exc_info.value)

    async def test_access_denied_error_propagates(self, mcp_client_with_mock) -> None:
        """Test that ACCESS_DENIED errors are properly propagated."""
        client, mock_backend = mcp_client_with_mock
        mock_backend.list_files.return_value = ErrorResponse(
            error=ErrorDetail(code="ACCESS_DENIED", message="Permission denied")
        )

        with pytest.raises(Exception) as exc_info:
            await client.call_tool("list_files", {"repo": "private.git"})

        assert "ACCESS_DENIED" in str(exc_info.value)
