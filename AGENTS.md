# Gitblit MCP Server

An MCP (Model Context Protocol) server that provides AI assistants access to Gitblit-hosted Git repositories.

## Project Structure

```
GitblitMCPServer/           # MCP server (Python/FastMCP)
├── src/                    # Python source code
├── tests/                  # Pytest tests
├── docs/                   # Documentation
├── pyproject.toml          # Poetry configuration
├── Dockerfile              # Container build
└── .env.example            # Environment configuration template

../GitblitSearchApiPlugin/  # Companion Java plugin for Gitblit
├── src/main/java/          # Java source code
└── pom.xml                 # Maven build
```

## Architecture

The MCP server is a thin protocol adapter. All repository operations are delegated to the Gitblit Search API Plugin:

- **MCP Server** (Python): Implements MCP protocol, calls Search API Plugin
- **Search API Plugin** (Java): Provides REST API for repository/file/search operations

## Key Files

- `docs/product_brief.md` - Product overview
- `docs/mcp_api.md` - MCP tool specifications
- `docs/mvp_scope.md` - MVP feature scope
- `docs/search_plugin_api.md` - Search plugin REST API specification

## Configuration

The MCP server uses environment variables (supports `.env` files):

- `GITBLIT_URL` - Base URL of Gitblit instance with Search API Plugin

## Development

### MCP Server (Python)

```bash
# Install dependencies
poetry install

# Run server
poetry run python -m gitblit_mcp_server

# Run tests
poetry run pytest

# Lint and type check
poetry run ruff check .
poetry run mypy .
```

### Search API Plugin (Java)

```bash
cd ../GitblitSearchApiPlugin
mvn clean package
# Deploy JAR to Gitblit plugins directory
```

## MCP Tools

The server exposes these tools (see `docs/mcp_api.md` for details):

| Tool | Description |
|------|-------------|
| `gb_list_repos` | List repositories |
| `gb_list_files` | List files in a repository path |
| `gb_read_file` | Read file contents |
| `gb_file_search` | Search file contents |
| `gb_commit_search` | Search commit history |
| `gb_find_files` | Find files by path pattern across repositories |

## Search Plugin API

All MCP tools call the Search API Plugin at `/api/.mcp-internal/*`. See `docs/search_plugin_api.md` for endpoint specifications.

## Conventions

- Repository names include the `.git` suffix (e.g., `team/project.git`)
- File paths are relative to repository root, no leading slash
- Revisions can be branch names, tags, or commit SHAs
- Search uses Gitblit's Lucene index (all indexed branches/tags available)

## MCP Tool Documentation Style

Tool documentation is critical for AI assistant usability. Follow these guidelines:

### Required Documentation

Each MCP tool must have:

1. **Tool description** (`@mcp.tool(description=...)`) - Concise overview with:
   - One-line summary of what the tool does
   - "Behavior:" section listing all default behaviors and edge cases
   - Document what happens when each optional parameter is omitted

2. **Parameter descriptions** (`Annotated[type, Field(description=...)]`) - Each parameter must document:
   - What it does
   - Format/syntax requirements (e.g., "with .git suffix", "no leading slash")
   - Default behavior when omitted (use "Omit to..." phrasing)
   - Limits where applicable (e.g., "max: 100")

### Style Guidelines

- **Keep descriptions concise** - Minimize token usage; avoid examples and verbose explanations
- **Document all defaults** - AI models guess when defaults aren't documented
- **Use consistent phrasing** - "Omit to..." for optional params, "Default: X, max: Y" for limits
- **Reference `docs/sourcegraph_mcp_tools.json`** for comprehensive style examples (but our style is intentionally leaner)

### Example

```python
_TOOL_DESCRIPTION = """
Brief description of what the tool does.

Behavior:
- If paramA is omitted, does X
- If paramB is omitted, uses default branch
- Results are sorted by Y
""".strip()

@mcp.tool(description=_TOOL_DESCRIPTION)
def my_tool(
    required_param: Annotated[
        str,
        Field(description="What this is. Format: X (e.g., 'example')."),
    ],
    optional_param: Annotated[
        int,
        Field(description="What this controls. Default: 25, max: 100."),
    ] = 25,
) -> dict[str, Any]:
    ...
```
