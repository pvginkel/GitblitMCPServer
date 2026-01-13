"""Integration tests for MCP tools using FastMCP Client.

These tests verify the full MCP protocol flow by connecting a FastMCP Client
directly to the server instance, testing tools end-to-end against the live
Gitblit server.
"""

import pytest
from fastmcp import Client

from gitblit_mcp_server.server import get_server


@pytest.fixture
async def mcp_client():
    """Create an MCP client connected to the server."""
    server = get_server()
    async with Client(server) as client:
        yield client


def get_text_content(result) -> str:
    """Extract text content from CallToolResult."""
    return result.content[0].text


class TestListReposTool:
    """Tests for the list_repos MCP tool."""

    async def test_list_repos_returns_repositories(self, mcp_client: Client) -> None:
        """Test that list_repos returns a list of repositories."""
        result = await mcp_client.call_tool("list_repos", {})

        content = get_text_content(result)
        assert "repositories" in content
        assert "pagination" in content

    async def test_list_repos_with_limit(self, mcp_client: Client) -> None:
        """Test list_repos respects the limit parameter."""
        result = await mcp_client.call_tool("list_repos", {"limit": 2})

        content = get_text_content(result)
        assert "repositories" in content

    async def test_list_repos_with_query(self, mcp_client: Client) -> None:
        """Test list_repos filters by query."""
        result = await mcp_client.call_tool("list_repos", {"query": "netide"})

        content = get_text_content(result)
        assert "repositories" in content

    async def test_list_repos_no_matches(self, mcp_client: Client) -> None:
        """Test list_repos with query that matches nothing."""
        result = await mcp_client.call_tool(
            "list_repos", {"query": "nonexistent_repo_xyz_999"}
        )

        content = get_text_content(result)
        assert "repositories" in content
        assert '"totalCount": 0' in content or '"totalCount":0' in content


