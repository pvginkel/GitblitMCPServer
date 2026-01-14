# Plan: MCP Server MVP Implementation

## 0) Research Log & Findings

### Discovery Summary

I researched the following areas to inform this plan:

1. **MCP Tool Specifications** (`docs/mcp_api.md`): Complete specifications for all 5 MCP tools with input/output schemas, descriptions, and examples. All tools are clearly defined with specific parameter requirements and response structures.

2. **Search API Plugin Endpoints** (`docs/search_plugin_api.md`): REST API specification for the backend that the MCP server will call. All endpoints are defined at `/api/.mcp-internal/*` with query parameters, response formats, and error handling.

3. **MVP Scope** (`docs/mvp_scope.md`): Clear definition of what's in/out of scope. P0 tools are gb_list_repos, gb_list_files, gb_read_file, and gb_file_search. P1 is gb_commit_search. Authentication and advanced features are explicitly out of scope.

4. **FastMCP Framework** (web research): FastMCP is a high-level Python framework that simplifies MCP server development through decorators and automatic schema generation from type hints. It handles protocol details and provides production-ready features.

5. **Project Structure** (CLAUDE.md): The project uses Poetry for dependency management, pytest for testing, and expects the server to be runnable as `python -m gitblit_mcp_server`. Configuration via environment variables with .env file support.

### Key Findings

- **Thin Adapter Pattern**: The MCP server is explicitly designed as a thin protocol adapter with no business logic - all operations delegate to the Search API Plugin
- **Direct API Mapping**: Each MCP tool maps 1:1 to a Search API Plugin endpoint with minimal transformation
- **Live Testing**: Tests will run against a live test server at `http://10.1.2.3` rather than mocking
- **No Repository Structure**: The project has no Python source code yet - this is a greenfield implementation
- **Clear Conventions**: Repository names include `.git` suffix, file paths are relative without leading slash, revisions can be branch/tag/SHA

### Areas of Special Interest

1. **Error Handling Consistency**: MCP tools expect structured error responses (`{error: {code, message}}`) while the Search API Plugin returns `{error, status}`. Need transformation logic.

2. **Line Numbering**: Both `gb_read_file` output and `gb_file_search` chunk content include line number prefixes. Need consistent formatting logic.

3. **Pagination**: `gb_list_repos` supports cursor-based pagination through `after/endCursor` parameters.

4. **Testing Strategy**: All tests against live server means no mock data needed but requires careful fixture management and idempotent test design.

## 1) Intent & Scope

**User intent**

Build the MVP version of Gitblit MCP Server - a Python/FastMCP application that acts as a thin protocol adapter, translating Model Context Protocol tool calls into HTTP requests to the Gitblit Search API Plugin. The server enables AI assistants to browse repositories, read files, and search code/commits hosted on a Gitblit instance.

**Prompt quotes**

- "Build the MVP version of the Gitblit MCP Server"
- "MCP server is a thin protocol adapter that translates MCP tool calls into HTTP requests"
- "Write pytest tests against the live test server at `http://10.1.2.3`"
- "Server can be started with `poetry run python -m gitblit_mcp_server`"
- "Code passes ruff check and mypy type checking"

**In scope**

- Implement 5 MCP tools (gb_list_repos, gb_list_files, gb_read_file, gb_file_search, gb_commit_search)
- FastMCP server setup with proper tool registration
- HTTP client for calling Search API Plugin endpoints
- Environment variable configuration with .env file support (GITBLIT_URL)
- Pytest test suite against live server at http://10.1.2.3
- Poetry project setup with dependencies (fastmcp, httpx, python-dotenv, pytest)
- Code quality compliance (ruff, mypy)
- Runnable as Python module: `python -m gitblit_mcp_server`

**Out of scope**

- Authentication/authorization (Search API Plugin handles this)
- Business logic or data transformation beyond protocol translation
- Caching or performance optimizations
- Advanced error recovery (retries, circuit breakers)
- Logging beyond basic error capture
- Metrics/observability infrastructure
- Docker image creation (Dockerfile exists, implementation separate)
- CI/CD configuration

**Assumptions / constraints**

- Search API Plugin is already deployed and functional at http://10.1.2.3
- Test repositories and data exist on the test Gitblit instance
- Direct HTTP requests without connection pooling or advanced networking (MVP simplicity)
- Python 3.10+ environment
- FastMCP framework handles MCP protocol details (schema validation, transport, etc.)
- .env file placed in working directory where server starts

## 1a) User Requirements Checklist

**User Requirements Checklist**

- [ ] Implement `gb_list_repos` MCP tool to list and search repositories
- [ ] Implement `gb_list_files` MCP tool to list files in a repository path
- [ ] Implement `gb_read_file` MCP tool to read file contents with line range support
- [ ] Implement `gb_file_search` MCP tool to search file contents
- [ ] Implement `gb_commit_search` MCP tool to search commit history
- [ ] Use environment variables with .env file support for configuration
- [ ] GITBLIT_URL environment variable to configure the server URL
- [ ] Write pytest tests against the live test server at http://10.1.2.3
- [ ] Use .env file to provide server URL for tests
- [ ] Server can be started with `poetry run python -m gitblit_mcp_server`
- [ ] Code passes ruff check and mypy type checking

## 2) Affected Areas & File Map

### New Files to Create

- **Area:** `src/gitblit_mcp_server/__init__.py`
- **Why:** Package initialization, exports main server instance
- **Evidence:** CLAUDE.md:11 specifies "src/" directory for Python source code

