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

../GitblitMCPSupportPlugin/ # Companion Java plugin for Gitblit
├── src/main/java/          # Java source code
└── pom.xml                 # Maven build
```

The plugin is cloned alongside this repo in the KubeCoder environment
(`.kubecoder/config.yaml`), so `../GitblitMCPSupportPlugin` is a real path here.

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

The curated entry points are in `.kubecoder/project.yaml`; prefer them over
ad-hoc commands:

```bash
kc project setup   # poetry install
kc project build   # build the container image with kaniko
kc project test    # pytest
kc project lint    # ruff, mypy, and the architecture artifact validation
```

Python lives in the `python` tool container, so a one-off command is prefixed
with `cexec python`:

```bash
# Run the server
cexec python poetry run python -m gitblit_mcp_server

# Run part of the suite
cexec python poetry run pytest tests/test_config.py
```

### MCP Support Plugin (Java)

Maven lives in the `java` tool container. The plugin has its own curated
automation:

```bash
cd ../GitblitMCPSupportPlugin
kc project setup   # seed the Gitblit JAR into the local Maven repository
kc project build   # mvn clean package -DskipTests
# Deploy target/mcp-support-plugin-*.zip to the Gitblit plugins directory
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

## Federated architecture model

We take part in a federated Architecture-as-Code model. The architecture for this repository is maintained in `docs/architecture/architecture.yaml`. Whenever a change is made in this repo that could impact an Enterprise Architecture / ArchiMate model modeling everything owned by this repo, nudge the user to spawn the `update-architecture` agent. The agent is incremental, so it's not a hard requirement that it runs on every change. Nudge a bit harder when significant changes are made (new managed host, new daemon, removed service, renamed external identity). When you are performing work unattended, feel free to invoke the agent yourself.

The tooling is installed on the operator's filesystem (not in this repo): the `/seed-architecture` skill (one-shot, authors the first artifact) and the `update-architecture` agent (permanent, incremental). Generated producers — those whose `docs/architecture/*.yaml` is a build output from a generator + annotation layer — use the `update-architecture-generated` agent instead, which edits the annotations and never the output. The producer manual at `~/.claude/architecture/producer-manual.md` is the authoritative vocabulary reference; the skill and agents read it from the operator's filesystem on startup.
