"""Unit tests for GitblitClient with mocked HTTP responses.

These tests verify client behavior in isolation by mocking httpx responses,
allowing testing of error handling, response parsing, and edge cases without
requiring a live server.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from gitblit_mcp_server.client import GitblitClient
from gitblit_mcp_server.schemas import (
    CommitSearchResponse,
    ErrorResponse,
    FileSearchResponse,
    ListFilesResponse,
    ListReposResponse,
    ReadFileResponse,
)


@pytest.fixture
def mock_client() -> GitblitClient:
    """Create a GitblitClient for testing."""
    with patch.dict("os.environ", {"GITBLIT_URL": "http://test-server:8080"}):
        return GitblitClient()


class TestListReposClient:
    """Tests for GitblitClient.list_repos method."""

    def test_list_repos_success(self, mock_client: GitblitClient) -> None:
        """Test successful list_repos response parsing."""
        mock_response = {
            "repositories": [
                {
                    "name": "test/repo.git",
                    "description": "Test repo",
                    "lastChange": "2024-01-15T10:30:00Z",
                    "hasCommits": True,
                }
            ],
            "pagination": {
                "totalCount": 1,
                "hasNextPage": False,
                "endCursor": None,
            },
        }

        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, json=lambda: mock_response
            )
            result = mock_client.list_repos()

        assert isinstance(result, ListReposResponse)
        assert len(result.repositories) == 1
        assert result.repositories[0].name == "test/repo.git"
        assert result.pagination.totalCount == 1

    def test_list_repos_empty(self, mock_client: GitblitClient) -> None:
        """Test list_repos with no repositories."""
        mock_response = {
            "repositories": [],
            "pagination": {"totalCount": 0, "hasNextPage": False, "endCursor": None},
        }

        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, json=lambda: mock_response
            )
            result = mock_client.list_repos()

        assert isinstance(result, ListReposResponse)
        assert len(result.repositories) == 0

    def test_list_repos_with_pagination(self, mock_client: GitblitClient) -> None:
        """Test list_repos pagination parameters."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {
                    "repositories": [],
                    "pagination": {
                        "totalCount": 100,
                        "hasNextPage": True,
                        "endCursor": "cursor123",
                    },
                },
            )
            mock_client.list_repos(query="test", limit=10, after="cursor_abc")

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args.kwargs["params"]["query"] == "test"
        assert call_args.kwargs["params"]["limit"] == 10
        assert call_args.kwargs["params"]["after"] == "cursor_abc"


class TestListFilesClient:
    """Tests for GitblitClient.list_files method."""

    def test_list_files_success(self, mock_client: GitblitClient) -> None:
        """Test successful list_files response parsing."""
        mock_response = {
            "files": [
                {"path": "src/", "isDirectory": True},
                {"path": "README.md", "isDirectory": False},
            ]
        }

        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, json=lambda: mock_response
            )
            result = mock_client.list_files(repo="test.git")

        assert isinstance(result, ListFilesResponse)
        assert len(result.files) == 2
        assert result.files[0].isDirectory is True
        assert result.files[1].isDirectory is False

    def test_list_files_with_path_and_revision(
        self, mock_client: GitblitClient
    ) -> None:
        """Test list_files with path and revision parameters."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, json=lambda: {"files": []}
            )
            mock_client.list_files(repo="test.git", path="src/main", revision="develop")

        call_args = mock_get.call_args
        assert call_args.kwargs["params"]["repo"] == "test.git"
        assert call_args.kwargs["params"]["path"] == "src/main"
        assert call_args.kwargs["params"]["revision"] == "develop"


class TestReadFileClient:
    """Tests for GitblitClient.read_file method."""

    def test_read_file_success(self, mock_client: GitblitClient) -> None:
        """Test successful read_file response parsing."""
        mock_response = {"content": "1: line one\n2: line two\n3: line three"}

        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, json=lambda: mock_response
            )
            result = mock_client.read_file(repo="test.git", path="file.txt")

        assert isinstance(result, ReadFileResponse)
        assert "line one" in result.content

    def test_read_file_with_line_range(self, mock_client: GitblitClient) -> None:
        """Test read_file with line range parameters."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, json=lambda: {"content": "5: line five"}
            )
            mock_client.read_file(
                repo="test.git", path="file.txt", start_line=5, end_line=10
            )

        call_args = mock_get.call_args
        assert call_args.kwargs["params"]["startLine"] == 5
        assert call_args.kwargs["params"]["endLine"] == 10


