# Gitblit MCP Server - API Reference

This document describes the MCP tools provided by the Gitblit MCP Server.

---

## gb_list_repos

Lists repositories available in the Gitblit instance.

### Description

Lists repositories that match a search query. Use this tool to discover repositories or resolve partial repository names to full names.

**When to use:**
- Find repositories by name substring
- List all available repositories
- Resolve partial repo names to full paths

### Input Schema

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "query": {
      "type": "string",
      "description": "Optional search query to filter repositories by name. Uses substring matching."
    },
    "limit": {
      "type": "integer",
      "description": "Maximum number of repositories to return. Defaults to 50."
    },
    "after": {
      "type": "string",
      "description": "Pagination cursor for fetching results after this point."
    }
  }
}
```

### Output Schema

```json
{
  "type": "object",
  "required": ["repositories", "pagination"],
  "properties": {
    "repositories": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "description"],
        "properties": {
          "name": {
            "type": "string",
            "description": "Full repository name (e.g., 'team/project.git')"
          },
          "description": {
            "type": "string",
            "description": "Repository description"
          },
          "lastChange": {
            "type": "string",
            "description": "ISO 8601 timestamp of last change"
          },
          "hasCommits": {
            "type": "boolean",
            "description": "Whether the repository has any commits"
          }
        }
      }
    },
    "pagination": {
      "type": "object",
      "required": ["totalCount", "hasNextPage"],
      "properties": {
        "totalCount": {
          "type": "integer"
        },
        "hasNextPage": {
          "type": "boolean"
        },
        "endCursor": {
          "type": "string"
        }
      }
    }
  }
}
```

### Examples

```
User: "Find repositories containing 'api' in the name"
Tool call: gb_list_repos(query="api")

User: "List all repositories"
Tool call: gb_list_repos()
```

---

## gb_list_files

Lists files and directories in a repository path.

### Description

Lists the files and subdirectories at a given path within a repository. Directories are indicated with a trailing slash. Use this to navigate repository structure.

**When to use:**
- Explore repository directory structure
- Find files in a specific directory
- Verify file existence before reading

### Input Schema

```json
{
  "type": "object",
  "required": ["repo"],
  "properties": {
    "repo": {
      "type": "string",
      "description": "Repository name (e.g., 'team/project.git')"
    },
    "path": {
      "type": "string",
      "description": "Directory path within repository. Defaults to root if not specified."
    },
    "revision": {
      "type": "string",
      "description": "Branch, tag, or commit SHA. Defaults to HEAD of default branch."
    }
  }
}
```

### Output Schema

```json
{
  "type": "object",
  "required": ["files"],
  "properties": {
    "files": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "isDirectory"],
        "properties": {
          "path": {
            "type": "string",
            "description": "File or directory name. Directories end with '/'"
          },
          "isDirectory": {
            "type": "boolean"
          }
        }
      }
    }
  }
}
```

### Examples

```
User: "List files in the src directory of myproject.git"
Tool call: gb_list_files(repo="myproject.git", path="src")

User: "Show root directory of team/api.git on branch develop"
Tool call: gb_list_files(repo="team/api.git", revision="develop")
```

---

## gb_read_file

Reads the content of a file from a repository.

### Description

Reads and returns the content of a file at a specific path and revision. Supports line range parameters for large files. Files larger than 128KB will return an error.

**When to use:**
- Read source code files
- Examine configuration files
- View documentation

**Important:** Always verify the file exists using `gb_list_files` or search before attempting to read.

### Input Schema

```json
{
  "type": "object",
  "required": ["repo", "path"],
  "properties": {
    "repo": {
      "type": "string",
      "description": "Repository name (e.g., 'team/project.git')"
    },
    "path": {
      "type": "string",
      "description": "File path within the repository"
    },
    "revision": {
      "type": "string",
      "description": "Branch, tag, or commit SHA. Defaults to HEAD of default branch."
    },
    "startLine": {
      "type": "integer",
      "description": "1-based line number to start reading from"
    },
    "endLine": {
      "type": "integer",
      "description": "1-based line number to stop reading at (inclusive)"
    }
  }
}
```

### Output Schema

```json
{
  "type": "object",
  "required": ["content"],
  "properties": {
    "content": {
      "type": "string",
      "description": "File content with line numbers prefixed (e.g., '1: line one\\n2: line two')"
    }
  }
}
```

### Examples

```
User: "Read the README.md in myproject.git"
Tool call: gb_read_file(repo="myproject.git", path="README.md")

