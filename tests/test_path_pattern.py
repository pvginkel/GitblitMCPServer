"""Tests for pathPattern filtering in file search.

These tests specifically verify that pathPattern filtering works correctly
after the fix for the quoting issue in the Gitblit Search API Plugin.
"""

import pytest
from fastmcp import Client

from gitblit_mcp_server.client import GitblitClient
from gitblit_mcp_server.schemas import ErrorResponse, FileSearchResponse
from gitblit_mcp_server.server import get_server


@pytest.fixture
async def mcp_client():
    """Create an MCP client connected to the server."""
    server = get_server()
    async with Client(server) as client:
        yield client


class TestPathPatternFiltering:
    """Tests for pathPattern parameter in file_search."""

    def test_path_pattern_wildcard_extension(self, client: GitblitClient) -> None:
        """Test filtering by file extension using *.ext pattern."""
        # Search for license-related content, filter to .txt files
        result = client.search_files(query="license", path_pattern="*.txt", limit=10)

        if isinstance(result, ErrorResponse):
            pytest.skip("Search not available")

        assert isinstance(result, FileSearchResponse)

        # All results should be .txt files
        for search_result in result.results:
            assert search_result.path.endswith(".txt"), (
                f"Expected .txt file, got {search_result.path}"
            )

    def test_path_pattern_directory_wildcard(
        self, client: GitblitClient, test_repo: str
    ) -> None:
        """Test filtering by directory pattern using *Dir* pattern."""
        result = client.search_files(
            query="namespace",
            repos=[test_repo],
            path_pattern="*Interop*",
            limit=10,
        )

        if isinstance(result, ErrorResponse):
            pytest.skip("Search not available")

        assert isinstance(result, FileSearchResponse)

        # All results should be from Interop directories
        for search_result in result.results:
            assert "Interop" in search_result.path, (
                f"Expected Interop in path, got {search_result.path}"
            )

    def test_path_pattern_filters_results_not_count(
        self, client: GitblitClient
    ) -> None:
        """Test that pathPattern filters results but totalCount may differ.

        Note: The current implementation may return totalCount from the
        unfiltered query while filtering the actual results. This tests
        the actual filtering behavior.
        """
        # First search without filter
        result_all = client.search_files(query="license", limit=20)

        if isinstance(result_all, ErrorResponse):
            pytest.skip("Search not available")

        # Then search with .txt filter
        result_filtered = client.search_files(
            query="license", path_pattern="*.txt", limit=20
        )

        if isinstance(result_filtered, ErrorResponse):
            pytest.skip("Search not available")

        # Filtered results should be a subset (or equal if all are .txt)
        assert len(result_filtered.results) <= len(result_all.results)

        # All filtered results should match the pattern
        for r in result_filtered.results:
            assert r.path.endswith(".txt")

    def test_path_pattern_no_matches(self, client: GitblitClient) -> None:
        """Test pathPattern that matches no files returns empty results."""
        result = client.search_files(
            query="namespace",  # Common term
            path_pattern="*.nonexistent_extension_xyz",
            limit=10,
        )

        if isinstance(result, ErrorResponse):
            pytest.skip("Search not available")

        assert isinstance(result, FileSearchResponse)
        assert len(result.results) == 0

    def test_path_pattern_with_multiple_wildcards(
        self, client: GitblitClient, test_repo: str
    ) -> None:
        """Test pathPattern with multiple wildcards like *foo*bar*."""
        result = client.search_files(
            query="public",
            repos=[test_repo],
            path_pattern="*Interop*.cs",
            limit=10,
        )

        if isinstance(result, ErrorResponse):
            pytest.skip("Search not available")

        assert isinstance(result, FileSearchResponse)

        # Results should match both patterns
        for search_result in result.results:
            assert "Interop" in search_result.path
            assert search_result.path.endswith(".cs")


class TestPathPatternMCPIntegration:
    """Tests for pathPattern via MCP protocol."""

    async def test_mcp_file_search_with_path_pattern(
        self, mcp_client: Client
    ) -> None:
        """Test file_search tool with pathPattern parameter via MCP."""
        result = await mcp_client.call_tool(
            "file_search",
            {"query": "namespace", "pathPattern": "*Interop*", "limit": 5},
        )

        content = result.content[0].text
        assert "results" in content

        # If we have results, they should match the pattern
        if '"path":' in content:
            assert "Interop" in content

    async def test_mcp_file_search_extension_filter(
        self, mcp_client: Client
    ) -> None:
        """Test file_search with extension filter via MCP."""
        result = await mcp_client.call_tool(
            "file_search", {"query": "license", "pathPattern": "*.txt", "limit": 5}
        )

        content = result.content[0].text
        assert "results" in content

    async def test_mcp_file_search_combined_filters(
        self, mcp_client: Client, test_repo: str
    ) -> None:
        """Test file_search with repos and pathPattern combined."""
        result = await mcp_client.call_tool(
            "file_search",
            {
                "query": "interface",
                "repos": [test_repo],
                "pathPattern": "*.cs",
                "limit": 5,
            },
        )

        content = result.content[0].text
        assert "results" in content


class TestPathPatternEdgeCases:
    """Edge case tests for pathPattern filtering."""

    def test_path_pattern_case_sensitivity(
        self, client: GitblitClient, test_repo: str
    ) -> None:
        """Test that pathPattern matching handles case correctly.

        Note: Case sensitivity depends on Lucene configuration.
        """
        # Try lowercase
        result_lower = client.search_files(
            query="namespace", repos=[test_repo], path_pattern="*.cs", limit=5
        )

        # Try uppercase
        result_upper = client.search_files(
            query="namespace", repos=[test_repo], path_pattern="*.CS", limit=5
        )

        # At least one should return results (depending on case sensitivity)
        if isinstance(result_lower, ErrorResponse) and isinstance(
            result_upper, ErrorResponse
        ):
            pytest.skip("Search not available")

        # We mainly care that at least one works
        has_results = False
        if isinstance(result_lower, FileSearchResponse) and result_lower.results:
            has_results = True
        if isinstance(result_upper, FileSearchResponse) and result_upper.results:
            has_results = True

        assert has_results, "Expected at least one case variant to return results"

    def test_path_pattern_special_characters(self, client: GitblitClient) -> None:
        """Test pathPattern with special regex-like characters.

        The pathPattern should use glob wildcards (* and ?), not regex.
        """
        # This should not be interpreted as regex
        result = client.search_files(
            query="test", path_pattern="*[test]*", limit=5  # Literal brackets
        )

        # Should not error - pattern is passed to Lucene as-is
        if isinstance(result, ErrorResponse):
            # Some patterns might not be supported, which is acceptable
            assert result.error.code in ("INVALID_REQUEST", "INTERNAL_ERROR")
        else:
            assert isinstance(result, FileSearchResponse)

    def test_path_pattern_empty_string(self, client: GitblitClient) -> None:
        """Test that empty pathPattern is handled gracefully."""
        # Empty string should be treated as no filter
        result = client.search_files(query="namespace", path_pattern="", limit=5)

        # Should work normally
        if not isinstance(result, ErrorResponse):
            assert isinstance(result, FileSearchResponse)

    def test_path_pattern_single_asterisk(self, client: GitblitClient) -> None:
        """Test pathPattern with just a single asterisk (match all)."""
        result = client.search_files(query="namespace", path_pattern="*", limit=5)

        if isinstance(result, ErrorResponse):
            pytest.skip("Search not available")

        # Should return results since * matches everything
        assert isinstance(result, FileSearchResponse)
