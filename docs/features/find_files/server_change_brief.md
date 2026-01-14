# Change Brief: Find Files MCP Tool

## Overview

Add a new `gb_find_files` MCP tool to the Gitblit MCP Server that enables AI assistants to discover files by path pattern across repositories.

## Motivation

Current file discovery options are limited:

- `gb_list_files` - Lists files in a single directory, one repo at a time
- `gb_file_search` - Searches file *contents*, not paths

Common AI assistant tasks require finding files by name/pattern across repos:

- "Find all repos with a Dockerfile"
- "Which projects have protobuf definitions?"
- "Find all sdkconfig files in the firmware repos"

## Functional Requirements

### New MCP Tool

**`gb_find_files`**

Find files matching a glob pattern across repositories.

#### Input Schema

```json
{
  "type": "object",
  "required": ["pathPattern"],
  "properties": {
    "pathPattern": {
      "type": "string",
      "description": "Glob pattern to match file paths (e.g., '*.proto', '**/Dockerfile', 'src/**/test_*.py')"
    },
    "repos": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Repository names to search. If empty, searches all accessible repositories."
    },
    "revision": {
      "type": "string",
      "description": "Branch, tag, or commit SHA. Defaults to HEAD of default branch."
    },
    "limit": {
      "type": "integer",
      "description": "Maximum number of files to return. Defaults to 50."
    }
  }
}
```

#### Output Schema

```json
{
  "type": "object",
  "required": ["pattern", "totalCount", "limitHit", "results"],
  "properties": {
    "pattern": {
      "type": "string",
      "description": "The glob pattern that was searched"
    },
    "totalCount": {
      "type": "integer",
      "description": "Total number of matching files found"
    },
    "limitHit": {
      "type": "boolean",
      "description": "Whether results were truncated due to limit"
    },
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["repository", "files"],
        "properties": {
          "repository": {
            "type": "string",
            "description": "Repository name"
          },
          "revision": {
            "type": "string",
            "description": "Resolved revision reference"
          },
          "files": {
            "type": "array",
            "items": { "type": "string" },
            "description": "List of matching file paths"
          }
        }
      }
    }
  }
}
```

#### Glob Pattern Syntax

| Pattern | Description | Example Matches |
|---------|-------------|-----------------|
| `*` | Any characters except `/` | `*.java` → `Foo.java` |
| `**` | Any path segments | `**/test.py` → `src/foo/test.py` |
| `?` | Single character | `?.txt` → `a.txt` |

#### Example Usage

```
User: "Find all Dockerfiles in the organization"
Tool call: gb_find_files(pathPattern="**/Dockerfile")

User: "Which repos have protobuf files?"
Tool call: gb_find_files(pathPattern="**/*.proto")

User: "Find sdkconfig in firmware repos"
Tool call: gb_find_files(pathPattern="**/sdkconfig", repos=["firmware/sensor.git", "firmware/gateway.git"])

User: "List all Python test files"
Tool call: gb_find_files(pathPattern="**/test_*.py")
```

## Technical Design

### Client Method

Add to `GitblitClient` in `client.py`:

```python
def find_files(
    self,
    path_pattern: str,
    repos: list[str] | None = None,
    revision: str | None = None,
    limit: int = 50,
) -> FindFilesResponse | ErrorResponse:
    """Find files by path pattern across repositories.

    Args:
        path_pattern: Glob pattern to match file paths
        repos: Repository names to search (default: all)
        revision: Branch, tag, or commit SHA (default: HEAD)
        limit: Maximum files to return

    Returns:
        FindFilesResponse or ErrorResponse
    """
    params: dict[str, Any] = {"pathPattern": path_pattern, "limit": limit}
    if repos:
        params["repos"] = ",".join(repos)
    if revision:
        params["revision"] = revision

    result = self._make_request("/find", params)
    if isinstance(result, ErrorResponse):
        return result

    return FindFilesResponse(**result)
```

### Tool Implementation

Add `tools/find_files.py`:

```python
"""Find files MCP tool."""

from ..client import get_client
from ..schemas import ErrorResponse, FindFilesResponse


def gb_find_files(
    pathPattern: str,
    repos: list[str] | None = None,
    revision: str | None = None,
    limit: int = 50,
) -> FindFilesResponse | ErrorResponse:
    """Find files matching a glob pattern across repositories.

    Args:
        pathPattern: Glob pattern to match file paths.
        repos: Repository names to search. Searches all if not specified.
        revision: Branch, tag, or commit SHA. Defaults to HEAD.
        limit: Maximum number of files to return. Defaults to 50.

    Returns:
        FindFilesResponse with matching files grouped by repository.
    """
    client = get_client()
    return client.find_files(
        path_pattern=pathPattern,
        repos=repos,
        revision=revision,
        limit=limit,
    )
```

### Response Schema

Add to `schemas.py`:

```python
class FindFilesResult(BaseModel):
    """Single repository's matching files."""
    repository: str
    revision: str | None = None
    files: list[str]


class FindFilesResponse(BaseModel):
    """Response from find_files endpoint."""
    pattern: str
    totalCount: int
    limitHit: bool
    results: list[FindFilesResult]
```

### Server Registration

Register in `server.py`:

```python
from .tools.find_files import gb_find_files

@mcp.tool()
def find_files(
    pathPattern: str,
    repos: list[str] | None = None,
    revision: str | None = None,
    limit: int = 50,
) -> dict:
    """Find files matching a glob pattern across repositories."""
    result = gb_find_files(pathPattern, repos, revision, limit)
    return result.model_dump()
```

## Files to Create/Modify

| File | Action |
|------|--------|
| `src/gitblit_mcp_server/tools/find_files.py` | Create - Tool implementation |
| `src/gitblit_mcp_server/schemas.py` | Modify - Add response models |
| `src/gitblit_mcp_server/client.py` | Modify - Add client method |
| `src/gitblit_mcp_server/server.py` | Modify - Register MCP tool |
| `tests/test_find_files.py` | Create - Integration tests |
| `docs/mcp_api.md` | Modify - Document new tool |

## Testing

Integration tests against live server:

```python
def test_find_files_exact_name():
    """Find files by exact name."""
    result = gb_find_files(pathPattern="README.md")
    assert result.totalCount > 0
    assert all("README.md" in r.files for r in result.results)

def test_find_files_extension():
    """Find files by extension."""
    result = gb_find_files(pathPattern="**/*.java")
    assert result.totalCount > 0
    assert all(f.endswith(".java") for r in result.results for f in r.files)

def test_find_files_specific_repo():
    """Find files in specific repository."""
    result = gb_find_files(pathPattern="**/*.py", repos=["test-repo.git"])
    assert all(r.repository == "test-repo.git" for r in result.results)

def test_find_files_no_matches():
    """Pattern matching nothing returns empty results."""
    result = gb_find_files(pathPattern="**/nonexistent-file-xyz.abc")
    assert result.totalCount == 0
    assert result.results == []

def test_find_files_limit():
    """Verify limit is respected."""
    result = gb_find_files(pathPattern="**/*", limit=5)
    assert result.totalCount <= 5 or result.limitHit
```

## Dependencies

- Requires plugin endpoint `GET /api/.mcp-internal/find` (see `plugin_change_brief.md`)

## Success Criteria

1. Tool registered and callable via MCP
2. Glob patterns work as documented
3. Results correctly grouped by repository
4. Error handling matches other tools
5. Tests pass against live server
6. Documentation updated in `mcp_api.md`