---

- **Area:** `src/gitblit_mcp_server/__main__.py`
- **Why:** Entry point for `python -m gitblit_mcp_server` execution
- **Evidence:** docs/features/mcp_server_mvp/change_brief.md:42 requires "MCP server can be started with `poetry run python -m gitblit_mcp_server`"

---

- **Area:** `src/gitblit_mcp_server/server.py`
- **Why:** FastMCP server setup and tool registration
- **Evidence:** docs/mcp_api.md defines 5 tools (gb_list_repos:7-103, gb_list_files:106-178, gb_read_file:181-251, gb_file_search:254-372, gb_commit_search:375-471)

---

- **Area:** `src/gitblit_mcp_server/config.py`
- **Why:** Load and validate environment configuration (GITBLIT_URL)
- **Evidence:** docs/features/mcp_server_mvp/change_brief.md:21-24 specifies environment variables with .env support

---

- **Area:** `src/gitblit_mcp_server/client.py`
- **Why:** HTTP client wrapper for Search API Plugin endpoints
- **Evidence:** docs/search_plugin_api.md defines 5 endpoints (/repos:30, /files:70, /file:109, /search/files:146, /search/commits:198)

---

- **Area:** `src/gitblit_mcp_server/schemas.py`
- **Why:** Pydantic models for request/response validation and type safety
- **Evidence:** docs/mcp_api.md provides JSON schemas for all tools; mypy requirement from change_brief.md:44

---

- **Area:** `src/gitblit_mcp_server/tools/list_repos.py`
- **Why:** Implement gb_list_repos MCP tool
- **Evidence:** docs/mcp_api.md:7-103 defines input schema (query, limit, after) and output schema (repositories, pagination)

---

- **Area:** `src/gitblit_mcp_server/tools/list_files.py`
- **Why:** Implement gb_list_files MCP tool
- **Evidence:** docs/mcp_api.md:106-178 defines input schema (repo, path, revision) and output (files array)

---

- **Area:** `src/gitblit_mcp_server/tools/read_file.py`
- **Why:** Implement gb_read_file MCP tool with line range support
- **Evidence:** docs/mcp_api.md:181-251 defines input schema (repo, path, revision, startLine, endLine) and output (content with line numbers)

---

- **Area:** `src/gitblit_mcp_server/tools/file_search.py`
- **Why:** Implement gb_file_search MCP tool
- **Evidence:** docs/mcp_api.md:254-372 defines input schema (query, repos, pathPattern, branch, count, contextLines) and output (query, totalCount, results with chunks)

---

- **Area:** `src/gitblit_mcp_server/tools/commit_search.py`
- **Why:** Implement gb_commit_search MCP tool
- **Evidence:** docs/mcp_api.md:375-471 defines input schema (query, repos, authors, branch, count) and output (query, totalCount, commits)

---

- **Area:** `tests/conftest.py`
- **Why:** Pytest fixtures for test configuration and shared test utilities
- **Evidence:** docs/features/mcp_server_mvp/change_brief.md:27-30 requires tests against live server with .env configuration

---

- **Area:** `tests/test_list_repos.py`
- **Why:** Test gb_list_repos tool against live server
- **Evidence:** docs/features/mcp_server_mvp/change_brief.md:30 requires tests covering success paths, error conditions, edge cases

---

- **Area:** `tests/test_list_files.py`
- **Why:** Test gb_list_files tool against live server
- **Evidence:** docs/features/mcp_server_mvp/change_brief.md:30 requires tests covering success paths, error conditions, edge cases

---

- **Area:** `tests/test_read_file.py`
- **Why:** Test gb_read_file tool with line range scenarios
- **Evidence:** docs/mcp_api.md:215-222 specifies startLine/endLine parameters; change_brief.md:30 requires edge case testing

---

- **Area:** `tests/test_file_search.py`
- **Why:** Test gb_file_search tool with various query patterns
- **Evidence:** docs/mcp_api.md:269-301 lists complex search parameters; change_brief.md:30 requires comprehensive testing

---

- **Area:** `tests/test_commit_search.py`
- **Why:** Test gb_commit_search tool with author and branch filters
- **Evidence:** docs/mcp_api.md:389-419 defines filter parameters; mvp_scope.md:21 marks as P1 priority

---

- **Area:** `tests/.env.test`
- **Why:** Test environment configuration for live server URL
- **Evidence:** docs/features/mcp_server_mvp/change_brief.md:28-29 "Use `.env` file to provide the server URL"

---

- **Area:** `pyproject.toml`
- **Why:** Poetry project configuration with dependencies and tool settings
- **Evidence:** CLAUDE.md:25 mentions "pyproject.toml # Poetry configuration"; change_brief.md:44 requires ruff and mypy configuration

---

- **Area:** `.env.example`
- **Why:** Template for environment configuration
- **Evidence:** CLAUDE.md:27 references ".env.example # Environment configuration template"

---

- **Area:** `README.md` (update if exists, create if not)
- **Why:** Document server startup, configuration, and testing
- **Evidence:** Standard practice for project documentation; change_brief.md:42-43 specifies startup command

## 3) Data Model / Contracts

### MCP Tool Input Schemas

- **Entity / contract:** gb_list_repos input
- **Shape:**
  ```json
  {
    "query": "string (optional)",
    "limit": "integer (optional, default: 50)",
    "after": "string (optional)"
  }
  ```
