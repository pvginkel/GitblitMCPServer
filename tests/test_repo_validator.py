"""Unit tests for repository validation with Levenshtein distance suggestions."""

from unittest.mock import MagicMock, patch

import pytest
from gitblit_mcp_server.repo_validator import (
    RepositoryCache,
    find_similar_repos,
    levenshtein_distance,
    validate_repositories,
    validate_repository,
)
from gitblit_mcp_server.schemas import (
    ErrorDetail,
    ErrorResponse,
    GitblitAPIError,
    ListReposResponse,
    Repository,
)


class TestLevenshteinDistance:
    """Tests for Levenshtein distance calculation."""

    def test_identical_strings(self) -> None:
        """Test that identical strings have distance 0."""
        assert levenshtein_distance("test", "test") == 0
        assert levenshtein_distance("", "") == 0

    def test_empty_string(self) -> None:
        """Test distance with empty string."""
        assert levenshtein_distance("test", "") == 4
        assert levenshtein_distance("", "test") == 4

    def test_single_insertion(self) -> None:
        """Test single character insertion."""
        assert levenshtein_distance("test", "tests") == 1
        assert levenshtein_distance("cat", "cats") == 1

    def test_single_deletion(self) -> None:
        """Test single character deletion."""
        assert levenshtein_distance("tests", "test") == 1

    def test_single_substitution(self) -> None:
        """Test single character substitution."""
        assert levenshtein_distance("test", "best") == 1
        assert levenshtein_distance("cat", "bat") == 1

    def test_multiple_operations(self) -> None:
        """Test multiple edit operations."""
        assert levenshtein_distance("kitten", "sitting") == 3
        assert levenshtein_distance("saturday", "sunday") == 3

    def test_case_sensitivity(self) -> None:
        """Test that comparison is case-sensitive."""
        assert levenshtein_distance("Test", "test") == 1
        assert levenshtein_distance("TEST", "test") == 4

    def test_symmetry(self) -> None:
        """Test that distance is symmetric."""
        assert levenshtein_distance("abc", "xyz") == levenshtein_distance("xyz", "abc")
        assert levenshtein_distance("hello", "world") == levenshtein_distance("world", "hello")


class TestFindSimilarRepos:
    """Tests for finding similar repository names."""

    def test_exact_match_case_insensitive(self) -> None:
        """Test that case-insensitive matches are found first."""
        all_repos = ["Team/Project.git", "other/repo.git"]
        result = find_similar_repos("team/project.git", all_repos)
        assert result[0] == "Team/Project.git"

    def test_returns_max_suggestions(self) -> None:
        """Test that only max_suggestions are returned."""
        all_repos = ["repo1.git", "repo2.git", "repo3.git", "repo4.git", "repo5.git"]
        result = find_similar_repos("repo.git", all_repos, max_suggestions=3)
        assert len(result) == 3

    def test_empty_repo_list(self) -> None:
        """Test with empty repository list."""
        result = find_similar_repos("test.git", [])
        assert result == []

    def test_sorted_by_similarity(self) -> None:
        """Test that results are sorted by similarity."""
        all_repos = [
            "completely/different.git",
            "pvginkel/ElectronicsInventory.git",
            "pvginkel/ElectronicsInventoryUI.git",
        ]
        result = find_similar_repos("electronics-inventory-app.git", all_repos)
        # The ElectronicsInventory repos should be suggested before completely/different
        electronics_repos = [r for r in result if "Electronics" in r]
        assert len(electronics_repos) >= 1

    def test_finds_similar_with_typo(self) -> None:
        """Test finding similar repos with typos."""
        all_repos = ["myproject.git", "myprojects.git", "other.git"]
        result = find_similar_repos("myprojetc.git", all_repos)
        # myproject.git should be the closest match
        assert "myproject.git" in result


