# Server Change Brief: Offset-Based Pagination

## Overview

Update the MCP server to use consistent offset-based pagination across all list and search tools, aligning with plugin changes.

## Tools to Update

| Tool | Current State | Changes Needed |
|------|---------------|----------------|
| `gb_list_repos` | `limit`, `after` (cursor), returns `pagination` object | Remove `after`, flatten response, add `offset` |
| `gb_list_files` | No pagination | Add `limit`, `offset`, update response schema |
| `gb_file_search` | `count` param | Rename to `limit`, add `offset` |
| `gb_commit_search` | `count` param | Rename to `limit`, add `offset` |
| `gb_find_files` | `limit` param | Add `offset` |

**Not changing:** `gb_read_file` - uses line ranges which is appropriate.

## Aligned Parameter Specification

All paginated tools should use these parameters:

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `limit` | int | 50 | 100-200 | Maximum results to return |
| `offset` | int | 0 | - | Results to skip for pagination |

All paginated responses should include:

| Field | Type | Description |
|-------|------|-------------|
| `totalCount` | int | Total matching items (before limit/offset) |
| `limitHit` | bool | Whether more results exist beyond current page |

## Schema Changes

### schemas.py

**Update ListReposResponse:**
```python
# Remove Pagination model usage
class ListReposResponse(BaseModel):
    repositories: list[Repository]
    totalCount: int = Field(..., description="Total number of matching repositories")
    limitHit: bool = Field(..., description="Whether more results exist beyond current page")
```

**Update ListFilesResponse:**
```python
class ListFilesResponse(BaseModel):
    files: list[FileInfo]
    totalCount: int = Field(..., description="Total number of files in directory")
    limitHit: bool = Field(..., description="Whether more files exist beyond current page")
```

**Pagination model:** Can be removed if no longer used elsewhere.

## Client Changes

### client.py

**Update list_repos:**
```python
def list_repos(
    self,
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,  # New parameter, replaces 'after'
) -> ListReposResponse | ErrorResponse:
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if query:
        params["query"] = query
    # Remove 'after' handling
    ...
```

**Update list_files:**
```python
def list_files(
    self,
    repo: str,
    path: str = "",
    revision: str | None = None,
    limit: int = 100,  # New parameter
    offset: int = 0,   # New parameter
) -> ListFilesResponse | ErrorResponse:
    params: dict[str, Any] = {"repo": repo, "limit": limit, "offset": offset}
    ...
```

**Update search_files:**
```python
def search_files(
    self,
    query: str,
    repos: list[str] | None = None,
    path_pattern: str | None = None,
    branch: str | None = None,
    limit: int = 25,       # Renamed from 'count'
    offset: int = 0,       # New parameter
    context_lines: int = 10,
) -> FileSearchResponse | ErrorResponse:
    params: dict[str, Any] = {
        "query": query,
        "limit": limit,        # Changed from 'count'
        "offset": offset,      # New
        "contextLines": context_lines
    }
    ...
```

**Update search_commits:**
```python
def search_commits(
    self,
    query: str,
    repos: list[str],
    authors: list[str] | None = None,
    branch: str | None = None,
    limit: int = 25,   # Renamed from 'count'
    offset: int = 0,   # New parameter
) -> CommitSearchResponse | ErrorResponse:
    params: dict[str, Any] = {
        "query": query,
        "repos": ",".join(repos),
        "limit": limit,    # Changed from 'count'
        "offset": offset,  # New
    }
    ...
```

**Update find_files:**
```python
def find_files(
    self,
    path_pattern: str,
    repos: list[str] | None = None,
    revision: str | None = None,
    limit: int = 50,
    offset: int = 0,  # New parameter
) -> FindFilesResponse | ErrorResponse:
    params: dict[str, Any] = {
        "pathPattern": path_pattern,
        "limit": limit,
        "offset": offset,  # New
    }
    ...
```

## Tool Changes

### tools/*.py and server.py

Update all tool functions and MCP registrations to:
1. Replace `count` with `limit` parameter
2. Add `offset` parameter
3. Update parameter descriptions

**Parameter descriptions (consistent across tools):**
```python
limit: Annotated[
    int,
    Field(description="Maximum results to return. Default: N, max: M."),
] = N,
offset: Annotated[
    int,
    Field(description="Results to skip for pagination. Default: 0."),
] = 0,
```

**Tool description additions:**
Add to Behavior section of each paginated tool:
```
- Supports offset-based pagination via 'offset' parameter
- Returns 'totalCount' (total matches) and 'limitHit' (whether more results exist)
```

## Documentation Changes

### docs/mcp_api.md

Update each tool's documentation:
1. Add `offset` to input schema
2. Update `limit` description (was `count` for search tools)
3. Ensure output schema shows `totalCount` and `limitHit` for all paginated endpoints
4. Update `gb_list_repos` to remove cursor-based pagination docs

### CLAUDE.md

No changes needed (tools table doesn't include pagination details).

## Test Changes

### tests/

**Update existing tests:**
- `test_list_repos.py`: Remove cursor-based pagination tests, add offset tests
- `test_file_search.py`: Update `count` to `limit` in test calls
- `test_commit_search.py`: Update `count` to `limit` in test calls

**Add pagination tests for each endpoint:**
```python
def test_<endpoint>_pagination_offset(client):
    """Test offset parameter skips results."""
    # Get first page
    result1 = client.<method>(limit=5, offset=0)
    # Get second page
    result2 = client.<method>(limit=5, offset=5)
    # Verify no overlap (if enough results exist)
    ...

def test_<endpoint>_pagination_limit_hit(client):
    """Test limitHit indicates more results."""
    result = client.<method>(limit=1)
    if result.totalCount > 1:
        assert result.limitHit is True
    ...
```

## Migration Notes

This is a breaking change for:
- `gb_list_repos`: Response structure changes (flattened, no `pagination` object)
- `gb_list_repos`: `after` parameter removed
- `gb_file_search`: `count` parameter renamed to `limit`
- `gb_commit_search`: `count` parameter renamed to `limit`

Consumers will need to update their calls when upgrading.
