"""Real-world tests for repository suggestion algorithm.

These tests use the actual repository list from the Gitblit instance to verify
that the Levenshtein distance algorithm provides useful suggestions for common
mistakes an AI or user might make.

ALGORITHM DESIGN:
The algorithm compares only the repository name portion, ignoring:
- Namespace prefix (e.g., 'pvginkel/' is stripped)
- The '.git' suffix

This means 'zigbee.git' is compared against 'ZigbeeControl', 'ZigbeeConfiguration',
etc. rather than against full paths like 'pvginkel/ZigbeeControl.git'.

This approach works well because:
- Users typically guess project names, not full paths with namespaces
- Namespace differences would otherwise dominate the edit distance
- The semantic meaning is in the repo name, not the organizational structure
"""

import json
from pathlib import Path

import pytest
from gitblit_mcp_server.repo_validator import find_similar_repos, levenshtein_distance


@pytest.fixture
def real_repo_names() -> list[str]:
    """Load the real repository names from the fixture file."""
    fixture_path = Path(__file__).parent / "fixtures" / "repository_names.json"
    with open(fixture_path) as f:
        return json.load(f)


class TestRealWorldSuggestions:
    """Test the algorithm against real-world guesses."""

    def test_missing_namespace_electronics_inventory(self, real_repo_names: list[str]) -> None:
        """User forgets the namespace prefix."""
        # User tries just the project name without pvginkel/
        suggestions = find_similar_repos("ElectronicsInventory.git", real_repo_names)
        assert "pvginkel/ElectronicsInventory.git" in suggestions
        print(f"\n'ElectronicsInventory.git' -> {suggestions}")

    def test_hyphenated_name_electronics(self, real_repo_names: list[str]) -> None:
        """User uses hyphens instead of camelCase - the original problem case."""
        suggestions = find_similar_repos("electronics-inventory-app.git", real_repo_names)
        # At least one Electronics repo should be suggested
        electronics_repos = [r for r in suggestions if "Electronics" in r]
        assert len(electronics_repos) >= 1, f"Expected Electronics repos in {suggestions}"
        print(f"\n'electronics-inventory-app.git' -> {suggestions}")

    def test_missing_namespace_gitblit_mcp(self, real_repo_names: list[str]) -> None:
        """User forgets namespace for GitblitMCPServer."""
        suggestions = find_similar_repos("GitblitMCPServer.git", real_repo_names)
        assert "pvginkel/GitblitMCPServer.git" in suggestions
        print(f"\n'GitblitMCPServer.git' -> {suggestions}")

    def test_all_lowercase(self, real_repo_names: list[str]) -> None:
        """User types everything lowercase."""
        suggestions = find_similar_repos("homeassistantconfiguration.git", real_repo_names)
        assert "pvginkel/HomeAssistantConfiguration.git" in suggestions
        print(f"\n'homeassistantconfiguration.git' -> {suggestions}")

    def test_hyphenated_home_assistant(self, real_repo_names: list[str]) -> None:
        """User guesses with hyphens for Home Assistant.

        By comparing only repo names (ignoring namespace), 'home-assistant-config'
        matches well against 'HomeAssistantConfiguration'.
        """
        suggestions = find_similar_repos("home-assistant-config.git", real_repo_names)
        ha_repos = [r for r in suggestions if "HomeAssistant" in r]
        assert len(ha_repos) >= 1, f"Expected HomeAssistant repos in {suggestions}"
        print(f"\n'home-assistant-config.git' -> {suggestions}")

    def test_abbreviated_docker(self, real_repo_names: list[str]) -> None:
        """User abbreviates DockerImages."""
        suggestions = find_similar_repos("pvginkel/DockerImgs.git", real_repo_names)
        assert "pvginkel/DockerImages.git" in suggestions
        print(f"\n'pvginkel/DockerImgs.git' -> {suggestions}")

    def test_typo_thermostat(self, real_repo_names: list[str]) -> None:
        """User makes a typo in ThermostatProxy."""
        suggestions = find_similar_repos("pvginkel/ThermostatPrxy.git", real_repo_names)
        assert "pvginkel/ThermostatProxy.git" in suggestions
        print(f"\n'pvginkel/ThermostatPrxy.git' -> {suggestions}")

    def test_partial_name_zigbee(self, real_repo_names: list[str]) -> None:
        """User types a partial name 'ZigbeeCtrl' hoping for ZigbeeControl.

        Short partial names like 'zigbee' alone still struggle because the
        edit distance to 'ZigbeeControl' (7 extra chars) is similar to other
        short repo names. But closer guesses work well.
        """
        suggestions = find_similar_repos("pvginkel/ZigbeeCtrl.git", real_repo_names)
        zigbee_repos = [r for r in suggestions if "Zigbee" in r]
        assert len(zigbee_repos) >= 1, f"Expected Zigbee repos in {suggestions}"
        print(f"\n'pvginkel/ZigbeeCtrl.git' -> {suggestions}")

    def test_generic_recipes(self, real_repo_names: list[str]) -> None:
        """User guesses 'RecipeServer' instead of 'RecipesServer'.

        Close guesses work well now that we compare only repo names.
        """
        suggestions = find_similar_repos("RecipeServer.git", real_repo_names)
        recipes_repos = [r for r in suggestions if "Recipe" in r]
        assert len(recipes_repos) >= 1, f"Expected Recipe repos in {suggestions}"
        print(f"\n'RecipeServer.git' -> {suggestions}")

    def test_wrong_case_netide(self, real_repo_names: list[str]) -> None:
        """User uses wrong case for netide namespace."""
        suggestions = find_similar_repos("NetIDE/netide.git", real_repo_names)
        assert "netide/netide.git" in suggestions
        print(f"\n'NetIDE/netide.git' -> {suggestions}")

    def test_similar_project_names_pdf(self, real_repo_names: list[str]) -> None:
        """User confuses PDF-related project names."""
        suggestions = find_similar_repos("pvginkel/PdfReader.git", real_repo_names)
        pdf_repos = [r for r in suggestions if "Pdf" in r]
        assert len(pdf_repos) >= 1, f"Expected PDF repos in {suggestions}"
        print(f"\n'pvginkel/PdfReader.git' -> {suggestions}")

    def test_scan_pdf_typo(self, real_repo_names: list[str]) -> None:
        """User types ScanPdf instead of ScanToPdf."""
        suggestions = find_similar_repos("pvginkel/ScanPdf.git", real_repo_names)
        assert "pvginkel/ScanToPdf.git" in suggestions
        print(f"\n'pvginkel/ScanPdf.git' -> {suggestions}")

    def test_iot_abbreviation(self, real_repo_names: list[str]) -> None:
        """User types IoT without proper casing."""
        suggestions = find_similar_repos("pvginkel/iotsupport.git", real_repo_names)
        assert "pvginkel/IoTSupport.git" in suggestions
        print(f"\n'pvginkel/iotsupport.git' -> {suggestions}")

    def test_finances_without_version(self, real_repo_names: list[str]) -> None:
        """User guesses Finances without version suffix."""
        suggestions = find_similar_repos("pvginkel/Finances.git", real_repo_names)
        # This should be an exact match
        assert "pvginkel/Finances.git" in suggestions
        print(f"\n'pvginkel/Finances.git' -> {suggestions}")

    def test_tql_wrong_namespace(self, real_repo_names: list[str]) -> None:
        """User puts TQL in wrong namespace.

        By ignoring namespace, 'pvginkel/TQL.git' compares 'TQL' against 'TQL'
        and finds 'TQLApp/TQL.git' as an exact match.
        """
        suggestions = find_similar_repos("pvginkel/TQL.git", real_repo_names)
        assert "TQLApp/TQL.git" in suggestions
        print(f"\n'pvginkel/TQL.git' -> {suggestions}")

    def test_rust_js_without_namespace(self, real_repo_names: list[str]) -> None:
        """User forgets rust-js namespace."""
        suggestions = find_similar_repos("rjs.git", real_repo_names)
        # Should suggest both pvginkel/rjs.git and rust-js/rjs.git
        rjs_repos = [r for r in suggestions if "rjs" in r.lower()]
        assert len(rjs_repos) >= 1, f"Expected rjs repos in {suggestions}"
        print(f"\n'rjs.git' -> {suggestions}")