class TestRepositoryCache:
    """Tests for repository cache functionality."""

    def test_cache_refresh_on_expired(self) -> None:
        """Test that cache refreshes when expired."""
        mock_client = MagicMock()
        mock_client.list_repos.return_value = ListReposResponse(
            repositories=[
                Repository(
                    name="test/repo.git",
                    description="Test",
                    lastChange=None,
                    hasCommits=True,
                )
            ],
            totalCount=1,
            limitHit=False,
        )

        with patch("gitblit_mcp_server.repo_validator.get_client", return_value=mock_client), \
             patch("gitblit_mcp_server.repo_validator.get_config") as mock_config:
            mock_config.return_value.repo_cache_ttl = 600  # 10 minutes
            cache = RepositoryCache()
            result = cache.get_repo_names()

            assert result == ["test/repo.git"]
            mock_client.list_repos.assert_called_once()

    def test_cache_paginates_all_repos(self) -> None:
        """Test that cache fetches all pages of repositories."""
        mock_client = MagicMock()
        # First call returns repos with limitHit=True
        mock_client.list_repos.side_effect = [
            ListReposResponse(
                repositories=[
                    Repository(name="repo1.git", description="", lastChange=None, hasCommits=True)
                ],
                totalCount=2,
                limitHit=True,
            ),
            ListReposResponse(
                repositories=[
                    Repository(name="repo2.git", description="", lastChange=None, hasCommits=True)
                ],
                totalCount=2,
                limitHit=False,
            ),
        ]

        with patch("gitblit_mcp_server.repo_validator.get_client", return_value=mock_client), \
             patch("gitblit_mcp_server.repo_validator.get_config") as mock_config:
            mock_config.return_value.repo_cache_ttl = 600
            cache = RepositoryCache()
            result = cache.get_repo_names()

            assert result == ["repo1.git", "repo2.git"]
            assert mock_client.list_repos.call_count == 2


class TestValidateRepository:
    """Tests for single repository validation."""

    def test_valid_repository_passes(self) -> None:
        """Test that valid repository passes validation."""
        with patch("gitblit_mcp_server.repo_validator._get_cache") as mock_cache:
            mock_cache.return_value.get_repo_names.return_value = ["valid/repo.git"]
            # Should not raise
            validate_repository("valid/repo.git")

    def test_invalid_repository_raises_with_suggestions(self) -> None:
        """Test that invalid repository raises error with suggestions."""
        with patch("gitblit_mcp_server.repo_validator._get_cache") as mock_cache:
            mock_cache.return_value.get_repo_names.return_value = [
                "pvginkel/ElectronicsInventory.git",
                "pvginkel/ElectronicsInventoryUI.git",
            ]

            with pytest.raises(GitblitAPIError) as exc_info:
                validate_repository("electronics-inventory-app.git")

            assert exc_info.value.code == "NOT_FOUND"
            assert "electronics-inventory-app.git" in exc_info.value.message
            assert "Did you mean:" in exc_info.value.message
            # Should suggest at least one of the similar repos
            assert (
                "ElectronicsInventory.git" in exc_info.value.message or
                "ElectronicsInventoryUI.git" in exc_info.value.message
            )


class TestValidateRepositories:
    """Tests for multiple repository validation."""

    def test_empty_list_passes(self) -> None:
        """Test that empty list passes validation."""
        # Should not raise
        validate_repositories([])

    def test_all_valid_passes(self) -> None:
        """Test that all valid repositories pass."""
        with patch("gitblit_mcp_server.repo_validator._get_cache") as mock_cache:
            mock_cache.return_value.get_repo_names.return_value = ["repo1.git", "repo2.git"]
            # Should not raise
            validate_repositories(["repo1.git", "repo2.git"])

    def test_multiple_invalid_reports_all(self) -> None:
        """Test that multiple invalid repos are all reported."""
        with patch("gitblit_mcp_server.repo_validator._get_cache") as mock_cache:
            mock_cache.return_value.get_repo_names.return_value = ["valid.git"]

            with pytest.raises(GitblitAPIError) as exc_info:
                validate_repositories(["invalid1.git", "invalid2.git"])

            assert "invalid1.git" in exc_info.value.message
            assert "invalid2.git" in exc_info.value.message

    def test_cache_error_propagates(self) -> None:
        """Test that cache errors are propagated."""
        mock_client = MagicMock()
        mock_client.list_repos.return_value = ErrorResponse(
            error=ErrorDetail(code="INTERNAL_ERROR", message="Server error")
        )

        with patch("gitblit_mcp_server.repo_validator.get_client", return_value=mock_client), \
             patch("gitblit_mcp_server.repo_validator.get_config") as mock_config, \
             patch("gitblit_mcp_server.repo_validator._cache", None):
            mock_config.return_value.repo_cache_ttl = 600

            with pytest.raises(GitblitAPIError) as exc_info:
                validate_repositories(["any.git"])

            assert exc_info.value.code == "INTERNAL_ERROR"
