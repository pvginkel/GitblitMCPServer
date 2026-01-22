"""FastMCP server setup and tool registration."""

from typing import Annotated, Any

from fastmcp import FastMCP  # type: ignore
from pydantic import Field

from .repo_validator import validate_repositories, validate_repository
from .schemas import ErrorResponse, GitblitAPIError
from .tools.commit_search import gb_commit_search
from .tools.file_search import gb_file_search
from .tools.find_files import gb_find_files
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


# Tool descriptions - kept concise to minimize token usage
# See docs/sourcegraph_mcp_tools.json for the comprehensive style reference

_LIST_REPOS_DESCRIPTION = """
Lists repositories in the Gitblit instance.

Behavior:
- Query uses case-insensitive substring matching on repository names
- If query is omitted, returns all accessible repositories
- Results are sorted alphabetically by name
- Supports offset-based pagination via 'offset' parameter
- Returns 'totalCount' (total matches) and 'limitHit' (whether more results exist)
""".strip()

_LIST_FILES_DESCRIPTION = """
Lists files and directories at a path within a repository.

Behavior:
- If path is omitted, lists the repository root
- If revision is omitted, uses HEAD of the default branch
- Directories are listed first, then files
- Directory paths end with '/'
- Supports offset-based pagination via 'offset' parameter
- Returns 'totalCount' (total files) and 'limitHit' (whether more results exist)
""".strip()

_READ_FILE_DESCRIPTION = """
Reads file content from a repository. Returns content with line numbers prefixed (e.g., "1: line\\n2: line").

Behavior:
- If revision is omitted, reads from HEAD of the default branch
- If startLine/endLine are omitted, reads the entire file
- Line numbers are 1-indexed
- Maximum file size is 128KB; larger files return an error
""".strip()

_FILE_SEARCH_DESCRIPTION = """
Searches file contents across repositories using Gitblit's Lucene index. Returns matching code snippets with context.

Behavior:
- Supports Lucene syntax: exact phrases ("foo"), wildcards (foo*), AND/OR operators
- If repos is omitted, searches all accessible repositories
- If branch is omitted, searches only each repository's default branch (avoids duplicate results)
- If pathPattern is omitted, searches all file types
- If limit is omitted, defaults to 25 (max: 100)
- If contextLines is omitted, defaults to 10 (max: 200)
- Supports offset-based pagination via 'offset' parameter
- Returns 'totalCount' (total matches) and 'limitHit' (whether more results exist)
""".strip()

_COMMIT_SEARCH_DESCRIPTION = """
Searches commit history across repositories using Gitblit's Lucene index.

Behavior:
- Supports Lucene syntax: exact phrases ("foo"), wildcards (foo*), AND/OR operators
- repos parameter is required; must specify at least one repository
- If authors is specified, multiple authors use OR logic
- If branch is omitted, searches only each repository's default branch (avoids duplicate results)
- If limit is omitted, defaults to 25 (max: 100)
- Supports offset-based pagination via 'offset' parameter
- Returns 'totalCount' (total matches) and 'limitHit' (whether more results exist)
""".strip()

_FIND_FILES_DESCRIPTION = """
Finds files matching a glob pattern across repositories using Git tree walking.
Use this to discover files by path/name without searching file contents.

Behavior:
- Uses Git tree walking (not Lucene index) for efficient path matching
- If repos is omitted, searches all accessible repositories
- If revision is omitted, uses HEAD of each repository's default branch
- If limit is omitted, defaults to 50 (max: 200)
- Supports offset-based pagination via 'offset' parameter
- Returns 'totalCount' (total matches) and 'limitHit' (whether more results exist)
- Results are grouped by repository
- Glob patterns: * matches any chars except /, ** matches any path segments, ? matches single char
""".strip()