User: "Show lines 50-100 of src/main.py in project.git at tag v1.0"
Tool call: gb_read_file(repo="project.git", path="src/main.py", revision="v1.0", startLine=50, endLine=100)
```

---

## gb_file_search

Searches for content within files across repositories.

### Description

Searches file contents (blobs) using Gitblit's Lucene index. Returns matching code snippets with surrounding context. Use this for finding code patterns, function definitions, or specific text in files.

**When to use:**
- Find code containing specific patterns
- Locate function or class definitions
- Search for configuration values
- Find files by content

### Input Schema

```json
{
  "type": "object",
  "required": ["query"],
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query. Supports Lucene syntax: exact phrases (\"foo bar\"), wildcards (foo*), AND/OR operators."
    },
    "repos": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Repository names to search. If empty, searches all accessible repositories."
    },
    "pathPattern": {
      "type": "string",
      "description": "Filter by file path pattern (e.g., '*.java', 'src/*.py')"
    },
    "branch": {
      "type": "string",
      "description": "Filter by branch (e.g., 'refs/heads/main'). If omitted, searches only each repository's default branch."
    },
    "count": {
      "type": "integer",
      "description": "Maximum number of results to return. Defaults to 25."
    },
    "contextLines": {
      "type": "integer",
      "description": "Number of context lines to include around each match. Defaults to 10, max 200."
    }
  }
}
```

### Output Schema

```json
{
  "type": "object",
  "required": ["query", "totalCount", "results", "limitHit"],
  "properties": {
    "query": {
      "type": "string",
      "description": "The executed search query"
    },
    "totalCount": {
      "type": "integer",
      "description": "Total number of matches found"
    },
    "limitHit": {
      "type": "boolean",
      "description": "Whether results were truncated due to limit"
    },
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["repository", "path", "chunks"],
        "properties": {
          "repository": {
            "type": "string"
          },
          "path": {
            "type": "string"
          },
          "branch": {
            "type": "string"
          },
          "commitId": {
            "type": "string"
          },
          "chunks": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["startLine", "endLine", "content"],
              "properties": {
                "startLine": { "type": "integer" },
                "endLine": { "type": "integer" },
                "content": { "type": "string" }
              }
            }
          }
        }
      }
    }
  }
}
```

### Examples

```
User: "Find all Java files containing 'SQLException'"
Tool call: gb_file_search(query="SQLException", pathPattern="*.java")

User: "Search for 'async def' in the backend.git repository"
Tool call: gb_file_search(query="\"async def\"", repos=["backend.git"])