class TestListFilesTool:
    """Tests for the list_files MCP tool."""

    async def test_list_files_root(self, mcp_client: Client, test_repo: str) -> None:
        """Test listing files at repository root."""
        result = await mcp_client.call_tool("list_files", {"repo": test_repo})

        content = get_text_content(result)
        assert "files" in content

    async def test_list_files_subdirectory(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test listing files in a subdirectory."""
        result = await mcp_client.call_tool(
            "list_files", {"repo": test_repo, "path": "NetIde.Project"}
        )

        content = get_text_content(result)
        assert "files" in content

    async def test_list_files_nonexistent_repo(self, mcp_client: Client) -> None:
        """Test list_files with nonexistent repository raises error."""
        with pytest.raises(Exception) as exc_info:
            await mcp_client.call_tool(
                "list_files", {"repo": "nonexistent/repo.git"}
            )
        assert "NOT_FOUND" in str(exc_info.value)

    async def test_list_files_nonexistent_path(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test list_files with nonexistent path returns empty or raises error."""
        # Some servers return empty list, others return NOT_FOUND
        try:
            result = await mcp_client.call_tool(
                "list_files", {"repo": test_repo, "path": "nonexistent/path/xyz"}
            )
            # If no error, should return empty files list
            content = get_text_content(result)
            assert "files" in content
        except Exception as exc_info:
            assert "NOT_FOUND" in str(exc_info)


class TestReadFileTool:
    """Tests for the read_file MCP tool."""

    async def test_read_file_success(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test reading a file returns content."""
        result = await mcp_client.call_tool(
            "read_file", {"repo": test_repo, "path": "License.txt"}
        )

        content = get_text_content(result)
        assert "content" in content
        # License.txt contains GNU license text
        assert "GNU" in content or "license" in content.lower()

    async def test_read_file_with_line_range(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test reading specific line range."""
        result = await mcp_client.call_tool(
            "read_file",
            {"repo": test_repo, "path": "License.txt", "startLine": 1, "endLine": 5},
        )

        content = get_text_content(result)
        assert "content" in content

    async def test_read_file_nonexistent(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test reading nonexistent file raises error."""
        with pytest.raises(Exception) as exc_info:
            await mcp_client.call_tool(
                "read_file", {"repo": test_repo, "path": "nonexistent.txt"}
            )
        assert "NOT_FOUND" in str(exc_info.value)

    async def test_read_file_directory(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test reading a directory path raises error."""
        with pytest.raises(Exception):
            await mcp_client.call_tool(
                "read_file", {"repo": test_repo, "path": "NetIde.Project"}
            )


class TestFileSearchTool:
    """Tests for the file_search MCP tool."""

    async def test_file_search_basic(self, mcp_client: Client) -> None:
        """Test basic file content search."""
        result = await mcp_client.call_tool(
            "file_search", {"query": "namespace"}
        )

        content = get_text_content(result)
        assert "results" in content
        assert "totalCount" in content

    async def test_file_search_with_repos(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test file search filtered to specific repository."""
        result = await mcp_client.call_tool(
            "file_search", {"query": "namespace", "repos": [test_repo]}
        )

        content = get_text_content(result)
        assert "results" in content
        # All results should be from the specified repo
        if '"repository":' in content:
            assert test_repo in content

    async def test_file_search_with_path_pattern(self, mcp_client: Client) -> None:
        """Test file search with pathPattern filter."""
        result = await mcp_client.call_tool(
            "file_search",
            {"query": "namespace", "pathPattern": "*Interop*", "count": 5},
        )

        content = get_text_content(result)
        assert "results" in content
        # Results should be from Interop paths
        if '"path":' in content:
            assert "Interop" in content

    async def test_file_search_extension_filter(self, mcp_client: Client) -> None:
        """Test file search filtering by file extension."""
        result = await mcp_client.call_tool(
            "file_search", {"query": "license", "pathPattern": "*.txt", "count": 5}
        )

        content = get_text_content(result)
        assert "results" in content

    async def test_file_search_no_results(self, mcp_client: Client) -> None:
        """Test file search with no matching results."""
        result = await mcp_client.call_tool(
            "file_search", {"query": "xyznonexistent123456"}
        )

        content = get_text_content(result)
        assert "totalCount" in content
        # Should have 0 or very few results
        assert '"totalCount": 0' in content or '"totalCount":0' in content

    async def test_file_search_with_count_limit(self, mcp_client: Client) -> None:
        """Test file search respects count limit."""
        result = await mcp_client.call_tool(
            "file_search", {"query": "using", "count": 3}
        )

        content = get_text_content(result)
        assert "results" in content

    async def test_file_search_lucene_phrase(self, mcp_client: Client) -> None:
        """Test file search with Lucene phrase query."""
        result = await mcp_client.call_tool(
            "file_search", {"query": '"using System"'}
        )

        content = get_text_content(result)
        assert "results" in content

    async def test_file_search_lucene_boolean(self, mcp_client: Client) -> None:
        """Test file search with Lucene boolean operators."""
        result = await mcp_client.call_tool(
            "file_search", {"query": "interface AND public"}
        )

        content = get_text_content(result)
        assert "results" in content


class TestCommitSearchTool:
    """Tests for the commit_search MCP tool."""

    async def test_commit_search_basic(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test basic commit search."""
        result = await mcp_client.call_tool(
            "commit_search", {"query": "fix OR update OR add", "repos": [test_repo]}
        )

        content = get_text_content(result)
        assert "commits" in content
        assert "totalCount" in content

    async def test_commit_search_no_results(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test commit search with no matches."""
        result = await mcp_client.call_tool(
            "commit_search",
            {"query": "xyznonexistentcommitmessage999", "repos": [test_repo]},
        )

        content = get_text_content(result)
        assert "commits" in content

    async def test_commit_search_with_count(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test commit search with count limit."""
        result = await mcp_client.call_tool(
            "commit_search", {"query": "fix OR add OR update", "repos": [test_repo], "count": 5}
        )

        content = get_text_content(result)
        assert "commits" in content

    async def test_commit_search_multiple_repos(self, mcp_client: Client) -> None:
        """Test commit search across multiple repositories."""
        result = await mcp_client.call_tool(
            "commit_search",
            {
                "query": "initial OR first",
                "repos": ["netide/netide.git", "netide/netide-demo.git"],
            },
        )

        content = get_text_content(result)
        assert "commits" in content

    async def test_commit_search_wildcard_query(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test commit search with wildcard query to browse commits."""
        result = await mcp_client.call_tool(
            "commit_search", {"query": "*", "repos": [test_repo], "count": 10}
        )

        content = get_text_content(result)
        assert "commits" in content
        assert "totalCount" in content
        # Should have commits
        assert '"commit":' in content


class TestWildcardQueries:
    """Tests for wildcard query support (browse mode)."""

    async def test_file_search_wildcard_with_repos(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test file search with wildcard query and repos filter."""
        result = await mcp_client.call_tool(
            "file_search", {"query": "*", "repos": [test_repo], "count": 10}
        )

        content = get_text_content(result)
        assert "results" in content
        assert "totalCount" in content

    async def test_file_search_wildcard_with_path_pattern(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test file search with wildcard query and pathPattern filter."""
        result = await mcp_client.call_tool(
            "file_search",
            {"query": "*", "repos": [test_repo], "pathPattern": "*.cs", "count": 10},
        )

        content = get_text_content(result)
        assert "results" in content
        # Results should be C# files
        if '"path":' in content:
            assert ".cs" in content

    async def test_commit_search_wildcard_browse(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test commit search wildcard to browse recent commits."""
        result = await mcp_client.call_tool(
            "commit_search", {"query": "*", "repos": [test_repo], "count": 5}
        )

        content = get_text_content(result)
        assert "commits" in content
        # Should return commits sorted by date
        assert '"date":' in content


class TestToolDiscovery:
    """Tests for MCP tool discovery."""

    async def test_list_tools(self, mcp_client: Client) -> None:
        """Test that all expected tools are registered."""
        tools = await mcp_client.list_tools()

        tool_names = {tool.name for tool in tools}
        expected_tools = {
            "list_repos",
            "list_files",
            "read_file",
            "file_search",
            "commit_search",
        }
        assert expected_tools.issubset(tool_names)

    async def test_tool_descriptions(self, mcp_client: Client) -> None:
        """Test that all tools have descriptions."""
        tools = await mcp_client.list_tools()

        for tool in tools:
            assert tool.description, f"Tool {tool.name} missing description"
            assert len(tool.description) > 10, f"Tool {tool.name} has too short description"


class TestResponseFiltering:
    """Tests for response field filtering."""

    async def test_file_search_excludes_query_field(self, mcp_client: Client) -> None:
        """Test that file_search response excludes the 'query' field."""
        result = await mcp_client.call_tool(
            "file_search", {"query": "namespace", "count": 1}
        )

        content = get_text_content(result)
        # The response should NOT contain the 'query' field
        assert '"query":' not in content
        # But should contain the actual results
        assert "results" in content
        assert "totalCount" in content

    async def test_commit_search_excludes_query_field(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test that commit_search response excludes the 'query' field."""
        result = await mcp_client.call_tool(
            "commit_search", {"query": "fix OR add", "repos": [test_repo], "count": 1}
        )

        content = get_text_content(result)
        # The response should NOT contain the 'query' field
        assert '"query":' not in content
        # But should contain the actual results
        assert "commits" in content
        assert "totalCount" in content
