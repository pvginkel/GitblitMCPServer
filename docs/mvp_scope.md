# Gitblit MCP Server - MVP Scope

This document defines the Minimum Viable Product scope for the Gitblit MCP Server.

## MVP Goals

1. Enable AI assistants to browse and search Gitblit repositories
2. Provide a working end-to-end integration with minimal features
3. Validate the architecture before expanding functionality

## In Scope

### MCP Tools

| Tool | Description | Priority |
|------|-------------|----------|
| `gb_list_repos` | List and search repositories | P0 |
| `gb_list_files` | List files in a repository directory | P0 |
| `gb_read_file` | Read file contents | P0 |
| `gb_file_search` | Search file contents (blob search) | P0 |
| `gb_commit_search` | Search commit history | P1 |

### Features

- **Repository listing** with optional name filtering
- **File browsing** at any path within a repository
- **File reading** with line range support for large files
- **Full-text search** across file contents
- **Commit search** by message content and author
- **Revision support** (branches, tags, commit SHAs) for file operations
- **Pagination** for list and search results

### Configuration

- Environment variable configuration (`GITBLIT_URL`)
- Support for `.env` files
- Docker deployment support

## Out of Scope (Future Versions)

The following features are explicitly excluded from MVP:

### Authentication & Authorization
- User authentication (MVP assumes open access or pre-authenticated requests)
- Per-repository access control enforcement

### Advanced Search
- Diff search (searching within code changes)
- Semantic/NLS search
- Symbol search (go to definition, find references)
- Search within specific date ranges

### Code Intelligence
- Go to definition
- Find references
- Symbol extraction

### Repository Operations
- Compare revisions
- Blame/annotation
- Commit details with diffs

### Administrative
- Repository management (create, delete, configure)
- User management
- Webhook/notification support

## Search Plugin API Endpoints (MVP)

The following REST endpoints must be implemented in the Gitblit Search API Plugin:

| Endpoint | MCP Tool | Description |
|----------|----------|-------------|
| `GET /api/mcp-server/repos` | `gb_list_repos` | List repositories |
| `GET /api/mcp-server/files` | `gb_list_files` | List directory contents |
| `GET /api/mcp-server/file` | `gb_read_file` | Read file content |
| `GET /api/mcp-server/search/files` | `gb_file_search` | Search file contents |
| `GET /api/mcp-server/search/commits` | `gb_commit_search` | Search commits |

## Technical Constraints

- **File size limit**: 128KB maximum for `gb_read_file`
- **Search results**: Maximum 100 results per query
- **Pagination**: Cursor-based for large result sets
- **Response format**: JSON with SourceGraph-compatible structure for search results

## Success Criteria

1. All P0 tools functional and tested
2. MCP server successfully connects to Claude Desktop or similar MCP client
3. End-to-end workflow: list repos -> list files -> read file -> search
4. Docker image builds and runs successfully
5. Documentation complete for setup and usage