- **Refactor strategy:** New schema, no backward compatibility needed (greenfield)
- **Evidence:** docs/mcp_api.md:22-40

---

- **Entity / contract:** gb_list_files input
- **Shape:**
  ```json
  {
    "repo": "string (required)",
    "path": "string (optional, default: root)",
    "revision": "string (optional, default: HEAD)"
  }
  ```
- **Refactor strategy:** New schema, no backward compatibility needed
- **Evidence:** docs/mcp_api.md:121-139

---

- **Entity / contract:** gb_read_file input
- **Shape:**
  ```json
  {
    "repo": "string (required)",
    "path": "string (required)",
    "revision": "string (optional, default: HEAD)",
    "startLine": "integer (optional, 1-based)",
    "endLine": "integer (optional, 1-based, inclusive)"
  }
  ```
- **Refactor strategy:** New schema, no backward compatibility needed
- **Evidence:** docs/mcp_api.md:197-224

---

- **Entity / contract:** gb_file_search input
- **Shape:**
  ```json
  {
    "query": "string (required)",
    "repos": "array<string> (optional, default: all)",
    "pathPattern": "string (optional)",
    "branch": "string (optional)",
    "count": "integer (optional, default: 25)",
    "contextLines": "integer (optional, default: 100)"
  }
  ```
- **Refactor strategy:** New schema, no backward compatibility needed
- **Evidence:** docs/mcp_api.md:270-301

---

- **Entity / contract:** gb_commit_search input
- **Shape:**
  ```json
  {
    "query": "string (required)",
    "repos": "array<string> (required)",
    "authors": "array<string> (optional)",
    "branch": "string (optional)",
    "count": "integer (optional, default: 25)"
  }
  ```
- **Refactor strategy:** New schema, no backward compatibility needed
- **Evidence:** docs/mcp_api.md:390-419

### MCP Tool Output Schemas

- **Entity / contract:** gb_list_repos output
- **Shape:**
  ```json
  {
    "repositories": [
      {
        "name": "string",
        "description": "string",
        "lastChange": "string (ISO 8601)",
        "hasCommits": "boolean"
      }
    ],
    "pagination": {
      "totalCount": "integer",
      "hasNextPage": "boolean",
      "endCursor": "string (optional)"
    }
  }
  ```
- **Refactor strategy:** Direct pass-through from Search API Plugin response
- **Evidence:** docs/mcp_api.md:45-91, docs/search_plugin_api.md:44-59

---

- **Entity / contract:** gb_list_files output
- **Shape:**
  ```json
  {
    "files": [
      {
        "path": "string (directories end with /)",
        "isDirectory": "boolean"
      }
    ]
  }
  ```
- **Refactor strategy:** Direct pass-through from Search API Plugin response
- **Evidence:** docs/mcp_api.md:144-166, docs/search_plugin_api.md:84-96

---

- **Entity / contract:** gb_read_file output
- **Shape:**
  ```json
  {
    "content": "string (format: 'N: line\\n' with 1-based line numbers)"
  }
  ```
- **Refactor strategy:** Direct pass-through from Search API Plugin response
- **Evidence:** docs/mcp_api.md:229-239, docs/search_plugin_api.md:125-129

---

- **Entity / contract:** gb_file_search output
- **Shape:**
  ```json
  {
    "query": "string",
    "totalCount": "integer",
    "limitHit": "boolean",
    "results": [
      {
        "repository": "string",
        "path": "string",
        "branch": "string",
        "commitId": "string",
        "chunks": [
          {
            "startLine": "integer (1-based)",
            "endLine": "integer (1-based, inclusive)",
            "content": "string (format: 'N: line\\n')"
          }
        ]
      }
    ]
  }
  ```
- **Refactor strategy:** Direct pass-through from Search API Plugin response
- **Evidence:** docs/mcp_api.md:306-357, docs/search_plugin_api.md:165-186

---

- **Entity / contract:** gb_commit_search output
- **Shape:**
  ```json
  {
    "query": "string",
    "totalCount": "integer",
    "limitHit": "boolean",
    "commits": [
      {
        "repository": "string",
        "commit": "string (SHA)",
        "author": "string",
        "committer": "string",
        "date": "string (ISO 8601)",
        "title": "string",
        "message": "string",
        "branch": "string"
      }
    ]
  }
  ```
- **Refactor strategy:** Direct pass-through from Search API Plugin response
- **Evidence:** docs/mcp_api.md:425-456, docs/search_plugin_api.md:216-234

### Error Response Transformation

- **Entity / contract:** Error response conversion
- **Shape:**
  ```json
  // MCP expected format
  {"error": {"code": "NOT_FOUND", "message": "..."}}

  // Search API format
  {"error": "...", "status": 404}

  // HTTP status to error code mapping:
  // 404 -> NOT_FOUND
  // 400 -> INVALID_REQUEST
  // 403 -> ACCESS_DENIED
  // 500 -> INTERNAL_ERROR
  ```
- **Refactor strategy:** Transform Search API Plugin errors to MCP format in client layer
- **Evidence:** docs/mcp_api.md:490-505, docs/search_plugin_api.md:12-24

### Configuration Schema

- **Entity / contract:** Environment configuration
- **Shape:**
  ```python
  GITBLIT_URL: str  # Required, base URL like "http://10.1.2.3"
  ```
