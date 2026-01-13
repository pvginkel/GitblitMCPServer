# Gitblit MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with access to Gitblit-hosted Git repositories.

> **Warning**
>
> **This project is experimental and provided as-is. Use at your own risk.**
>
> This MCP server requires the [GitblitMCPSupportPlugin](https://github.com/pvginkel/GitblitMCPSupportPlugin) to be installed on your Gitblit instance.
>
> **Important architectural note:** This Python-based MCP server exists as a proof-of-concept. The recommended long-term approach would be to integrate MCP support directly into Gitblit's Java codebase using a [Java MCP SDK](https://modelcontextprotocol.io/sdk/java/mcp-overview). This would eliminate the need for a separate service and provide a more maintainable solution. This project may be deprecated if native MCP support is added to Gitblit.

## Overview

Gitblit MCP Server is a thin protocol adapter that translates MCP tool calls into HTTP requests to the GitblitMCPSupportPlugin. It enables AI assistants to:

- **Browse repositories**: List and search available repositories
- **Navigate files**: Browse directory structures and list files
- **Read content**: Access file contents with line range and revision support
- **Search code**: Full-text search across file contents using Lucene
- **Search commits**: Query commit history by message and metadata

## Requirements

- Gitblit instance with [GitblitMCPSupportPlugin](https://github.com/pvginkel/GitblitMCPSupportPlugin) installed
- Python 3.10+ (for local installation) or Docker

## Installation

### Docker (Recommended)

```bash
docker build -t gitblit-mcp-server .
docker run -d \
  -e GITBLIT_URL=http://your-gitblit-host:8080 \
  -p 8000:8000 \
  gitblit-mcp-server
```

### Local Installation

```bash
# Clone the repository
git clone https://github.com/pvginkel/GitblitMCPServer.git
cd GitblitMCPServer

# Install dependencies
poetry install

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
poetry run python -m gitblit_mcp_server
```

## Configuration

Configure via environment variables or a `.env` file:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITBLIT_URL` | Yes | - | Base URL of your Gitblit instance (e.g., `http://10.1.2.3:8080`) |
| `MCP_PORT` | No | `8000` | Port for the MCP server HTTP endpoint |
| `MCP_HOST` | No | `0.0.0.0` | Host to bind to (use `127.0.0.1` for local-only access) |
| `MCP_PATH_PREFIX` | No | - | Path prefix for reverse proxy setups (e.g., `/api/mcp`) |

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_repos` | List repositories matching an optional search query |
| `list_files` | List files and directories at a repository path |
| `read_file` | Read file contents (supports line ranges, max 128KB) |
| `file_search` | Full-text search across file contents |
| `commit_search` | Search commit history by message/metadata |

## Architecture

```
┌─────────────────┐     MCP Protocol      ┌─────────────────────┐
│   MCP Client    │◄────────────────────►│  Gitblit MCP Server │
│  (AI Assistant) │                       │       (Python)      │
└─────────────────┘                       └──────────┬──────────┘
                                                     │ HTTP/JSON
                                                     ▼
                                          ┌─────────────────────┐
                                          │ GitblitMCPSupport   │
                                          │      Plugin         │
                                          └──────────┬──────────┘
                                                     │
                                                     ▼
                                          ┌─────────────────────┐
                                          │      Gitblit        │
                                          │  (Git Repositories) │
                                          └─────────────────────┘
```

## Development

```bash
# Run tests (requires configured Gitblit instance)
poetry run pytest

# Lint
poetry run ruff check .

# Type check
poetry run mypy src
```

## License

See LICENSE file for details.

## Related Projects

- [GitblitMCPSupportPlugin](https://github.com/pvginkel/GitblitMCPSupportPlugin) - Required Gitblit plugin providing the REST API backend
