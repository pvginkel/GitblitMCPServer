# Change Brief: Search Improvements Server Changes

## Overview

Update MCP server documentation and defaults to reflect plugin search behavior changes:

1. Document new default context lines (10 instead of 100)
2. Document default branch behavior when branch filter is omitted

## Changes

### 1. Update `docs/mcp_api.md`

#### gb_file_search Section

Update the `contextLines` parameter description:

**Current:**
```json
"contextLines": {
  "type": "integer",
  "description": "Number of context lines to include around each match. Defaults to 100."
}
```

**Change to:**
```json
"contextLines": {
  "type": "integer",
  "description": "Number of context lines to include around each match. Defaults to 10. Maximum 200."
}
```

Update the `branch` parameter description:

**Current:**
```json
"branch": {
  "type": "string",
  "description": "Filter by branch (e.g., 'refs/heads/main')"
}
```

**Change to:**
```json
"branch": {
  "type": "string",
  "description": "Filter by branch (e.g., 'refs/heads/main'). If omitted, searches only each repository's default branch to avoid duplicate results."
}
```

#### gb_commit_search Section

Update the `branch` parameter description similarly:

**Change to:**
```json
"branch": {
  "type": "string",
  "description": "Filter by branch (e.g., 'refs/heads/main'). If omitted, searches only each repository's default branch."
}
```

### 2. Update `docs/search_plugin_api.md`

#### GET /api/.mcp-internal/search/files

Update parameter table:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `contextLines` | integer | No | 10 | Lines of context around each match (max: 200) |
| `branch` | string | No | default branch | Branch filter. If omitted, searches only the default branch of each repository. |

#### GET /api/.mcp-internal/search/commits

Update parameter table:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `branch` | string | No | default branch | Branch filter. If omitted, searches only the default branch of each repository. |

### 3. Update Python Defaults (Optional)

If the Python server has hardcoded defaults, update them to match:

**File:** `src/gitblit_mcp_server/tools/file_search.py`

```python
def gb_file_search(
    query: str,
    repos: list[str] | None = None,
    pathPattern: str | None = None,
    branch: str | None = None,
    count: int = 25,
    contextLines: int = 10,  # Changed from 100
) -> FileSearchResponse | ErrorResponse:
```

**File:** `src/gitblit_mcp_server/client.py`

```python
def search_files(
    self,
    query: str,
    repos: list[str] | None = None,
    path_pattern: str | None = None,
    branch: str | None = None,
    count: int = 25,
    context_lines: int = 10,  # Changed from 100
) -> FileSearchResponse | ErrorResponse:
```

## Files to Modify

| File | Changes |
|------|---------|
| `docs/mcp_api.md` | Update contextLines default, branch behavior |
| `docs/search_plugin_api.md` | Update contextLines default, branch behavior |
| `src/gitblit_mcp_server/tools/file_search.py` | Update contextLines default (optional) |
| `src/gitblit_mcp_server/client.py` | Update context_lines default (optional) |

## Testing

1. Verify documentation accurately describes new behavior
2. If Python defaults updated, verify they match plugin defaults
3. Run existing tests to ensure no regressions

## Dependencies

- Requires plugin changes from `plugin_change_brief.md` to be deployed first

## Success Criteria

1. `docs/mcp_api.md` reflects new defaults and behavior
2. `docs/search_plugin_api.md` reflects new defaults and behavior
3. Python code defaults match plugin defaults (if updated)