class TestFileSearchClient:
    """Tests for GitblitClient.search_files method."""

    def test_search_files_success(self, mock_client: GitblitClient) -> None:
        """Test successful search_files response parsing."""
        mock_response = {
            "query": "type:blob AND (test)",
            "totalCount": 5,
            "limitHit": False,
            "results": [
                {
                    "repository": "test.git",
                    "path": "src/test.py",
                    "branch": "refs/heads/main",
                    "commitId": "abc123",
                    "chunks": [
                        {"startLine": 10, "endLine": 15, "content": "10: test code"}
                    ],
                }
            ],
        }

        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, json=lambda: mock_response
            )
            result = mock_client.search_files(query="test")

        assert isinstance(result, FileSearchResponse)
        assert result.totalCount == 5
        assert len(result.results) == 1
        assert result.results[0].repository == "test.git"

    def test_search_files_with_filters(self, mock_client: GitblitClient) -> None:
        """Test search_files with all filter parameters."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {
                    "query": "test",
                    "totalCount": 0,
                    "limitHit": False,
                    "results": [],
                },
            )
            mock_client.search_files(
                query="test",
                repos=["repo1.git", "repo2.git"],
                path_pattern="*.py",
                branch="refs/heads/main",
                count=50,
                context_lines=20,
            )

        call_args = mock_get.call_args
        params = call_args.kwargs["params"]
        assert params["query"] == "test"
        assert params["repos"] == "repo1.git,repo2.git"
        assert params["pathPattern"] == "*.py"
        assert params["branch"] == "refs/heads/main"
        assert params["count"] == 50
        assert params["contextLines"] == 20


class TestCommitSearchClient:
    """Tests for GitblitClient.search_commits method."""

    def test_search_commits_success(self, mock_client: GitblitClient) -> None:
        """Test successful search_commits response parsing."""
        mock_response = {
            "query": "type:commit AND (fix)",
            "totalCount": 3,
            "limitHit": False,
            "commits": [
                {
                    "repository": "test.git",
                    "commit": "abc123def456",
                    "author": "John Doe",
                    "committer": "John Doe",
                    "date": "2024-01-15T10:30:00Z",
                    "title": "Fix bug",
                    "message": "Fix bug in parser",
                    "branch": "refs/heads/main",
                }
            ],
        }

        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, json=lambda: mock_response
            )
            result = mock_client.search_commits(query="fix", repos=["test.git"])

        assert isinstance(result, CommitSearchResponse)
        assert result.totalCount == 3
        assert len(result.commits) == 1
        assert result.commits[0].author == "John Doe"

    def test_search_commits_with_authors(self, mock_client: GitblitClient) -> None:
        """Test search_commits with author filter."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {
                    "query": "test",
                    "totalCount": 0,
                    "limitHit": False,
                    "commits": [],
                },
            )
            mock_client.search_commits(
                query="test",
                repos=["test.git"],
                authors=["Alice", "Bob"],
                count=10,
            )

        call_args = mock_get.call_args
        params = call_args.kwargs["params"]
        assert params["authors"] == "Alice,Bob"
        assert params["count"] == 10


class TestErrorHandling:
    """Tests for client error handling."""

    def test_404_error(self, mock_client: GitblitClient) -> None:
        """Test handling of 404 Not Found errors."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=404, json=lambda: {"error": "Repository not found"}
            )
            result = mock_client.list_files(repo="nonexistent.git")

        assert isinstance(result, ErrorResponse)
        assert result.error.code == "NOT_FOUND"
        assert "not found" in result.error.message.lower()

    def test_400_error(self, mock_client: GitblitClient) -> None:
        """Test handling of 400 Bad Request errors."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=400, json=lambda: {"error": "Invalid query syntax"}
            )
            result = mock_client.search_files(query="[invalid")

        assert isinstance(result, ErrorResponse)
        assert result.error.code == "INVALID_REQUEST"

    def test_403_error(self, mock_client: GitblitClient) -> None:
        """Test handling of 403 Forbidden errors."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=403, json=lambda: {"error": "Access denied"}
            )
            result = mock_client.read_file(repo="private.git", path="secret.txt")

        assert isinstance(result, ErrorResponse)
        assert result.error.code == "ACCESS_DENIED"

    def test_500_error(self, mock_client: GitblitClient) -> None:
        """Test handling of 500 Internal Server errors."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=500, json=lambda: {"error": "Internal server error"}
            )
            result = mock_client.list_repos()

        assert isinstance(result, ErrorResponse)
        assert result.error.code == "INTERNAL_ERROR"

    def test_invalid_json_response(self, mock_client: GitblitClient) -> None:
        """Test handling of non-JSON responses."""
        with patch("httpx.get") as mock_get:
            mock_response = MagicMock(status_code=200)
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response
            result = mock_client.list_repos()

        assert isinstance(result, ErrorResponse)
        assert result.error.code == "INTERNAL_ERROR"
        assert "Invalid JSON" in result.error.message

    def test_connection_error(self, mock_client: GitblitClient) -> None:
        """Test handling of connection errors."""
        with patch("httpx.get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")
            result = mock_client.list_repos()

        assert isinstance(result, ErrorResponse)
        assert result.error.code == "INTERNAL_ERROR"
        assert "connect" in result.error.message.lower()

    def test_timeout_error(self, mock_client: GitblitClient) -> None:
        """Test handling of timeout errors."""
        with patch("httpx.get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timed out")
            result = mock_client.list_repos()

        assert isinstance(result, ErrorResponse)
        assert result.error.code == "INTERNAL_ERROR"
        assert "timed out" in result.error.message.lower()


class TestURLConstruction:
    """Tests for proper URL construction."""

    def test_base_url_without_trailing_slash(self) -> None:
        """Test that base URL trailing slash is handled."""
        with patch.dict(
            "os.environ", {"GITBLIT_URL": "http://test-server:8080/"}
        ):
            client = GitblitClient()
            assert not client.base_url.endswith("//")

    def test_api_endpoint_path(self) -> None:
        """Test that API endpoint path is correct."""
        with patch.dict("os.environ", {"GITBLIT_URL": "http://test-server:8080"}):
            client = GitblitClient()
            assert "/api/.mcp-internal" in client.base_url
