# Gitblit MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with access to Gitblit-hosted Git repositories.

## Overview

Gitblit MCP Server is a thin protocol adapter that translates MCP tool calls into HTTP requests to the Gitblit Search API Plugin. It enables AI assistants to browse repositories, read files, and search code and commit history hosted on Gitblit instances.

## Features

- **Repository Discovery**: List and search available repositories
- **File Browsing**: Navigate directory structures and list files within repositories
- **File Content Access**: Read file contents with support for line ranges and revisions
- **File Search**: Full-text search across file contents using Lucene
- **Commit Search**: Search commit history by message content and metadata

## Requirements

- Python 3.10 or higher
- Poetry for dependency management
- Gitblit instance with the Search API Plugin installed and running

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd GitblitMCPServer
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Configure the server by creating a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

4. Edit `.env` and set your Gitblit URL:
```env
GITBLIT_URL=http://10.1.2.3:8080
```

## Usage

Start the MCP server:

```bash
poetry run python -m gitblit_mcp_server
```

The server will:
- Validate configuration on startup
- Display connection information
- Run as an MCP server listening on stdio for protocol messages

## Configuration

The server is configured via environment variables (can be set in `.env` file):

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GITBLIT_URL` | Yes | Base URL of Gitblit instance | `http://10.1.2.3:8080` |

## MCP Tools

The server exposes these MCP tools:

### list_repos
List repositories available in the Gitblit instance.

**Parameters:**
- `query` (optional): Search query to filter repositories by name
- `limit` (optional): Maximum results to return (default: 50)
- `after` (optional): Pagination cursor

### list_files
List files and directories in a repository path.

**Parameters:**
- `repo` (required): Repository name (e.g., 'team/project.git')
- `path` (optional): Directory path within repository (default: root)
- `revision` (optional): Branch, tag, or commit SHA (default: HEAD)

### read_file
Read the content of a file from a repository.

**Parameters:**
- `repo` (required): Repository name
- `path` (required): File path within repository
- `revision` (optional): Branch, tag, or commit SHA (default: HEAD)
- `startLine` (optional): 1-based starting line number
- `endLine` (optional): 1-based ending line number (inclusive)

**Note:** Files larger than 128KB will return an error.

### file_search
Search for content within files across repositories.

**Parameters:**
- `query` (required): Search query (supports Lucene syntax)
- `repos` (optional): Repository names to search (default: all)
- `pathPattern` (optional): File path pattern filter (e.g., '*.java')
- `branch` (optional): Branch filter (e.g., 'refs/heads/main')
- `count` (optional): Maximum results (default: 25)
- `contextLines` (optional): Lines of context around matches (default: 100)

### commit_search
Search commit history across repositories.

**Parameters:**
- `query` (required): Search query (supports Lucene syntax)
- `repos` (required): Repository names to search
- `authors` (optional): Filter by author names
- `branch` (optional): Branch filter
- `count` (optional): Maximum results (default: 25)

## Development

### Running Tests

Run the test suite against a live Gitblit server:

```bash
# Configure test server URL in tests/.env.test
poetry run pytest
```

Tests are written to run against a live Gitblit server at `http://10.1.2.3:8080` by default. Update `tests/.env.test` to point to your test server.

### Code Quality

Run linting and type checking:

```bash
# Run ruff linter
poetry run ruff check .

# Run mypy type checker
poetry run mypy src
```

## Architecture

```
┌─────────────────┐     MCP Protocol      ┌─────────────────────┐
│   MCP Client    │◄────────────────────►│  Gitblit MCP Server │
│  (AI Assistant) │                       │    (Python/FastMCP) │
└─────────────────┘                       └──────────┬──────────┘
                                                     │ HTTP/JSON
                                                     ▼
                                          ┌─────────────────────┐
                                          │  Gitblit Search     │
                                          │   API Plugin        │
                                          │     (Java)          │
                                          └──────────┬──────────┘
                                                     │
                                                     ▼
                                          ┌─────────────────────┐
                                          │      Gitblit        │
                                          │  (Git Repositories) │
                                          └─────────────────────┘
```

The MCP server is a stateless protocol adapter with no business logic - all operations are delegated to the Gitblit Search API Plugin.

## Project Structure

```
GitblitMCPServer/
├── src/gitblit_mcp_server/     # Python source code
│   ├── __init__.py             # Package initialization
│   ├── __main__.py             # Entry point
│   ├── server.py               # FastMCP server setup
│   ├── config.py               # Configuration management
│   ├── client.py               # HTTP client for Search API
│   ├── schemas.py              # Pydantic models
│   └── tools/                  # MCP tool implementations
│       ├── list_repos.py
│       ├── list_files.py
│       ├── read_file.py
│       ├── file_search.py
│       └── commit_search.py
├── tests/                      # Pytest tests
├── docs/                       # Documentation
├── pyproject.toml             # Poetry configuration
└── .env.example               # Environment configuration template
```

## Contributing

Contributions are welcome! Please ensure:

1. Code passes ruff linting: `poetry run ruff check .`
2. Code passes mypy type checking: `poetry run mypy src`
3. All tests pass: `poetry run pytest`

## License

See LICENSE file for details.

## Related Projects

- **Gitblit Search API Plugin**: Companion Java plugin that provides the REST API backend (located in `../GitblitSearchApiPlugin/`)

## Documentation

- `docs/product_brief.md` - Product overview
- `docs/mcp_api.md` - MCP tool specifications
- `docs/search_plugin_api.md` - Search Plugin REST API specification
