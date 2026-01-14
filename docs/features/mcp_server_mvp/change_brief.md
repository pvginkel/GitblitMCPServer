# Change Brief: MCP Server MVP Implementation

## Overview

Build the MVP version of the Gitblit MCP Server - a Python/FastMCP server that provides AI assistants access to Gitblit-hosted Git repositories via MCP (Model Context Protocol).

## Functional Requirements

The MCP server is a thin protocol adapter that translates MCP tool calls into HTTP requests to the Gitblit Search API Plugin (already deployed at `http://10.1.2.3`).

### MCP Tools to Implement

| Tool | Priority | Description |
|------|----------|-------------|
| `gb_list_repos` | P0 | List and search repositories |
| `gb_list_files` | P0 | List files in a repository directory |
| `gb_read_file` | P0 | Read file contents |
| `gb_file_search` | P0 | Search file contents (blob search) |
| `gb_commit_search` | P1 | Search commit history |

### Configuration

- Use environment variables with `.env` file support
- `GITBLIT_URL` - Base URL of Gitblit instance (e.g., `http://10.1.2.3`)

### Testing

- Write pytest tests against the live test server at `http://10.1.2.3`
- Use `.env` file to provide the server URL
- Tests should cover success paths, error conditions, and edge cases

## Reference Documentation

- `docs/mcp_api.md` - MCP tool specifications (input/output schemas)
- `docs/search_plugin_api.md` - REST API endpoints the server calls
- `docs/mvp_scope.md` - MVP feature scope
- `CLAUDE.md` - Project structure and conventions

## Success Criteria

1. All 5 MCP tools functional and tested
2. MCP server can be started with `poetry run python -m gitblit_mcp_server`
3. Tests pass against the live test server
4. Code passes `ruff check` and `mypy` checks