- **Refactor strategy:** New configuration, validated on startup, fail-fast if missing
- **Evidence:** docs/features/mcp_server_mvp/change_brief.md:21-24

## 4) API / Integration Surface

### MCP Server Startup

- **Surface:** Python module execution `python -m gitblit_mcp_server`
- **Inputs:** None (reads GITBLIT_URL from environment/env file)
- **Outputs:** MCP server listening on stdio for protocol messages
- **Errors:** Exit with error if GITBLIT_URL not configured or invalid URL format
- **Evidence:** docs/features/mcp_server_mvp/change_brief.md:42, FastMCP framework handles stdio transport

---

### Search API Plugin HTTP Endpoints

- **Surface:** GET /api/.mcp-internal/repos
- **Inputs:** Query params (query, limit, after)
- **Outputs:** JSON with repositories array and pagination object
- **Errors:** 400 (invalid params), 500 (server error)
- **Evidence:** docs/search_plugin_api.md:30-66

---

- **Surface:** GET /api/.mcp-internal/files
- **Inputs:** Query params (repo, path, revision)
- **Outputs:** JSON with files array
- **Errors:** 404 (repo not found), 400 (invalid params)
- **Evidence:** docs/search_plugin_api.md:70-105

---

- **Surface:** GET /api/.mcp-internal/file
- **Inputs:** Query params (repo, path, revision, startLine, endLine)
- **Outputs:** JSON with content string (line-numbered)
- **Errors:** 404 (repo/file not found), 400 (file too large >128KB or invalid range)
- **Evidence:** docs/search_plugin_api.md:109-142

---

- **Surface:** GET /api/.mcp-internal/search/files
- **Inputs:** Query params (query, repos comma-separated, pathPattern, branch, count, contextLines)
- **Outputs:** JSON with query, totalCount, limitHit, results array with chunks
- **Errors:** 400 (invalid query syntax or params), 500 (search error)
- **Evidence:** docs/search_plugin_api.md:146-194

---

- **Surface:** GET /api/.mcp-internal/search/commits
- **Inputs:** Query params (query, repos comma-separated, authors comma-separated, branch, count)
- **Outputs:** JSON with query, totalCount, limitHit, commits array
- **Errors:** 400 (missing repos or invalid query), 500 (search error)
- **Evidence:** docs/search_plugin_api.md:198-240

## 5) Algorithms & State Machines

### Tool Execution Flow (all tools follow this pattern)

- **Flow:** MCP tool invocation to Search API response
- **Steps:**
  1. FastMCP framework receives tool call from MCP client over stdio
  2. Framework validates input against tool's type hints and calls tool function
  3. Tool function calls client method with validated parameters
  4. Client constructs HTTP GET request with query parameters
  5. Client sends request to Search API Plugin endpoint at GITBLIT_URL base
  6. Client receives HTTP response (200 success or error status)
  7. If error status, client transforms to MCP error format {error: {code, message}}
  8. If success, client parses JSON response body
  9. Tool function returns parsed response
  10. FastMCP framework serializes response and sends to MCP client
- **States / transitions:** None (stateless request-response)
- **Hotspots:** HTTP request timeout (default 30s), no retry logic in MVP, JSON parsing errors
- **Evidence:** FastMCP framework docs, docs/search_plugin_api.md:8-24

---

### Configuration Loading

- **Flow:** Server startup configuration validation
- **Steps:**
  1. Server startup triggers config.py import
  2. Load environment variables from .env file if present (python-dotenv)
  3. Read GITBLIT_URL environment variable
  4. Validate GITBLIT_URL is not empty
  5. Validate GITBLIT_URL is valid HTTP/HTTPS URL format
  6. Store validated URL for use by client
  7. If validation fails, raise exception and exit
- **States / transitions:** None (one-time startup)
- **Hotspots:** File I/O for .env, process exit on misconfiguration
- **Evidence:** docs/features/mcp_server_mvp/change_brief.md:21-24

---

### Error Response Transformation

- **Flow:** HTTP error to MCP error conversion
- **Steps:**
  1. HTTP client receives non-2xx status code
  2. Parse JSON response body to extract error message
  3. Map HTTP status to MCP error code:
     - 404 -> "NOT_FOUND"
     - 400 -> "INVALID_REQUEST"
     - 403 -> "ACCESS_DENIED"
     - 500 -> "INTERNAL_ERROR"
     - Other -> "INTERNAL_ERROR"
  4. Construct MCP error format: {error: {code, message}}
  5. Return error dict to tool function
  6. Tool function can return error directly (FastMCP handles error responses)
- **States / transitions:** None (per-request transformation)
- **Hotspots:** Malformed error responses from plugin, missing error message field
- **Evidence:** docs/mcp_api.md:490-505, docs/search_plugin_api.md:12-18

## 6) Derived State & Invariants

### No Derived State in MVP

The MCP server is a stateless protocol adapter with no derived state:

- **No caching:** Every request fetches fresh data from Search API Plugin
- **No session management:** No user sessions or request correlation beyond single tool call
- **No aggregations:** All data structures are direct pass-throughs from plugin responses
- **No background processing:** No async jobs, queues, or scheduled tasks
- **No persistence:** No database or file storage

This is justified by MVP scope focusing on basic protocol translation without optimization. Future versions may add caching or request batching.

**Evidence:** docs/features/mcp_server_mvp/change_brief.md:8-9 "thin protocol adapter that translates MCP tool calls into HTTP requests"

