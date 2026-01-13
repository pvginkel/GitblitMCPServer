# GitblitMCPSupportPlugin - Implementation Plan

This document provides specifications for a Java developer to rework the existing Gitblit Search API Plugin into the GitblitMCPSupportPlugin.

## Overview

The plugin provides REST API endpoints that the Gitblit MCP Server calls. The MCP Server is a thin Python adapter that translates MCP protocol requests to HTTP calls against this plugin. All repository operations (listing, file access, search) are implemented in this plugin.

**Related Documentation:**
- `docs/search_plugin_api.md` - REST API specification (request/response formats)
- `docs/mcp_api.md` - MCP tool specifications (context for how the API is used)
- `docs/mvp_scope.md` - MVP feature scope

## Renaming

### Project Rename

| Current | New |
|---------|-----|
| `GitblitSearchApiPlugin` | `GitblitMCPSupportPlugin` |
| `searchplugin` (artifactId) | `mcp-support-plugin` |
| `com.gitblit.plugin.search` | `com.gitblit.plugin.mcp` |
| `SearchPlugin.java` | `MCPSupportPlugin.java` |
| `SearchApiFilter.java` | `MCPApiFilter.java` |

### pom.xml Changes

```xml
<groupId>com.gitblit.plugin</groupId>
<artifactId>mcp-support-plugin</artifactId>
<version>1.0.0</version>

<name>Gitblit MCP Support Plugin</name>
<description>Provides REST API endpoints for Gitblit MCP Server integration</description>
```

### Manifest Changes

```xml
<Plugin-Id>mcp-support-plugin</Plugin-Id>
<Plugin-Class>com.gitblit.plugin.mcp.MCPSupportPlugin</Plugin-Class>
```

---

## API Base Path

Change from `/api/search` to `/api/mcp-server`.

All endpoints will be prefixed with `/api/mcp-server/`.

---

## Endpoints to Implement

### 1. GET /api/mcp-server/repos

List repositories accessible to the authenticated user.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | No | - | Filter by name (substring match, case-insensitive) |
| `limit` | int | No | 50 | Max results (cap at 100) |
| `after` | string | No | - | Pagination cursor (repository name to start after) |

**Implementation Notes:**
- Use `IGitblit.getRepositoryModels(UserModel)` to get accessible repositories
- Filter by `query` using case-insensitive substring match on `model.name`
- Sort alphabetically by name
- Implement cursor-based pagination using repository name as cursor

**Response:**

```json
{
  "repositories": [
    {
      "name": "team/project.git",
      "description": "Repository description",
      "lastChange": "2024-01-15T10:30:00Z",
      "hasCommits": true
    }
  ],
  "pagination": {
    "totalCount": 42,
    "hasNextPage": true,
    "endCursor": "team/project.git"
  }
}
```

**Fields from RepositoryModel:**
- `name` → `model.name`
- `description` → `model.description`
- `lastChange` → `model.lastChange` (format as ISO 8601)
- `hasCommits` → `model.hasCommits`

---

### 2. GET /api/mcp-server/files

List files and directories at a path within a repository.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `repo` | string | Yes | - | Repository name (e.g., `team/project.git`) |
| `path` | string | No | `/` | Directory path within repository |
| `revision` | string | No | HEAD | Branch, tag, or commit SHA |

**Implementation Notes:**
- Use `JGitUtils.getFilesInPath(Repository, String path, RevCommit commit)`
- For revision resolution, use `JGitUtils.getCommit(Repository, revision)`
- If revision is empty/null, use the default branch HEAD
- List directories first, then files
- Directory paths should end with `/`

**Response:**

```json
{
  "files": [
    {
      "path": "src/",
      "isDirectory": true
    },
    {
      "path": "README.md",
      "isDirectory": false
    }
  ]
}
```

**Error Cases:**
- 404 if repository not found or user has no access
- 404 if path does not exist
- 400 if revision cannot be resolved

---

### 3. GET /api/mcp-server/file

