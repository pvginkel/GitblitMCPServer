# Change Brief: Search Improvements Plugin Changes

## Overview

Improve file search behavior to reduce response sizes and eliminate duplicate results. Two changes:

1. Lower default context lines from 100 to 10
2. Search only default branch when branch filter is omitted

## Motivation

Current search behavior causes unnecessarily large responses:

- **Context bloat:** 100 lines of context per match inflates responses, contributing to token limit issues in AI assistants
- **Branch duplicates:** Same file appearing in multiple branches returns duplicate results

## Changes

### 1. Lower Default Context Lines

**File:** `handlers/FileSearchHandler.java`

**Current:**
```java
private static final int CONTEXT_LINES = 100;
```

**Change to:**
```java
private static final int DEFAULT_CONTEXT_LINES = 10;
```

Also update the handler to read `contextLines` from request parameters with the new default:

```java
int contextLines = parseIntParam(request, "contextLines", DEFAULT_CONTEXT_LINES);
// Cap at reasonable maximum
if (contextLines > 200) contextLines = 200;
```

**Behavior:**
- Default: 10 lines of context (5 before, 5 after match)
- Callers can request more via `contextLines` parameter
- Maximum capped at 200 to prevent abuse

### 2. Default Branch Only When Branch Filter Omitted

**File:** `handlers/FileSearchHandler.java`

**Current behavior:** When `branch` parameter is omitted, Lucene searches all indexed branches, returning duplicates when files exist on multiple branches.

**New behavior:** When `branch` parameter is omitted or empty, restrict search to the default branch of each repository.

**Implementation:**

```java
// If no branch specified, search default branch only
if (StringUtils.isEmpty(branch)) {
    // Get default branch for each repo and add to query
    // This requires building per-repo queries or post-filtering by branch
}
```

**Implementation - Lucene query approach:**

Use `RepositoryModel.HEAD` which contains the full branch reference (e.g., `refs/heads/main`) for each repository's default branch:

```java
// Build filter using default branch of each repository
StringBuilder branchFilter = new StringBuilder();
for (String repoName : searchRepos) {
    RepositoryModel model = gitblit.getRepositoryModel(repoName);
    if (model != null && !StringUtils.isEmpty(model.HEAD)) {
        if (branchFilter.length() > 0) {
            branchFilter.append(" OR ");
        }
        branchFilter.append("branch:\"").append(model.HEAD).append("\"");
    }
}
if (branchFilter.length() > 0) {
    luceneQuery.append(" AND (").append(branchFilter).append(")");
}
```

This approach filters at the Lucene query level, which is more efficient than post-filtering and ensures correct result counts.

## Files to Modify

| File | Changes |
|------|---------|
| `handlers/FileSearchHandler.java` | Lower default context, add default-branch filtering |
| `handlers/CommitSearchHandler.java` | Add default-branch filtering (same logic) |

## Testing

1. **Context lines default:**
   - Search without `contextLines` param → verify ~10 lines returned per chunk
   - Search with `contextLines=50` → verify 50 lines returned
   - Search with `contextLines=500` → verify capped at 200

2. **Default branch filtering:**
   - Search without `branch` param → verify no duplicates from multiple branches
   - Search with `branch=refs/heads/develop` → verify only develop branch results
   - Verify results come from each repo's default branch (may vary per repo)

## Success Criteria

1. Default context reduced to 10 lines
2. `contextLines` parameter respected up to 200 max
3. Omitting `branch` returns only default branch results
4. Explicit `branch` parameter still works as before
5. No duplicate results from multiple branches in default case
