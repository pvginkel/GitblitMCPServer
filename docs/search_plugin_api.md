# Gitblit Search API Plugin - REST API Specification

This document specifies the REST API endpoints provided by the Gitblit Search API Plugin for use by the Gitblit MCP Server.

**Base Path:** `/api/mcp-server`

## Common Response Format

### Success Response
All successful responses return HTTP 200 with a JSON body.

### Error Response
```json
{
  "error": "Error message describing what went wrong",
  "status": 400
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad request (missing/invalid parameters)
- `404` - Resource not found
- `500` - Internal server error

---

## Endpoints

### GET /api/mcp-server/repos

List repositories accessible to the current user.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | No | - | Filter repositories by name (substring match) |
| `limit` | integer | No | 50 | Maximum results to return (max: 100) |
| `after` | string | No | - | Pagination cursor |

#### Response

```json
{
  "repositories": [
    {
      "name": "team/project.git",
      "description": "Project description",
      "lastChange": "2024-01-15T10:30:00Z",
      "hasCommits": true
    }
  ],
  "pagination": {
    "totalCount": 42,
    "hasNextPage": true,
    "endCursor": "cursor_token_here"
  }
}
```

#### Example

```bash
curl "http://gitblit:8080/api/mcp-server/repos?query=api&limit=10"
```

---

### GET /api/mcp-server/files

List files and directories at a path within a repository.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `repo` | string | Yes | - | Repository name (e.g., `team/project.git`) |
| `path` | string | No | `/` | Directory path within repository |
| `revision` | string | No | HEAD | Branch, tag, or commit SHA |

#### Response

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

Directories are listed first, followed by files. Directory paths end with `/`.

#### Example

```bash
curl "http://gitblit:8080/api/mcp-server/files?repo=myproject.git&path=src&revision=main"
```

---

### GET /api/mcp-server/file

Read the content of a file from a repository.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `repo` | string | Yes | - | Repository name |
| `path` | string | Yes | - | File path within repository |
| `revision` | string | No | HEAD | Branch, tag, or commit SHA |
| `startLine` | integer | No | 1 | First line to return (1-indexed) |
| `endLine` | integer | No | EOF | Last line to return (1-indexed, inclusive) |

#### Response

```json
{
  "content": "1: # README\n2: \n3: This is the readme file.\n4: ..."
}
```

Content is returned with line numbers prefixed in the format `{line_number}: {content}`.

#### Errors

- `404` - Repository or file not found
- `400` - File exceeds 128KB size limit

#### Example

```bash
curl "http://gitblit:8080/api/mcp-server/file?repo=myproject.git&path=src/main.py&startLine=10&endLine=50"
```

---

### GET /api/mcp-server/search/files

Search file contents across repositories using Lucene.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Lucene search query |
| `repos` | string | No | all | Comma-separated repository names |
| `pathPattern` | string | No | - | File path pattern filter (e.g., `*.java`) |
| `branch` | string | No | - | Branch filter (e.g., `refs/heads/main`) |
| `count` | integer | No | 25 | Maximum results (max: 100) |
| `contextLines` | integer | No | 100 | Lines of context around each match |

The search is automatically scoped to `type:blob` (file content only).

#### Response

```json
{
  "query": "SQLException",
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
          "content": "45:     try {\n46:         connection = DriverManager.getConnection(url);\n47:     } catch (SQLException e) {\n48:         logger.error(\"Database error\", e);\n49:         throw e;\n50:     }"
        }
      ]
    }
  ]
}
```

Each result includes one or more `chunks` containing the matching code with surrounding context. Line numbers are 1-indexed.

#### Example

```bash
curl "http://gitblit:8080/api/mcp-server/search/files?query=SQLException&repos=backend.git&pathPattern=*.java&count=10"
```

---

### GET /api/mcp-server/search/commits

Search commit history across repositories using Lucene.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `repos` | string | Yes | - | Comma-separated repository names |
| `messageTerms` | string | No | - | Comma-separated terms to search in commit messages (OR logic) |
| `authors` | string | No | - | Comma-separated author names to filter by (OR logic) |
| `branch` | string | No | - | Branch filter |
| `count` | integer | No | 25 | Maximum results (max: 100) |

At least one of `messageTerms` or `authors` must be provided.

The search is automatically scoped to `type:commit`.

#### Response

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
      "message": "Fix null pointer bug in parser\n\nThe parser was crashing when input was empty.\nAdded null check to prevent this.",
      "branch": "refs/heads/main"
    }
  ]
}
```

#### Example

```bash
curl "http://gitblit:8080/api/mcp-server/search/commits?repos=myproject.git&messageTerms=bug,fix&count=10"
```

---

## Lucene Query Syntax

The search endpoints support Gitblit's Lucene query syntax:

### File Search Fields
- Default field searches file content
- `path:pattern` - File path (supports wildcards: `path:*.java`)

### Commit Search Fields
- Default field searches commit message
- `author:name` - Commit author
- `committer:name` - Committer

### Query Operators
- `term1 AND term2` - Both terms required
- `term1 OR term2` - Either term matches
- `"exact phrase"` - Phrase search
- `term*` - Prefix wildcard
- `-term` - Exclude term

### Examples

```
# File content containing "error" in Java files
query=error&pathPattern=*.java

# Commits by john with "fix" in message
messageTerms=fix&authors=john

# Complex query with Lucene syntax
query="null pointer" AND exception
```

---

## CORS Headers

All endpoints include CORS headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
```

---

## Implementation Notes

1. **Authentication**: Inherits Gitblit's authentication (Basic Auth, session cookies). Anonymous access works if repositories allow it.

2. **Repository Access**: Only returns repositories/files the authenticated user can access.

3. **Search Indexing**: Search only works on repositories with Lucene indexing enabled and indexed branches configured.

4. **Response Formatting**: All responses match the structure expected by the MCP server tools.

5. **Chunk Context**: File search results include configurable context lines around each match (default: 100).