Read file content from a repository.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `repo` | string | Yes | - | Repository name |
| `path` | string | Yes | - | File path within repository |
| `revision` | string | No | HEAD | Branch, tag, or commit SHA |
| `startLine` | int | No | 1 | First line to return (1-indexed) |
| `endLine` | int | No | EOF | Last line to return (1-indexed, inclusive) |

**Implementation Notes:**
- Use `JGitUtils.getStringContent(Repository, RevTree, String path)` to get content
- **Size limit**: Return 400 error if file exceeds 128KB (131072 bytes)
- Split content by newlines, apply line range filter
- Prefix each line with line number: `{lineNum}: {content}`
- Handle binary files gracefully (return error or indicate binary)

**Response:**

```json
{
  "content": "1: # README\n2: \n3: This is the readme.\n"
}
```

**Error Cases:**
- 404 if repository, path, or revision not found
- 400 if file exceeds 128KB
- 400 if file is binary

---

### 4. GET /api/mcp-server/search/files

Search file contents using Lucene index.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Lucene search query |
| `repos` | string | No | all | Comma-separated repository names |
| `pathPattern` | string | No | - | File path filter (e.g., `*.java`) |
| `branch` | string | No | - | Branch filter (e.g., `refs/heads/main`) |
| `count` | int | No | 25 | Max results (cap at 100) |
| `contextLines` | int | No | 100 | Lines of context around each match |

**Implementation Notes:**
- Automatically prepend `type:blob` to query to search only file content
- If `pathPattern` provided, add `path:{pattern}` to query
- If `branch` provided, add `branch:"{branch}"` to query
- Use existing `IGitblit.search()` method
- For each result, fetch file context using the chunk format (see below)

**Context Fetching (chunks):**
- For each search result, fetch the file content at the matching commit
- Find the line containing the match (use fragment to locate)
- Return a chunk with `contextLines` lines of context around the match (default: 100)
- Format as `{lineNum}: {content}` per line

**Response:**

```json
{
  "query": "type:blob AND SQLException",
  "totalCount": 15,
  "limitHit": false,
  "results": [
    {
      "repository": "backend.git",
      "path": "src/db/Connection.java",
      "branch": "refs/heads/main",
      "commitId": "abc123def456",
      "chunks": [
        {
          "startLine": 45,
          "endLine": 55,
          "content": "45:     try {\n46:         connection = DriverManager.getConnection(url);\n47:     } catch (SQLException e) {\n48:         logger.error(\"Database error\", e);\n49:     }"
        }
      ]
    }
  ]
}
```

**Chunk Format:**
- `startLine`: 1-indexed first line of chunk
- `endLine`: 1-indexed last line of chunk (inclusive)
- `content`: Lines with line numbers prefixed, joined by `\n`

---

### 5. GET /api/mcp-server/search/commits

Search commit history using Lucene index.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Lucene search query |
| `repos` | string | Yes | - | Comma-separated repository names |
| `authors` | string | No | - | Comma-separated author names to filter by (OR logic) |
| `branch` | string | No | - | Branch filter |
| `count` | int | No | 25 | Max results (cap at 100) |

**Implementation Notes:**
- Automatically prepend `type:commit` to query to search only commits
- If `authors` provided, add `AND (author:name1 OR author:name2 OR ...)` to query
- If `branch` provided, add `AND branch:"{branch}"` to query
- Use existing `IGitblit.search()` method

**Response:**

```json
{
  "query": "type:commit AND (bug OR fix)",
  "totalCount": 8,
  "limitHit": false,
  "commits": [
    {
      "repository": "myproject.git",
      "commit": "abc123def456789",
      "author": "John Doe",
      "committer": "John Doe",
      "date": "2024-01-15T10:30:00Z",
      "title": "Fix null pointer bug in parser",
      "message": "Fix null pointer bug in parser\n\nThe parser was crashing when input was empty.",
      "branch": "refs/heads/main"
    }
  ]
}
```

**Fields from SearchResult:**
- `repository` → `result.repository`
- `commit` → `result.commitId`
- `author` → `result.author`
- `committer` → `result.committer`
- `date` → `result.date` (format as ISO 8601)
- `title` → first line of `result.summary`
- `message` → `result.summary` (full message)
- `branch` → `result.branch`