User: "Find TODO comments in Python files"
Tool call: gb_file_search(query="TODO", pathPattern="*.py")
```

---

## gb_commit_search

Searches commit history across repositories.

### Description

Searches for commits by message content, author, or code changes. Use this to find when changes were made, who made them, or track down specific commits.

**When to use:**
- Find commits by message content
- Search commits by author
- Find when a feature was implemented
- Track code history

### Input Schema

```json
{
  "type": "object",
  "required": ["query", "repos"],
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query. Supports Lucene syntax: exact phrases (\"foo bar\"), wildcards (foo*), AND/OR operators."
    },
    "repos": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Repository names to search (required)"
    },
    "authors": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Filter by author names. Multiple authors use OR logic."
    },
    "branch": {
      "type": "string",
      "description": "Filter by branch (e.g., 'refs/heads/main'). If omitted, searches only each repository's default branch."
    },
    "count": {
      "type": "integer",
      "description": "Maximum number of results. Defaults to 25."
    }
  }
}
```

### Output Schema

```json
{
  "type": "object",
  "required": ["query", "totalCount", "commits", "limitHit"],
  "properties": {
    "query": {
      "type": "string"
    },
    "totalCount": {
      "type": "integer"
    },
    "limitHit": {
      "type": "boolean"
    },
    "commits": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["repository", "commit", "author", "date", "title", "message"],
        "properties": {
          "repository": { "type": "string" },
          "commit": { "type": "string", "description": "Commit SHA" },
          "author": { "type": "string" },
          "committer": { "type": "string" },
          "date": { "type": "string", "description": "ISO 8601 timestamp" },
          "title": { "type": "string", "description": "First line of commit message" },
          "message": { "type": "string", "description": "Full commit message" },
          "branch": { "type": "string" }
        }
      }
    }
  }
}
```

### Examples

```
User: "Find commits mentioning 'bug fix' in myproject.git"
Tool call: gb_commit_search(query="bug fix", repos=["myproject.git"])

User: "What has john.doe committed recently?"
Tool call: gb_commit_search(query="*", repos=["project.git"], authors=["john.doe"])

User: "Find commits about authentication"
Tool call: gb_commit_search(query="auth OR login OR authentication", repos=["api.git", "auth.git"])
```

---

## gb_find_files

Finds files matching a glob pattern across repositories.

### Description

Discovers files by path/name pattern using Git tree walking. Use this to find files across repositories without searching file contents.

**When to use:**
- Find all repositories containing a specific file (e.g., Dockerfile, package.json)
- Discover files by extension across repos
- Find configuration files by name pattern

### Input Schema

```json
{
  "type": "object",
  "required": ["pathPattern"],
  "properties": {
    "pathPattern": {
      "type": "string",
      "description": "Glob pattern to match file paths (e.g., '*.java', '**/Dockerfile', 'src/**/test_*.py')"
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
      "description": "Maximum number of files to return. Defaults to 50, max 200."
    }
  }
}
```

### Output Schema

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
          "repository": { "type": "string" },
          "revision": { "type": "string" },
          "files": {
            "type": "array",
            "items": { "type": "string" }
          }
        }
      }
    }
  }
}
```

### Glob Pattern Syntax

| Pattern | Description | Example |
|---------|-------------|---------|
| `*` | Any characters except `/` | `*.java` matches `Foo.java` |
| `**` | Any path segments | `**/test.py` matches `src/foo/test.py` |
| `?` | Single character | `?.txt` matches `a.txt` |

### Examples

```
User: "Find all Dockerfiles"
Tool call: gb_find_files(pathPattern="**/Dockerfile")

User: "Which repos have protobuf files?"
Tool call: gb_find_files(pathPattern="**/*.proto")

User: "Find sdkconfig in firmware repos"
Tool call: gb_find_files(pathPattern="**/sdkconfig", repos=["firmware/sensor.git", "firmware/gateway.git"])
```

---

## Lucene Query Syntax Reference

Both search tools support Gitblit's Lucene query syntax:

| Syntax | Description | Example |
|--------|-------------|---------|
| `word` | Single term | `TODO` |
| `"phrase"` | Exact phrase | `"null pointer"` |
| `word*` | Wildcard | `auth*` |
| `term1 AND term2` | Both required | `error AND fatal` |
| `term1 OR term2` | Either term | `bug OR fix` |
| `path:pattern` | File path filter | `path:*.java` |
| `author:name` | Author filter (commits) | `author:john*` |

## Error Responses

All tools return errors in this format:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Repository 'foo.git' not found"
  }
}
```

Common error codes:
- `NOT_FOUND` - Repository or file not found
- `INVALID_REQUEST` - Missing required parameters
- `FILE_TOO_LARGE` - File exceeds 128KB limit
- `ACCESS_DENIED` - No permission to access resource
