"""FastMCP server setup and tool registration."""

from typing import Any

from fastmcp import FastMCP  # type: ignore

from .schemas import ErrorResponse, GitblitAPIError
from .tools.commit_search import gb_commit_search
from .tools.file_search import gb_file_search
from .tools.list_files import gb_list_files
from .tools.list_repos import gb_list_repos
from .tools.read_file import gb_read_file

# Server instance - created lazily via get_server()
_mcp: FastMCP | None = None


def _check_error(result: Any) -> None:
    """Check if result is an error response and raise exception if so."""
    if isinstance(result, ErrorResponse):
        raise GitblitAPIError(result.error.code, result.error.message)


def get_server() -> FastMCP:
    """Get or create the FastMCP server instance."""
    global _mcp
    if _mcp is None:
        _mcp = FastMCP("Gitblit MCP Server")
        _register_tools(_mcp)
    return _mcp


def _register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools with the server."""

    @mcp.tool()  # type: ignore[misc, untyped-decorator]
    def list_repos(
        query: str | None = None, limit: int = 50, after: str | None = None
    ) -> dict[str, Any]:
        """List repositories available in the Gitblit instance.

        Lists repositories that match a search query. Use this tool to discover
        repositories or resolve partial repository names to full names.

        Args:
            query: Optional search query to filter repositories by name
            limit: Maximum number of repositories to return (default: 50)
            after: Pagination cursor for fetching results after this point

        Returns:
            Dictionary with repositories array and pagination info
        """
        result = gb_list_repos(query=query, limit=limit, after=after)
        _check_error(result)
        return result.model_dump()

    @mcp.tool()  # type: ignore[misc, untyped-decorator]
    def list_files(
        repo: str, path: str = "", revision: str | None = None
    ) -> dict[str, Any]:
        """List files and directories in a repository path.

        Lists the files and subdirectories at a given path within a repository.
        Directories are indicated with a trailing slash.

        Args:
            repo: Repository name (e.g., 'team/project.git')
            path: Directory path within repository (default: root)
            revision: Branch, tag, or commit SHA (default: HEAD)

        Returns:
            Dictionary with files array
        """
        result = gb_list_files(repo=repo, path=path, revision=revision)
        _check_error(result)
        return result.model_dump()

    @mcp.tool()  # type: ignore[misc, untyped-decorator]
    def read_file(
        repo: str,
        path: str,
        revision: str | None = None,
        startLine: int | None = None,
        endLine: int | None = None,
    ) -> dict[str, Any]:
        """Read the content of a file from a repository.

        Reads and returns the content of a file at a specific path and revision.
        Supports line range parameters for large files. Files larger than 128KB
        will return an error.

        Args:
            repo: Repository name (e.g., 'team/project.git')
            path: File path within the repository
            revision: Branch, tag, or commit SHA (default: HEAD)
            startLine: 1-based line number to start reading from
            endLine: 1-based line number to stop reading at (inclusive)

        Returns:
            Dictionary with file content (line-numbered)
        """
        result = gb_read_file(
            repo=repo,
            path=path,
            revision=revision,
            startLine=startLine,
            endLine=endLine,
        )
        _check_error(result)
        return result.model_dump()

    @mcp.tool()  # type: ignore[misc, untyped-decorator]
    def file_search(
        query: str,
        repos: list[str] | None = None,
        pathPattern: str | None = None,
        branch: str | None = None,
        count: int = 25,
        contextLines: int = 100,
    ) -> dict[str, Any]:
        """Search for content within files across repositories.

        Searches file contents using Gitblit's Lucene index. Returns matching
        code snippets with surrounding context.

        Args:
            query: Search query (supports Lucene syntax)
            repos: Repository names to search (default: all)
            pathPattern: Filter by file path pattern (e.g., '*.java')
            branch: Filter by branch (e.g., 'refs/heads/main')
            count: Maximum number of results (default: 25)
            contextLines: Lines of context around matches (default: 100)

        Returns:
            Dictionary with search results and chunks
        """
        result = gb_file_search(
            query=query,
            repos=repos,
            pathPattern=pathPattern,
            branch=branch,
            count=count,
            contextLines=contextLines,
        )
        _check_error(result)
        return result.model_dump(exclude={"query"})

    @mcp.tool()  # type: ignore[misc, untyped-decorator]
    def commit_search(
        query: str,
        repos: list[str],
        authors: list[str] | None = None,
        branch: str | None = None,
        count: int = 25,
    ) -> dict[str, Any]:
        """Search commit history across repositories.

        Searches for commits by message content, author, or code changes.
        Use this to find when changes were made, who made them, or track down
        specific commits.

        Args:
            query: Search query (supports Lucene syntax)
            repos: Repository names to search (required)
            authors: Filter by author names (OR logic)
            branch: Filter by branch (e.g., 'refs/heads/main')
            count: Maximum number of results (default: 25)

        Returns:
            Dictionary with commits array
        """
        result = gb_commit_search(
            query=query, repos=repos, authors=authors, branch=branch, count=count
        )
        _check_error(result)
        return result.model_dump(exclude={"query"})
