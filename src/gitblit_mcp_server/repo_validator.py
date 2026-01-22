"""Repository validation with suggestions based on Levenshtein distance."""

import time

from .client import get_client
from .config import get_config
from .schemas import ErrorResponse, GitblitAPIError


class RepositoryCache:
    """Cache for repository names with TTL."""

    def __init__(self) -> None:
        self._repo_names: list[str] = []
        self._last_refresh: float = 0.0

    def _is_expired(self) -> bool:
        """Check if the cache has expired."""
        ttl = get_config().repo_cache_ttl
        return time.time() - self._last_refresh > ttl

    def _refresh(self) -> None:
        """Refresh the cache by fetching all repository names."""
        client = get_client()
        all_repos: list[str] = []
        offset = 0
        limit = 100

        while True:
            result = client.list_repos(limit=limit, offset=offset)
            if isinstance(result, ErrorResponse):
                raise GitblitAPIError(result.error.code, result.error.message)

            for repo in result.repositories:
                all_repos.append(repo.name)

            if not result.limitHit:
                break
            offset += limit

        self._repo_names = all_repos
        self._last_refresh = time.time()

    def get_repo_names(self) -> list[str]:
        """Get the list of repository names, refreshing if needed."""
        if self._is_expired():
            self._refresh()
        return self._repo_names


# Singleton cache instance
_cache: RepositoryCache | None = None


def _get_cache() -> RepositoryCache:
    """Get or create the repository cache instance."""
    global _cache
    if _cache is None:
        _cache = RepositoryCache()
    return _cache


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings.

    Uses dynamic programming with O(min(m,n)) space complexity.
    """
    # Make s1 the shorter string to minimize space usage
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    m, n = len(s1), len(s2)

    # Previous and current row of distances
    prev_row = list(range(m + 1))
    curr_row = [0] * (m + 1)

    for j in range(1, n + 1):
        curr_row[0] = j
        for i in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                curr_row[i] = prev_row[i - 1]
            else:
                curr_row[i] = 1 + min(prev_row[i - 1], prev_row[i], curr_row[i - 1])
        prev_row, curr_row = curr_row, prev_row

    return prev_row[m]


def _extract_repo_name(full_path: str) -> str:
    """Extract the repository name without namespace and .git suffix.

    Examples:
        'pvginkel/ElectronicsInventory.git' -> 'electronicsinventory'
        'netide/netide-demo.git' -> 'netide-demo'
        'TQL.git' -> 'tql'
    """
    # Get the part after the last slash (or the whole string if no slash)
    name = full_path.rsplit("/", 1)[-1]
    # Remove .git suffix if present
    if name.endswith(".git"):
        name = name[:-4]
    # Lowercase for comparison
    return name.lower()


def find_similar_repos(
    invalid_repo: str,
    all_repos: list[str],
    max_suggestions: int = 3,
    max_relative_distance: float = 0.6,
) -> list[str]:
    """Find the most similar repository names using Levenshtein distance.

    Compares only the repository name portion (ignoring namespace and .git suffix)
    to provide better semantic matching. For example, 'zigbee.git' will match
    'pvginkel/ZigbeeControl.git' based on comparing 'zigbee' to 'zigbeecontrol'.

    Only returns matches where the edit distance is less than max_relative_distance
    of the longer string's length. This filters out semantically unrelated matches.

    Args:
        invalid_repo: The invalid repository name to find suggestions for
        all_repos: List of all valid repository names (full paths)
        max_suggestions: Maximum number of suggestions to return
        max_relative_distance: Maximum relative distance (0.0-1.0) to consider a match.
            Default 0.6 (60%) filters out clearly unrelated repositories.

    Returns:
        List of similar repository names (full paths), sorted by similarity (best first)
    """
    if not all_repos:
        return []

    # Extract just the repo name for comparison
    invalid_name = _extract_repo_name(invalid_repo)

    # Calculate distances based on repo names only
    candidates: list[tuple[float, str]] = []
    for repo in all_repos:
        repo_name = _extract_repo_name(repo)
        dist = levenshtein_distance(invalid_name, repo_name)

        # Calculate relative distance (proportion of longer string that differs)
        max_len = max(len(invalid_name), len(repo_name))
        rel_dist = dist / max_len if max_len > 0 else 0.0

        # Only include if within threshold
        if rel_dist <= max_relative_distance:
            candidates.append((rel_dist, repo))

    # Sort by relative distance (ascending) and return top suggestions
    candidates.sort(key=lambda x: x[0])
    return [repo for _, repo in candidates[:max_suggestions]]


def validate_repositories(repos: list[str]) -> None:
    """Validate that all provided repositories exist.

    Args:
        repos: List of repository names to validate

    Raises:
        GitblitAPIError: If any repository does not exist, with suggestions
    """
    if not repos:
        return

    cache = _get_cache()
    all_repo_names = cache.get_repo_names()
    valid_repos_set = set(all_repo_names)

    invalid_repos = [repo for repo in repos if repo not in valid_repos_set]

    if invalid_repos:
        # Build error message with suggestions for each invalid repo
        error_parts: list[str] = []
        for invalid_repo in invalid_repos:
            suggestions = find_similar_repos(invalid_repo, all_repo_names)
            if suggestions:
                quoted = [f"'{s}'" for s in suggestions]
                if len(quoted) == 1:
                    suggestions_str = quoted[0]
                else:
                    suggestions_str = ", ".join(quoted[:-1]) + " or " + quoted[-1]
                error_parts.append(
                    f"Repository '{invalid_repo}' not found. Did you mean: {suggestions_str}?"
                )
            else:
                error_parts.append(f"Repository '{invalid_repo}' not found.")

        raise GitblitAPIError("NOT_FOUND", " ".join(error_parts))


def validate_repository(repo: str) -> None:
    """Validate that a single repository exists.

    Args:
        repo: Repository name to validate

    Raises:
        GitblitAPIError: If the repository does not exist, with suggestions
    """
    validate_repositories([repo])