class TestLevenshteinDistanceRealWorld:
    """Test Levenshtein distances for real repository names."""

    def test_distance_electronics_variations(self) -> None:
        """Check distances for electronics inventory variations."""
        target = "pvginkel/electronicsinventory.git"
        actual = "pvginkel/ElectronicsInventory.git"

        # Case difference only - should have small distance
        dist = levenshtein_distance(target, actual.lower())
        assert dist == 0, "Lowercase comparison should match"

        # With hyphens
        hyphenated = "electronics-inventory-app.git"
        dist_hyphen = levenshtein_distance(hyphenated.lower(), actual.lower())
        print(f"\nDistance '{hyphenated}' to '{actual}': {dist_hyphen}")

    def test_distance_comparison_for_suggestions(self, real_repo_names: list[str]) -> None:
        """Verify that closer matches have smaller distances."""
        guess = "electronics-inventory.git"

        # Calculate distances to various repos
        distances = []
        for repo in real_repo_names:
            dist = levenshtein_distance(guess.lower(), repo.lower())
            distances.append((dist, repo))

        # Sort and show top 10
        distances.sort(key=lambda x: x[0])
        print(f"\nTop 10 closest to '{guess}':")
        for dist, repo in distances[:10]:
            print(f"  {dist}: {repo}")

        # The Electronics repos should be in the top results
        top_10_repos = [r for _, r in distances[:10]]
        electronics_in_top_10 = any("Electronics" in r for r in top_10_repos)
        assert electronics_in_top_10, "Electronics repos should be in top 10"


class TestEdgeCases:
    """Test edge cases with real repository data."""

    def test_very_short_guess(self, real_repo_names: list[str]) -> None:
        """User types a very short guess."""
        suggestions = find_similar_repos("go.git", real_repo_names)
        assert "pvginkel/Go.git" in suggestions
        print(f"\n'go.git' -> {suggestions}")

    def test_with_git_extension_missing(self, real_repo_names: list[str]) -> None:
        """User forgets .git extension."""
        suggestions = find_similar_repos("pvginkel/DockerImages", real_repo_names)
        # Should still find a close match
        docker_repos = [r for r in suggestions if "Docker" in r]
        assert len(docker_repos) >= 1
        print(f"\n'pvginkel/DockerImages' (no .git) -> {suggestions}")

    def test_completely_wrong_guess(self, real_repo_names: list[str]) -> None:
        """Completely wrong guesses return no suggestions (threshold filters them)."""
        suggestions = find_similar_repos("totally-nonexistent-project.git", real_repo_names)
        # With the 60% threshold, completely unrelated repos are filtered out
        # This is better than suggesting random repos like DokProject
        assert len(suggestions) == 0
        print(f"\n'totally-nonexistent-project.git' -> {suggestions} (correctly empty)")

    def test_special_characters_in_name(self, real_repo_names: list[str]) -> None:
        """Test repos with special characters like dots and hyphens."""
        suggestions = find_similar_repos("NHibernate.OData.git", real_repo_names)
        assert "pvginkel/NHibernate.OData.git" in suggestions
        print(f"\n'NHibernate.OData.git' -> {suggestions}")
