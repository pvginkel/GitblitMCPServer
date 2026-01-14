"""HTTP client for Gitblit Search API Plugin."""

from typing import Any

import httpx

from .config import get_config
from .schemas import (
    CommitSearchResponse,
    ErrorDetail,
    ErrorResponse,
    FileSearchResponse,
    ListFilesResponse,
    ListReposResponse,
    ReadFileResponse,
)


class GitblitClient:
    """HTTP client for calling Gitblit Search API Plugin endpoints."""

    def __init__(self) -> None:
        """Initialize the client with configuration."""
        self.config = get_config()
        self.base_url = self.config.api_base_url
        self.timeout = 30.0  # 30 second timeout for all requests

    def _map_status_to_error_code(self, status_code: int) -> str:
        """Map HTTP status code to MCP error code."""
        if status_code == 404:
            return "NOT_FOUND"
        elif status_code == 400:
            return "INVALID_REQUEST"
        elif status_code == 403:
            return "ACCESS_DENIED"
        else:
            return "INTERNAL_ERROR"

    def _handle_error_response(
        self, status_code: int, response_data: dict[str, Any]
    ) -> ErrorResponse:
        """Transform Search API Plugin error to MCP error format."""
        error_code = self._map_status_to_error_code(status_code)
        error_message = response_data.get("error", "Unknown error occurred")

        return ErrorResponse(error=ErrorDetail(code=error_code, message=error_message))

    def _make_request(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | ErrorResponse:
        """Make HTTP GET request to Search API Plugin.

        Args:
            endpoint: API endpoint path (e.g., '/repos')
            params: Query parameters

        Returns:
            Response data as dict or ErrorResponse on error
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = httpx.get(url, params=params, timeout=self.timeout)

            # Parse JSON response
            try:
                data = response.json()
            except Exception:
                return ErrorResponse(
                    error=ErrorDetail(
                        code="INTERNAL_ERROR", message="Invalid JSON response from server"
                    )
                )

            # Handle error responses
            if response.status_code != 200:
                return self._handle_error_response(response.status_code, data)

            return data

        except httpx.TimeoutException:
            return ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_ERROR",
                    message="Request timed out connecting to Gitblit server",
                )
            )
        except httpx.ConnectError:
            return ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_ERROR", message="Failed to connect to Gitblit server"
                )
            )
        except Exception as e:
            return ErrorResponse(
                error=ErrorDetail(code="INTERNAL_ERROR", message=f"Request failed: {str(e)}")
            )

    def list_repos(
        self, query: str | None = None, limit: int = 50, after: str | None = None
    ) -> ListReposResponse | ErrorResponse:
        """List repositories.

        Args:
            query: Optional search query to filter repositories by name
            limit: Maximum number of repositories to return
            after: Pagination cursor

        Returns:
            ListReposResponse or ErrorResponse
        """
        params: dict[str, Any] = {"limit": limit}
        if query:
            params["query"] = query
        if after:
            params["after"] = after

        result = self._make_request("/repos", params)
        if isinstance(result, ErrorResponse):
            return result

        return ListReposResponse(**result)

    def list_files(
        self, repo: str, path: str = "", revision: str | None = None
    ) -> ListFilesResponse | ErrorResponse:
        """List files in a repository path.

        Args:
            repo: Repository name (e.g., 'team/project.git')
            path: Directory path within repository
            revision: Branch, tag, or commit SHA

        Returns:
            ListFilesResponse or ErrorResponse
        """
        params: dict[str, Any] = {"repo": repo}
        if path:
            params["path"] = path
        if revision:
            params["revision"] = revision

        result = self._make_request("/files", params)
        if isinstance(result, ErrorResponse):
            return result

        return ListFilesResponse(**result)

    def read_file(
        self,
        repo: str,
        path: str,
        revision: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> ReadFileResponse | ErrorResponse:
        """Read file content.

        Args:
            repo: Repository name
            path: File path within repository
            revision: Branch, tag, or commit SHA
            start_line: 1-based starting line number
            end_line: 1-based ending line number (inclusive)

        Returns:
            ReadFileResponse or ErrorResponse
        """
        params: dict[str, Any] = {"repo": repo, "path": path}
        if revision:
            params["revision"] = revision
        if start_line is not None:
            params["startLine"] = start_line
        if end_line is not None:
            params["endLine"] = end_line

        result = self._make_request("/file", params)
        if isinstance(result, ErrorResponse):
            return result

        return ReadFileResponse(**result)

    def search_files(
        self,
        query: str,
        repos: list[str] | None = None,
        path_pattern: str | None = None,
        branch: str | None = None,
        count: int = 25,
        context_lines: int = 10,
    ) -> FileSearchResponse | ErrorResponse:
        """Search file contents.

        Args:
            query: Search query (Lucene syntax)
            repos: Repository names to search
            path_pattern: File path pattern filter
            branch: Branch filter
            count: Maximum number of results
            context_lines: Lines of context around matches

        Returns:
            FileSearchResponse or ErrorResponse
        """
        params: dict[str, Any] = {"query": query, "count": count, "contextLines": context_lines}
        if repos:
            params["repos"] = ",".join(repos)
        if path_pattern:
            params["pathPattern"] = path_pattern
        if branch:
            params["branch"] = branch

        result = self._make_request("/search/files", params)
        if isinstance(result, ErrorResponse):
            return result

        return FileSearchResponse(**result)

    def search_commits(
        self,
        query: str,
        repos: list[str],
        authors: list[str] | None = None,
        branch: str | None = None,
        count: int = 25,
    ) -> CommitSearchResponse | ErrorResponse:
        """Search commit history.

        Args:
            query: Search query (Lucene syntax)
            repos: Repository names to search (required)
            authors: Author names to filter by
            branch: Branch filter
            count: Maximum number of results

        Returns:
            CommitSearchResponse or ErrorResponse
        """
        params: dict[str, Any] = {"query": query, "repos": ",".join(repos), "count": count}
        if authors:
            params["authors"] = ",".join(authors)
        if branch:
            params["branch"] = branch

        result = self._make_request("/search/commits", params)
        if isinstance(result, ErrorResponse):
            return result

        return CommitSearchResponse(**result)


# Shared client singleton for connection pooling
_shared_client: GitblitClient | None = None


def get_client() -> GitblitClient:
    """Get or create the shared GitblitClient instance.

    Uses a singleton pattern to enable HTTP connection pooling across
    multiple tool invocations.

    Returns:
        Shared GitblitClient instance
    """
    global _shared_client
    if _shared_client is None:
        _shared_client = GitblitClient()
    return _shared_client
