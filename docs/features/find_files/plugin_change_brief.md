# Change Brief: Find Files Plugin Endpoint

## Overview

Add a new REST endpoint to the Gitblit Search API Plugin that finds files by path pattern across repositories using Git tree walking. This enables efficient cross-repo file discovery without loading file contents.

## Motivation

The existing `/api/.mcp-internal/search/files` endpoint uses Lucene search with post-filtering for path patterns. This is inefficient for path-only queries:

1. Fetches blob content from Lucene index, then filters by path
2. Limited to 100 results max, may miss matches
3. Cannot enumerate all files matching a pattern

Tree walking is the correct approach for path-based file discovery.

## Functional Requirements

### New Endpoint

**`GET /api/.mcp-internal/find`**

Find files matching a glob pattern across repositories.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `pathPattern` | string | Yes | - | Glob pattern (e.g., `*.proto`, `**/Dockerfile`, `src/**/test_*.py`) |
| `repos` | string | No | all | Comma-separated repository names to search |
| `revision` | string | No | HEAD | Branch, tag, or commit SHA |
| `limit` | int | No | 50 | Maximum total files to return (max: 200) |

#### Glob Pattern Syntax

| Pattern | Matches |
|---------|---------|
| `*` | Any characters except `/` |
| `**` | Any characters including `/` (directory crossing) |
| `?` | Single character |
| `*.java` | All Java files in root |
| `**/*.java` | All Java files anywhere |
| `src/**/test_*.py` | Test files under src/ |
| `Dockerfile` | Exact filename in root |
| `**/Dockerfile` | Dockerfile anywhere |

#### Response Schema

```json
{
  "pattern": "**/sdkconfig",
  "totalCount": 8,
  "limitHit": false,
  "results": [
    {
      "repository": "firmware/sensor.git",
      "revision": "refs/heads/main",
      "files": ["sdkconfig", "components/wifi/sdkconfig"]
    },
    {
      "repository": "firmware/gateway.git",
      "revision": "refs/heads/main",
      "files": ["sdkconfig"]
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `pattern` | string | The glob pattern that was searched |
| `totalCount` | int | Total number of matching files found |
| `limitHit` | boolean | True if results were truncated due to limit |
| `results` | array | Matching files grouped by repository |
| `results[].repository` | string | Repository name |
| `results[].revision` | string | Resolved revision (branch ref or commit SHA) |
| `results[].files` | array | List of matching file paths |

#### Error Responses

| Status | Condition |
|--------|-----------|
| 400 | Missing `pathPattern` parameter |
| 400 | Invalid glob pattern syntax |
| 404 | Specified repository not found |

## Technical Design

### Implementation

Create `FindFilesHandler.java` implementing `RequestHandler`:

```java
public class FindFilesHandler implements RequestHandler {

    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 200;

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
                       IGitblit gitblit, UserModel user) throws IOException {

        String pathPattern = request.getParameter("pathPattern");
        if (StringUtils.isEmpty(pathPattern)) {
            ResponseWriter.writeError(response, 400, "Missing required parameter: pathPattern");
            return;
        }

        PathMatcher matcher = parseGlobPattern(pathPattern);
        String revisionParam = request.getParameter("revision");
        int limit = parseIntParam(request, "limit", DEFAULT_LIMIT, MAX_LIMIT);

        List<String> repos = getAccessibleRepositories(gitblit, user, request.getParameter("repos"));

        FindFilesResponse result = new FindFilesResponse();
        result.pattern = pathPattern;
        result.results = new ArrayList<>();
        int totalCount = 0;
        boolean limitHit = false;

        for (String repoName : repos) {
            Repository repo = gitblit.getRepository(repoName);
            if (repo == null) continue;

            try {
                String revision = revisionParam != null ? revisionParam : "HEAD";
                ObjectId commitId = repo.resolve(revision);
                if (commitId == null) continue;

                RevWalk revWalk = new RevWalk(repo);
                RevCommit commit = revWalk.parseCommit(commitId);
                String resolvedRef = resolveRef(repo, revision, commitId);

                List<String> matches = new ArrayList<>();

                TreeWalk treeWalk = new TreeWalk(repo);
                treeWalk.addTree(commit.getTree());
                treeWalk.setRecursive(true);

                while (treeWalk.next()) {
                    if (totalCount >= limit) {
                        limitHit = true;
                        break;
                    }

                    String path = treeWalk.getPathString();
                    if (matcher.matches(path)) {
                        matches.add(path);
                        totalCount++;
                    }
                }

                if (!matches.isEmpty()) {
                    result.results.add(new FindFilesResult(repoName, resolvedRef, matches));
                }

                if (limitHit) break;

            } finally {
                repo.close();
            }
        }

        result.totalCount = totalCount;
        result.limitHit = limitHit;

        ResponseWriter.writeJson(response, result);
    }
}
```

### Glob Pattern Matching

Implement a `PathMatcher` class that compiles glob patterns to regex:

| Glob | Regex |
|------|-------|
| `*` | `[^/]*` |
| `**` | `.*` |
| `?` | `[^/]` |
| `.` | `\\.` (escaped) |

Special handling for `**/` prefix and `/**` suffix patterns.

### Performance Considerations

1. **Early termination** - Stop walking when limit reached
2. **No content loading** - TreeWalk only reads tree objects, not blobs
3. **Repository ordering** - Process repos alphabetically for predictable results
4. **Limit per repo** - Consider adding per-repo sublimit to prevent one large repo dominating results

## Files to Create/Modify

| File | Action |
|------|--------|
| `handlers/FindFilesHandler.java` | Create - Main handler |
| `model/FindFilesResponse.java` | Create - Response model |
| `MCPApiFilter.java` | Modify - Register `/find` route |

## Testing

Test against live Gitblit instance:

1. Find by exact filename: `pathPattern=README.md`
2. Find by extension: `pathPattern=*.java`
3. Find with directory wildcard: `pathPattern=**/pom.xml`
4. Find with path prefix: `pathPattern=src/**/*.py`
5. Limit handling: verify `limitHit` when results exceed limit
6. Empty results: pattern that matches nothing
7. Single repo filter: `repos=specific.git`
8. Non-existent repo: verify graceful handling

## Success Criteria

1. Endpoint returns matching files with correct structure
2. Glob patterns work as documented
3. Results grouped by repository
4. Limit and pagination work correctly
5. Performance acceptable (< 1s for typical queries)
6. No blob content loaded during tree walk