## 7) Consistency, Transactions & Concurrency

### No Transaction Management

- **Transaction scope:** None - all operations are read-only HTTP GET requests
- **Atomic requirements:** None - each tool invocation is independent
- **Retry / idempotency:** No retry logic in MVP; all operations naturally idempotent (reads)
- **Ordering / concurrency controls:** None - stateless server can handle concurrent requests
- **Evidence:** docs/search_plugin_api.md:281 mentions GET methods only; thin adapter pattern from change_brief.md:8-9

### Concurrency Behavior

The MCP server can handle multiple concurrent tool invocations from the MCP client. Each tool call:
- Creates independent HTTP request to Search API Plugin
- No shared state between requests
- FastMCP framework handles concurrent request scheduling
- HTTP client may have connection limits (httpx default pool size)

**Constraint:** If many concurrent requests hit Search API Plugin, that backend service handles queuing/rate limiting.

## 8) Errors & Edge Cases

### Configuration Errors

- **Failure:** GITBLIT_URL environment variable not set
- **Surface:** Server startup (before MCP protocol begins)
- **Handling:** Exit process with error message "GITBLIT_URL environment variable required"
- **Guardrails:** Check at startup, .env.example template documents required variable
- **Evidence:** docs/features/mcp_server_mvp/change_brief.md:21-24

---

- **Failure:** GITBLIT_URL is invalid URL format
- **Surface:** Server startup
- **Handling:** Exit process with error message "Invalid GITBLIT_URL format: must be http:// or https://"
- **Guardrails:** URL validation regex or urllib.parse validation
- **Evidence:** Inferred from configuration requirements

---

### Repository/File Not Found

- **Failure:** Repository or file doesn't exist
- **Surface:** gb_list_files, gb_read_file tools
- **Handling:** Return MCP error {error: {code: "NOT_FOUND", message: "Repository 'x.git' not found"}}
- **Guardrails:** Search API Plugin returns 404, client transforms to MCP format
- **Evidence:** docs/mcp_api.md:502, docs/search_plugin_api.md:135

---

### File Size Limit Exceeded

- **Failure:** File larger than 128KB
- **Surface:** gb_read_file tool
- **Handling:** Return MCP error {error: {code: "FILE_TOO_LARGE", message: "File exceeds 128KB limit"}}
- **Guardrails:** Search API Plugin enforces limit, returns 400
- **Evidence:** docs/mcp_api.md:504, docs/search_plugin_api.md:136

---

### Invalid Line Range

- **Failure:** startLine > endLine or negative line numbers
- **Surface:** gb_read_file tool
- **Handling:** Return MCP error {error: {code: "INVALID_REQUEST", message: "Invalid line range"}}
- **Guardrails:** Client-side validation before making request, or plugin returns 400
- **Evidence:** docs/mcp_api.md:215-222

---

### Invalid Search Query Syntax

- **Failure:** Malformed Lucene query
- **Surface:** gb_file_search, gb_commit_search tools
- **Handling:** Return MCP error {error: {code: "INVALID_REQUEST", message: "Invalid query syntax"}}
- **Guardrails:** Search API Plugin validates Lucene syntax, returns 400
- **Evidence:** docs/search_plugin_api.md:244-275

---

### Missing Required Parameters

- **Failure:** repos array empty for gb_commit_search
- **Surface:** gb_commit_search tool
- **Handling:** FastMCP validates required parameters before calling tool function, returns error to client
- **Guardrails:** Type hints on tool function enforce required parameters
- **Evidence:** docs/mcp_api.md:404 shows repos as required

---

### Network Failures

- **Failure:** Cannot connect to Search API Plugin (connection refused, timeout)
- **Surface:** All tools
- **Handling:** Return MCP error {error: {code: "INTERNAL_ERROR", message: "Failed to connect to Gitblit server"}}
- **Guardrails:** HTTP client timeout (30s), catch connection exceptions
- **Evidence:** Inferred from HTTP communication

---

### Malformed JSON Response

- **Failure:** Search API Plugin returns invalid JSON
- **Surface:** All tools
- **Handling:** Return MCP error {error: {code: "INTERNAL_ERROR", message: "Invalid response from server"}}
- **Guardrails:** JSON parsing with exception handling
- **Evidence:** Inferred from JSON response handling

---

### Access Denied

- **Failure:** User doesn't have permission to access repository
- **Surface:** All tools that take repo parameter
- **Handling:** Return MCP error {error: {code: "ACCESS_DENIED", message: "No permission to access resource"}}
- **Guardrails:** Search API Plugin returns 403, client transforms to MCP format
- **Evidence:** docs/mcp_api.md:505

## 9) Observability / Telemetry

### MVP Observability

The MVP focuses on minimal observability sufficient for development and basic troubleshooting:

- **Signal:** Error logging to stderr
- **Type:** Structured log entries
- **Trigger:** HTTP errors, parsing errors, configuration errors
- **Labels / fields:** timestamp, error_type, message, http_status (if applicable)
- **Consumer:** Developer console during testing
- **Evidence:** Standard Python logging module

---

- **Signal:** Request/response logging (optional debug mode)
- **Type:** Debug logs
- **Trigger:** Each HTTP request/response if debug enabled
- **Labels / fields:** tool_name, endpoint_url, status_code, response_time_ms
- **Consumer:** Developer troubleshooting
- **Evidence:** Optional for MVP, useful for development

---