---

## Error Response Format

All errors should return JSON:

```json
{
  "error": "Descriptive error message",
  "status": 400
}
```

**Standard Error Codes:**
- `400` - Bad request (missing required params, invalid values, file too large)
- `404` - Not found (repository, file, or revision doesn't exist)
- `500` - Internal server error

---

## Code Structure

### Recommended File Organization

```
src/main/java/com/gitblit/plugin/mcp/
├── MCPSupportPlugin.java          # Plugin lifecycle
├── MCPApiFilter.java              # HTTP filter, route dispatcher
├── handlers/
│   ├── ReposHandler.java          # /repos endpoint
│   ├── FilesHandler.java          # /files endpoint
│   ├── FileHandler.java           # /file endpoint
│   ├── FileSearchHandler.java     # /search/files endpoint
│   └── CommitSearchHandler.java   # /search/commits endpoint
├── model/
│   ├── RepoListResponse.java      # Response DTOs
│   ├── FileListResponse.java
│   ├── FileContentResponse.java
│   ├── FileSearchResponse.java
│   ├── CommitSearchResponse.java
│   └── ErrorResponse.java
└── util/
    └── ResponseWriter.java        # JSON serialization helper
```

### MCPApiFilter Changes

The existing `SearchApiFilter` handles a single endpoint. Refactor to:

1. Change API path constant to `/api/mcp-server`
2. Add routing logic to dispatch to appropriate handler based on URI:
   - `/api/mcp-server/repos` → `ReposHandler`
   - `/api/mcp-server/files` → `FilesHandler`
   - `/api/mcp-server/file` → `FileHandler`
   - `/api/mcp-server/search/files` → `FileSearchHandler`
   - `/api/mcp-server/search/commits` → `CommitSearchHandler`

3. Each handler implements a common interface:

```java
public interface RequestHandler {
    void handle(HttpServletRequest request, HttpServletResponse response,
                IGitblit gitblit, UserModel user) throws IOException;
}
```

---

## Key Gitblit APIs to Use

### Repository Access
```java
IGitblit gitblit = GitblitContext.getManager(IGitblit.class);
List<RepositoryModel> repos = gitblit.getRepositoryModels(user);
Repository repo = gitblit.getRepository(repoName);
```

### File Operations
```java
// Get commit from revision
RevCommit commit = JGitUtils.getCommit(repository, revision);

// List files at path
List<PathModel> files = JGitUtils.getFilesInPath(repository, path, commit);

// Read file content
String content = JGitUtils.getStringContent(repository, commit.getTree(), filePath);
```

### Search
```java
// Existing search API
List<SearchResult> results = gitblit.search(query, page, pageSize, repositories);
```

---

## Testing Checklist

- [ ] `/repos` - List all repos, filter by query, pagination
- [ ] `/files` - List root, list subdirectory, specific revision, non-existent path
- [ ] `/file` - Read file, line range, large file rejection, binary file handling
- [ ] `/search/files` - Basic search, path filter, repo filter, branch filter
- [ ] `/search/commits` - Message search, author search, combined filters
- [ ] Authentication - Anonymous access, authenticated access, permission filtering
- [ ] Error handling - Invalid params, not found, internal errors
- [ ] CORS headers - All endpoints return proper CORS headers

---

## Migration from Existing Code

The existing `SearchApiFilter.java` contains useful code that can be reused:

1. **Authentication handling** - Keep the existing `authManager.authenticate(request)` pattern
2. **Repository filtering** - Keep the accessible repository filtering logic
3. **Context fetching** - Adapt `populateFileContext()` for the new chunk format
4. **Match line finding** - Keep `findMatchLine()` for locating matches in files
5. **JSON serialization** - Keep using Gson with the same date format

**Key Changes:**
- Response format changes to match new schemas (chunks instead of context string)
- Add new endpoints (repos, files, file)
- Restructure search endpoints (separate file/commit search)
- Add line range support for file reading
- Add file size limit enforcement