def _register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools with the server."""

    @mcp.tool(description=_LIST_REPOS_DESCRIPTION)  # type: ignore[misc, untyped-decorator]
    def list_repos(
        query: Annotated[
            str | None,
            Field(
                description="Filter repositories by name (case-insensitive substring match). Omit to return all repositories."
            ),
        ] = None,
        limit: Annotated[
            int,
            Field(description="Maximum repositories to return. Default: 50, max: 100."),
        ] = 50,
        offset: Annotated[
            int,
            Field(description="Results to skip for pagination. Default: 0."),
        ] = 0,
    ) -> dict[str, Any]:
        result = gb_list_repos(query=query, limit=limit, offset=offset)
        _check_error(result)
        return result.model_dump()

    @mcp.tool(description=_LIST_FILES_DESCRIPTION)  # type: ignore[misc, untyped-decorator]
    def list_files(
        repo: Annotated[
            str,
            Field(description="Repository name with .git suffix (e.g., 'team/project.git')."),
        ],
        path: Annotated[
            str,
            Field(
                description="Directory path relative to root, no leading slash. Omit or use empty string for root."
            ),
        ] = "",
        revision: Annotated[
            str | None,
            Field(
                description="Branch, tag, or commit SHA. Omit to use HEAD of default branch."
            ),
        ] = None,
        limit: Annotated[
            int,
            Field(description="Maximum files to return. Default: 100, max: 1000."),
        ] = 100,
        offset: Annotated[
            int,
            Field(description="Results to skip for pagination. Default: 0."),
        ] = 0,
    ) -> dict[str, Any]:
        validate_repository(repo)
        result = gb_list_files(repo=repo, path=path, revision=revision, limit=limit, offset=offset)
        _check_error(result)
        return result.model_dump()

    @mcp.tool(description=_READ_FILE_DESCRIPTION)  # type: ignore[misc, untyped-decorator]
    def read_file(
        repo: Annotated[
            str,
            Field(description="Repository name with .git suffix (e.g., 'team/project.git')."),
        ],
        path: Annotated[
            str,
            Field(
                description="File path relative to root, no leading slash (e.g., 'src/main.py')."
            ),
        ],
        revision: Annotated[
            str | None,
            Field(
                description="Branch, tag, or commit SHA. Omit to use HEAD of default branch."
            ),
        ] = None,
        startLine: Annotated[
            int | None,
            Field(description="1-based starting line. Omit to start from line 1."),
        ] = None,
        endLine: Annotated[
            int | None,
            Field(description="1-based ending line (inclusive). Omit to read to end of file."),
        ] = None,
    ) -> dict[str, Any]:
        validate_repository(repo)
        result = gb_read_file(
            repo=repo,
            path=path,
            revision=revision,
            startLine=startLine,
            endLine=endLine,
        )
        _check_error(result)
        return result.model_dump()

    @mcp.tool(description=_FILE_SEARCH_DESCRIPTION)  # type: ignore[misc, untyped-decorator]
    def file_search(
        query: Annotated[
            str,
            Field(
                description="Lucene query for file contents. Supports phrases (\"foo\"), wildcards (foo*), AND/OR."
            ),
        ],
        repos: Annotated[
            list[str] | None,
            Field(
                description="Repository names to search. Omit to search all accessible repositories."
            ),
        ] = None,
        pathPattern: Annotated[
            str | None,
            Field(
                description="Glob pattern for file paths (e.g., '*.java', 'src/**/*.py'). Omit to search all files."
            ),
        ] = None,
        branch: Annotated[
            str | None,
            Field(
                description="Branch to search (e.g., 'refs/heads/main'). Omit to search default branch only."
            ),
        ] = None,
        limit: Annotated[
            int,
            Field(description="Maximum results. Default: 25, max: 100."),
        ] = 25,
        offset: Annotated[
            int,
            Field(description="Results to skip for pagination. Default: 0."),
        ] = 0,
        contextLines: Annotated[
            int,
            Field(description="Context lines around matches. Default: 10, max: 200."),
        ] = 10,
    ) -> dict[str, Any]:
        if repos:
            validate_repositories(repos)
        result = gb_file_search(
            query=query,
            repos=repos,
            pathPattern=pathPattern,
            branch=branch,
            limit=limit,
            offset=offset,
            contextLines=contextLines,
        )
        _check_error(result)
        return result.model_dump(exclude={"query"})

    @mcp.tool(description=_COMMIT_SEARCH_DESCRIPTION)  # type: ignore[misc, untyped-decorator]
    def commit_search(
        query: Annotated[
            str,
            Field(
                description="Lucene query for commit messages. Supports phrases (\"fix\"), wildcards (feat*), AND/OR."
            ),
        ],
        repos: Annotated[
            list[str],
            Field(description="Repository names to search. Required, at least one."),
        ],
        authors: Annotated[
            list[str] | None,
            Field(
                description="Filter by author names. Multiple authors use OR logic. Omit to include all authors."
            ),
        ] = None,
        branch: Annotated[
            str | None,
            Field(
                description="Branch to search (e.g., 'refs/heads/main'). Omit to search default branch only."
            ),
        ] = None,
        limit: Annotated[
            int,
            Field(description="Maximum results. Default: 25, max: 100."),
        ] = 25,
        offset: Annotated[
            int,
            Field(description="Results to skip for pagination. Default: 0."),
        ] = 0,
    ) -> dict[str, Any]:
        validate_repositories(repos)
        result = gb_commit_search(
            query=query,
            repos=repos,
            authors=authors,
            branch=branch,
            limit=limit,
            offset=offset,
        )
        _check_error(result)
        return result.model_dump(exclude={"query"})

    @mcp.tool(description=_FIND_FILES_DESCRIPTION)  # type: ignore[misc, untyped-decorator]
    def find_files(
        pathPattern: Annotated[
            str,
            Field(
                description="Glob pattern to match file paths (e.g., '*.java', '**/Dockerfile', 'src/**/test_*.py')."
            ),
        ],
        repos: Annotated[
            list[str] | None,
            Field(
                description="Repository names to search. Omit to search all accessible repositories."
            ),
        ] = None,
        revision: Annotated[
            str | None,
            Field(
                description="Branch, tag, or commit SHA. Omit to use HEAD of default branch."
            ),
        ] = None,
        limit: Annotated[
            int,
            Field(description="Maximum files to return. Default: 50, max: 200."),
        ] = 50,
        offset: Annotated[
            int,
            Field(description="Results to skip for pagination. Default: 0."),
        ] = 0,
    ) -> dict[str, Any]:
        if repos:
            validate_repositories(repos)
        result = gb_find_files(
            pathPattern=pathPattern,
            repos=repos,
            revision=revision,
            limit=limit,
            offset=offset,
        )
        _check_error(result)
        return result.model_dump()