**Note:** Advanced metrics (request rates, latencies, error rates) and distributed tracing are explicitly out of scope for MVP. These can be added in future versions with observability frameworks like OpenTelemetry.

**Evidence:** Out-of-scope section lists advanced features; MVP focuses on functional correctness

## 10) Background Work & Shutdown

### No Background Work

The MCP server has no background workers, threads, or scheduled tasks:

- All work is synchronous request-response on the MCP protocol connection
- HTTP client does not use connection pooling that requires cleanup (or uses defaults that auto-cleanup)
- No async tasks or event loops beyond FastMCP framework's built-in handling

### Shutdown Handling

- **Worker / job:** FastMCP framework lifecycle
- **Trigger cadence:** Runs continuously until MCP client disconnects or process receives signal
- **Responsibilities:** FastMCP handles stdio transport and protocol message loop
- **Shutdown handling:** Framework handles graceful shutdown on stdin EOF or process signal (SIGTERM/SIGINT)
- **Evidence:** FastMCP framework manages MCP protocol lifecycle

**No custom shutdown hooks required for MVP.**

## 11) Security & Permissions

### Authentication Pass-Through

- **Concern:** Authentication for accessing Gitblit repositories
- **Touchpoints:** None in MCP server - Search API Plugin handles authentication
- **Mitigation:** MCP server passes through any authentication context from MCP client (if framework supports); Search API Plugin enforces access control
- **Residual risk:** MCP server has no visibility into auth - assumes plugin handles it correctly. Acceptable for MVP as authentication is explicitly out of scope.
- **Evidence:** docs/mvp_scope.md:43-45 "Authentication & Authorization" out of scope

---

### URL Injection Prevention

- **Concern:** GITBLIT_URL could be malicious if attacker controls environment
- **Touchpoints:** Configuration loading
- **Mitigation:** Validate URL format (http/https scheme only), document that environment must be trusted
- **Residual risk:** If attacker controls environment variables, they control server behavior (general threat model). Acceptable for MVP with proper deployment security.
- **Evidence:** Inferred from configuration design

---

### Query Injection

- **Concern:** Malicious Lucene query syntax
- **Touchpoints:** gb_file_search, gb_commit_search
- **Mitigation:** Pass queries directly to Search API Plugin which validates Lucene syntax and has its own security controls
- **Residual risk:** Depends on Search API Plugin's Lucene security. MCP server is thin adapter and doesn't parse queries. Acceptable per thin adapter design.
- **Evidence:** docs/search_plugin_api.md:244-263 shows plugin handles query validation

---

### No Rate Limiting

- **Concern:** MCP client could overwhelm server with requests
- **Touchpoints:** All tools
- **Mitigation:** None in MVP - relies on MCP client being well-behaved and Search API Plugin handling load
- **Residual risk:** No protection against abusive clients. Acceptable for MVP; add rate limiting in future versions.
- **Evidence:** Out of scope per MVP simplicity focus

## 12) UX / UI Impact

### No UI - CLI Only

The MCP server has no user interface. Interaction is through:

1. **Starting the server:** `poetry run python -m gitblit_mcp_server`
   - User sees startup log message confirming server is running
   - Error messages if configuration invalid

2. **MCP Client Integration:** AI assistant (Claude Desktop, etc.) calls tools
   - User interacts with AI assistant natural language interface
   - AI assistant calls MCP tools behind the scenes
   - Tool results presented by AI assistant in conversational format

3. **Testing:** `poetry run pytest`
   - Developer sees pytest output with pass/fail results
   - Test output shows HTTP requests/responses if verbose mode enabled

**Evidence:** docs/features/mcp_server_mvp/change_brief.md:42, CLAUDE.md describes CLI usage

## 13) Deterministic Test Plan

### gb_list_repos Tool Tests

- **Surface:** gb_list_repos MCP tool
- **Scenarios:**
  - Given live server with repositories, When call gb_list_repos(), Then return list of repositories with name/description/lastChange/hasCommits fields
  - Given query parameter "test", When call gb_list_repos(query="test"), Then return only repositories with "test" in name
  - Given limit parameter 5, When call gb_list_repos(limit=5), Then return at most 5 repositories
  - Given pagination cursor, When call gb_list_repos(after="cursor123"), Then return next page of results
  - Given no repositories match query, When call gb_list_repos(query="nonexistent"), Then return empty repositories array with totalCount=0
  - Given server error, When call gb_list_repos(), Then return error response with code and message
- **Fixtures / hooks:** pytest fixture to get GITBLIT_URL from test .env, fixture to import tool function, parametrized tests for different query values
- **Gaps:** No mock testing of HTTP layer (all tests against live server per requirements)
- **Evidence:** docs/mcp_api.md:7-103, docs/features/mcp_server_mvp/change_brief.md:27-30

---

### gb_list_files Tool Tests

- **Surface:** gb_list_files MCP tool
- **Scenarios:**
  - Given valid repo, When call gb_list_files(repo="test.git"), Then return files array with path and isDirectory fields
  - Given path parameter, When call gb_list_files(repo="test.git", path="src"), Then return contents of src directory
  - Given revision parameter, When call gb_list_files(repo="test.git", revision="develop"), Then return files from develop branch
  - Given directory path, Then directories in results have trailing slash and isDirectory=true
  - Given file path, Then files have isDirectory=false
  - Given nonexistent repo, When call gb_list_files(repo="fake.git"), Then return NOT_FOUND error
  - Given nonexistent path, When call gb_list_files(repo="test.git", path="nonexistent"), Then return error or empty list
