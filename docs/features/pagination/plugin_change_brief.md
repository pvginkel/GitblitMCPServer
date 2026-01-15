# Plugin Change Brief: Offset-Based Pagination

## Overview

Implement consistent offset-based pagination across all list and search endpoints, aligning parameter names and response structure.

## Endpoints to Update

| Endpoint | Current State | Changes Needed |
|----------|---------------|----------------|
| `/repos` | Cursor-based (`after`/`endCursor`) | Switch to offset-based |
| `/files` | No pagination | Add `limit`, `offset`, `limitHit` |
| `/search/files` | `count` param, has `limitHit` | Rename to `limit`, add `offset` |
| `/search/commits` | `count` param, has `limitHit` | Rename to `limit`, add `offset` |
| `/find` | `limit` param, has `limitHit` | Add `offset` |

**Not changing:** `/file` (read file) - uses line ranges which is appropriate.

## Aligned Parameter Names

All paginated endpoints should use these parameter names:

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Maximum number of results to return |
| `offset` | integer | 0 | Number of results to skip (for pagination) |

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `totalCount` | integer | Total number of matching items (before limit/offset applied) |
| `limitHit` | boolean | `true` if more results exist beyond current page |

## Endpoint Specifications

### GET /repos

**Current request:**
```
?query=foo&limit=50&after=cursor123
```

**New request:**
```
?query=foo&limit=50&offset=0
```

**Current response:**
```json
{
  "repositories": [...],
  "pagination": {
    "totalCount": 150,
    "hasNextPage": true,
    "endCursor": "cursor123"
  }
}
```

**New response:**
```json
{
  "repositories": [...],
  "totalCount": 150,
  "limitHit": true
}
```

### GET /files

**Current request:**
```
?repo=team/project.git&path=src&revision=main
```

**New request:**
```
?repo=team/project.git&path=src&revision=main&limit=100&offset=0
```

**Current response:**
```json
{
  "files": [...]
}
```

**New response:**
```json
{
  "files": [...],
  "totalCount": 250,
  "limitHit": true
}
```

### GET /search/files

**Current request:**
```
?query=TODO&count=25&contextLines=10
```

**New request:**
```
?query=TODO&limit=25&offset=0&contextLines=10
```

**Response:** Already has `totalCount` and `limitHit`, no changes needed to response structure.

### GET /search/commits

**Current request:**
```
?query=fix&repos=project.git&count=25
```

**New request:**
```
?query=fix&repos=project.git&limit=25&offset=0
```

**Response:** Already has `totalCount` and `limitHit`, no changes needed to response structure.

### GET /find

**Current request:**
```
?pathPattern=**/*.java&limit=50
```

**New request:**
```
?pathPattern=**/*.java&limit=50&offset=0
```

**Response:** Already has `totalCount` and `limitHit`, no changes needed to response structure.

## Implementation Notes

### Offset Calculation

For all endpoints:
```java
// Skip 'offset' items, return up to 'limit' items
// limitHit = (offset + returnedCount) < totalCount
boolean limitHit = (offset + results.size()) < totalCount;
```

### Default Values

- `limit`: Default 50, max 100 (for `/repos`, `/files`) or max 200 (for search/find)
- `offset`: Default 0

### Backward Compatibility

The `count` parameter in search endpoints should be deprecated but still accepted as an alias for `limit` during a transition period. If both are provided, `limit` takes precedence.

The `after` parameter in `/repos` should be removed (breaking change) or return an error if provided.

## Testing

Each endpoint should have tests for:
1. Default pagination (no params) returns first page with correct `limitHit`
2. `offset=0` behaves same as no offset
3. `offset=N` skips first N results
4. `offset` beyond total results returns empty with `limitHit=false`
5. `totalCount` reflects true total regardless of limit/offset