- **Fixtures / hooks:** Test repo must exist on live server with known structure, fixture for common repo parameter
- **Gaps:** Depends on live server having test repositories with known structure (document required test data)
- **Evidence:** docs/mcp_api.md:106-178

---

### gb_read_file Tool Tests

- **Surface:** gb_read_file MCP tool
- **Scenarios:**
  - Given valid repo and path, When call gb_read_file(repo="test.git", path="README.md"), Then return content with line numbers
  - Given startLine parameter, When call gb_read_file(repo="test.git", path="file.txt", startLine=10), Then return content from line 10 onward
  - Given endLine parameter, When call gb_read_file(repo="test.git", path="file.txt", endLine=20), Then return content up to line 20
  - Given startLine and endLine, When call gb_read_file(repo="test.git", path="file.txt", startLine=10, endLine=20), Then return lines 10-20 inclusive
  - Given line numbers in format, Then each line starts with "{line_number}: "
  - Given revision parameter, When call gb_read_file(repo="test.git", path="file.txt", revision="v1.0"), Then return file from v1.0 tag
  - Given nonexistent file, When call gb_read_file(repo="test.git", path="fake.txt"), Then return NOT_FOUND error
  - Given file >128KB, When call gb_read_file(repo="test.git", path="large.bin"), Then return FILE_TOO_LARGE error
  - Given invalid line range (start > end), When call gb_read_file(..., startLine=20, endLine=10), Then return INVALID_REQUEST error
- **Fixtures / hooks:** Test files with known line counts, fixture to verify line number format
- **Gaps:** Large file testing requires test data >128KB on live server
- **Evidence:** docs/mcp_api.md:181-251

---

### gb_file_search Tool Tests

- **Surface:** gb_file_search MCP tool
- **Scenarios:**
  - Given query parameter, When call gb_file_search(query="TODO"), Then return results with matching files and chunks
  - Given repos filter, When call gb_file_search(query="error", repos=["test.git"]), Then return results only from test.git
  - Given pathPattern filter, When call gb_file_search(query="function", pathPattern="*.py"), Then return results only from Python files
  - Given branch filter, When call gb_file_search(query="test", branch="refs/heads/main"), Then return results from main branch only
  - Given count parameter, When call gb_file_search(query="TODO", count=5), Then return at most 5 results
  - Given contextLines parameter, When call gb_file_search(query="error", contextLines=20), Then chunks have ~20 lines of context
  - Given chunk content, Then each line has format "{line_number}: "
  - Given totalCount > count, Then limitHit=true
  - Given no matches, When call gb_file_search(query="nonexistent123xyz"), Then return empty results array with totalCount=0
  - Given Lucene syntax query, When call gb_file_search(query="error AND fatal"), Then return files matching boolean query
  - Given exact phrase query, When call gb_file_search(query='"null pointer"'), Then return files with exact phrase
- **Fixtures / hooks:** Test repositories with known searchable content, helper to validate chunk format
- **Gaps:** Limited Lucene syntax coverage (test basic cases only)
- **Evidence:** docs/mcp_api.md:254-372

---

### gb_commit_search Tool Tests

- **Surface:** gb_commit_search MCP tool
- **Scenarios:**
  - Given query and repos, When call gb_commit_search(query="fix", repos=["test.git"]), Then return commits with "fix" in message
  - Given authors filter, When call gb_commit_search(query="*", repos=["test.git"], authors=["john"]), Then return commits by john only
  - Given branch filter, When call gb_commit_search(query="*", repos=["test.git"], branch="refs/heads/main"), Then return commits from main branch
  - Given count parameter, When call gb_commit_search(query="*", repos=["test.git"], count=3), Then return at most 3 commits
  - Given commit results, Then each has repository, commit, author, date, title, message fields
  - Given date field, Then formatted as ISO 8601
  - Given no matching commits, When call gb_commit_search(query="nonexistent123", repos=["test.git"]), Then return empty commits array
  - Given missing repos parameter, When call gb_commit_search(query="test"), Then return error (repos required)
- **Fixtures / hooks:** Test repositories with known commit history, fixture for repos parameter
- **Gaps:** Limited commit history testing (depends on live server data)
- **Evidence:** docs/mcp_api.md:375-471

---

### HTTP Client Error Handling Tests

- **Surface:** HTTP client wrapper
- **Scenarios:**
  - Given 404 response, When client receives error, Then transform to {error: {code: "NOT_FOUND", message: ...}}
  - Given 400 response, When client receives error, Then transform to {error: {code: "INVALID_REQUEST", message: ...}}
  - Given 403 response, When client receives error, Then transform to {error: {code: "ACCESS_DENIED", message: ...}}
  - Given 500 response, When client receives error, Then transform to {error: {code: "INTERNAL_ERROR", message: ...}}
  - Given connection timeout, When client makes request, Then return INTERNAL_ERROR with connection message
  - Given malformed JSON response, When client parses response, Then return INTERNAL_ERROR with parsing message
- **Fixtures / hooks:** May need to temporarily point to invalid URL or use mock server for error scenarios
- **Gaps:** Connection error testing difficult against live server (may skip for MVP)
- **Evidence:** docs/mcp_api.md:490-505

---

### Configuration Tests

- **Surface:** Configuration loading
- **Scenarios:**
  - Given .env file with GITBLIT_URL, When load config, Then read URL from environment
  - Given missing GITBLIT_URL, When load config, Then raise exception
  - Given invalid URL format, When load config, Then raise exception
  - Given valid URL, When load config, Then store base URL without trailing slash
- **Fixtures / hooks:** Temporary .env file manipulation, monkeypatch environment variables
- **Gaps:** None
- **Evidence:** docs/features/mcp_server_mvp/change_brief.md:21-24

## 14) Implementation Slices

### Slice 1: Project Setup and Configuration

- **Goal:** Establish project structure with dependencies and configuration
- **Touches:** pyproject.toml, src/gitblit_mcp_server/__init__.py, src/gitblit_mcp_server/config.py, .env.example
- **Dependencies:** None - first slice
- **Deliverable:** Can run `poetry install` and import config module

---

### Slice 2: HTTP Client and Schema Definitions

- **Goal:** HTTP client for Search API Plugin with error handling and response schemas
- **Touches:** src/gitblit_mcp_server/client.py, src/gitblit_mcp_server/schemas.py
- **Dependencies:** Slice 1 complete (config available)
- **Deliverable:** Can make HTTP requests to Search API Plugin endpoints with error transformation

---

### Slice 3: MCP Tool Implementations (P0)

- **Goal:** Implement core P0 tools (list_repos, list_files, read_file, file_search)
- **Touches:** src/gitblit_mcp_server/tools/list_repos.py, list_files.py, read_file.py, file_search.py
- **Dependencies:** Slice 2 complete (client available)
- **Deliverable:** Four P0 tools implemented and callable

---

### Slice 4: Server Setup and Entry Point

- **Goal:** FastMCP server registration and module entry point
- **Touches:** src/gitblit_mcp_server/server.py, src/gitblit_mcp_server/__main__.py
- **Dependencies:** Slice 3 complete (tools available)
- **Deliverable:** Can run `poetry run python -m gitblit_mcp_server` and server starts

---

### Slice 5: P1 Tool and Test Infrastructure

- **Goal:** Implement commit_search tool and set up pytest framework
- **Touches:** src/gitblit_mcp_server/tools/commit_search.py, tests/conftest.py, tests/.env.test
- **Dependencies:** Slice 4 complete (server runnable)
- **Deliverable:** All 5 tools implemented, pytest configured

---

### Slice 6: Test Suite Implementation

- **Goal:** Complete test coverage for all tools
- **Touches:** tests/test_list_repos.py, test_list_files.py, test_read_file.py, test_file_search.py, test_commit_search.py
- **Dependencies:** Slice 5 complete (test infrastructure ready)
- **Deliverable:** Full test suite passes against live server

---

### Slice 7: Code Quality and Documentation

- **Goal:** Ensure code quality and complete documentation
- **Touches:** All source files (ruff/mypy fixes), README.md
- **Dependencies:** Slice 6 complete (all functionality implemented)
- **Deliverable:** `ruff check .` and `mypy .` pass, README documents usage

## 15) Risks & Open Questions

### Risks

- **Risk:** Live test server at http://10.1.2.3 not available or lacks test data
- **Impact:** Cannot run tests, blocks development verification
- **Mitigation:** Verify server access early, document required test repositories/files, consider fallback mock testing if server unavailable

---

- **Risk:** Search API Plugin response format doesn't match specification
- **Impact:** Response parsing errors, test failures
- **Mitigation:** Test against live server early in Slice 2, adjust schemas if needed, document any deviations

---

- **Risk:** FastMCP framework API differs from research/documentation
- **Impact:** Server setup and tool registration may need rework
- **Mitigation:** Review FastMCP examples and docs during Slice 4, adjust implementation to match actual API

---

- **Risk:** Line numbering format ambiguity between chunks and full file content
- **Impact:** Inconsistent formatting in test assertions
- **Mitigation:** Clarify format with early testing, ensure consistent formatting logic in client

---

- **Risk:** HTTP client timeout handling not robust enough
- **Impact:** Server hangs on slow Search API Plugin responses
- **Mitigation:** Set reasonable timeout (30s), document timeout behavior, consider user feedback in future versions

### Open Questions

- **Question:** Does .env file need to be in working directory or can it be elsewhere?
- **Why it matters:** Affects documentation and user experience for configuration
- **Owner / follow-up:** Test python-dotenv behavior, document in README

---

- **Question:** What test repositories and data must exist on http://10.1.2.3?
- **Why it matters:** Tests depend on specific repos/files existing with known content
- **Owner / follow-up:** Survey live server or create test data setup script, document in tests/README

---

- **Question:** Should HTTP client pool connections or create new connection per request?
- **Why it matters:** Performance and resource usage (marginal for MVP)
- **Owner / follow-up:** Use httpx defaults (has connection pooling), acceptable for MVP

---

- **Question:** How should server handle multiple concurrent MCP tool calls?
- **Why it matters:** Thread safety and resource contention
- **Owner / follow-up:** FastMCP framework likely handles this; verify framework behavior, assume safe for MVP

## 16) Confidence

Confidence: **High** — All MCP tools and Search API Plugin endpoints are well-specified with clear input/output schemas. The thin adapter pattern is straightforward with minimal business logic. FastMCP framework abstracts protocol complexity. Main dependencies are clear (FastMCP, httpx, pytest). Risks are manageable with early testing against live server. The greenfield nature avoids migration complexity.
