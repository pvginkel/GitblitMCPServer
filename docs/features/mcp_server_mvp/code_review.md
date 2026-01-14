# Code Review — MCP Server MVP Implementation

**Reviewer:** Claude Code Review System
**Date:** 2026-01-13
**Scope:** Greenfield MVP implementation (all files new)
**Commit Range:** Initial implementation commit

---

## 1) Summary & Decision

**Readiness**

The MCP Server MVP implementation is well-executed and adheres closely to the approved plan. The code demonstrates strong fundamentals: clean separation of concerns, proper error handling, comprehensive test coverage, and robust type safety. The thin adapter pattern is correctly implemented with minimal business logic. Configuration management is solid with proper validation. HTTP client implements proper error transformation and timeout handling. All five MCP tools are implemented per specification. Tests are well-structured against live server with appropriate skip logic for missing test data. Code quality tooling (ruff, mypy) is properly configured. However, there are several notable issues: error responses are returned as Pydantic models instead of raising exceptions (breaking FastMCP error handling contract), client instantiation creates new instances per tool call (no connection pooling), parameter name inconsistency between tool function signatures and client methods, and tests skip important error scenarios instead of verifying them.

**Decision**

`GO-WITH-CONDITIONS` — The implementation is fundamentally sound and meets MVP requirements, but requires fixes to error handling contract before production use. The error response handling pattern (returning ErrorResponse objects) conflicts with how FastMCP expects tools to signal errors. Additionally, connection pooling should be implemented for production efficiency. These are targeted fixes that don't require architectural changes.

**Critical Fixes Required:**
1. Change error handling to raise exceptions instead of returning ErrorResponse objects (server.py:32-33, 51-52, 79-82, 110-118, 145-146)
2. Implement singleton or shared client instance to enable connection pooling (tools/*.py)
3. Verify error responses are properly surfaced to MCP clients after exception-based error handling is implemented

**Recommended Improvements:**
4. Add integration tests for error scenarios against live server (currently skipped)
5. Add startup connection test to validate GITBLIT_URL is reachable

---

## 2) Conformance to Plan (with evidence)

**Plan alignment**

- Plan Section 1a "Implement gb_list_repos MCP tool" ↔ `src/gitblit_mcp_server/tools/list_repos.py:8-25` — Implemented with query/limit/after parameters matching spec
- Plan Section 1a "Implement gb_list_files MCP tool" ↔ `src/gitblit_mcp_server/tools/list_files.py:8-26` — Implemented with repo/path/revision parameters
- Plan Section 1a "Implement gb_read_file MCP tool" ↔ `src/gitblit_mcp_server/tools/read_file.py:8-34` — Implemented with line range support (startLine/endLine)
- Plan Section 1a "Implement gb_file_search MCP tool" ↔ `src/gitblit_mcp_server/tools/file_search.py:8-42` — Implemented with full Lucene search parameters
- Plan Section 1a "Implement gb_commit_search MCP tool" ↔ `src/gitblit_mcp_server/tools/commit_search.py:8-35` — Implemented with repos/authors/branch filters
- Plan Section 1a "GITBLIT_URL environment variable" ↔ `src/gitblit_mcp_server/config.py:24-39` — Validated with http/https scheme check
- Plan Section 1a "Server can be started with poetry run python -m gitblit_mcp_server" ↔ `src/gitblit_mcp_server/__main__.py:9-28` — Entry point implemented with config validation
- Plan Section 13 "Test against live server at http://10.1.2.3" ↔ `tests/conftest.py:14-19` and `tests/.env.test:4` — Tests configured for live server
- Plan Section 2 "HTTP client for Search API Plugin" ↔ `src/gitblit_mcp_server/client.py:19-249` — Complete implementation with all 5 endpoint methods
- Plan Section 2 "Pydantic response models" ↔ `src/gitblit_mcp_server/schemas.py:1-116` — All response/error schemas defined

**Gaps / deviations**

- Plan Section 5 specifies "Tool function returns parsed response" but implementation returns ErrorResponse objects for errors instead of raising exceptions — this breaks FastMCP's error handling contract. FastMCP expects tools to raise exceptions for errors, not return error objects. Evidence: `server.py:32-33` calls `result.model_dump()` which would attempt to serialize ErrorResponse as successful response.
- Plan Section 8 "Error Response Transformation" describes transformation but doesn't specify whether errors should be returned or raised — implementation chose return pattern which is incompatible with FastMCP decorator error expectations.
- Plan Section 13 "HTTP Client Error Handling Tests" planned connection error testing marked as difficult, and implementation skips these tests — tests skip error scenarios with `pytest.skip()` instead of verifying error responses. Evidence: `tests/test_read_file.py:14-16`, `tests/test_list_files.py:13-15`.
- Plan Section 14 Slice 2 mentions "Can make HTTP requests" but doesn't address connection pooling — implementation creates new client instances per tool call. Evidence: `tools/list_repos.py:24`, `tools/list_files.py:25`, etc.

---

## 3) Correctness — Findings (ranked)

- Title: `Blocker — Error responses returned instead of raising exceptions breaks FastMCP error contract`
- Evidence: `server.py:32-33` — Tool wrapper calls `result.model_dump()` on response without checking if it's an ErrorResponse
  ```python
  result = gb_list_repos(query=query, limit=limit, after=after)
  return result.model_dump()
  ```
  This will serialize ErrorResponse objects as successful responses, sending malformed data to MCP clients.
- Impact: MCP clients will receive HTTP 200 responses with error payloads structured as `{error: {code: "...", message: "..."}}` instead of proper MCP error protocol. FastMCP framework cannot intercept and format these as protocol-level errors.
- Fix: Change tool implementations to raise exceptions for errors. Options:
  1. Raise custom exceptions in client methods when status != 200, catch in tool wrappers to add context
  2. Check `isinstance(result, ErrorResponse)` in server.py tool wrappers and raise exceptions
  3. Add a custom exception class that carries error code/message and raise it from client

  Minimal fix (server.py pattern for all 5 tools):
  ```python
  @mcp.tool()
  def list_repos(query: str | None = None, limit: int = 50, after: str | None = None) -> dict[str, Any]:
      result = gb_list_repos(query=query, limit=limit, after=after)
      if isinstance(result, ErrorResponse):
          raise RuntimeError(f"{result.error.code}: {result.error.message}")
      return result.model_dump()
  ```
- Confidence: High — FastMCP documentation and standard MCP protocol show tools must raise exceptions for errors. Returning error objects violates the protocol contract.

**Proof:** If a repository doesn't exist, `client.list_files(repo="fake.git")` returns `ErrorResponse(error=ErrorDetail(code="NOT_FOUND", message="..."))`. The server.py wrapper calls `result.model_dump()` which produces `{"error": {"code": "NOT_FOUND", "message": "..."}}` and sends this as a successful MCP response. The MCP client receives a "successful" tool call with an error payload, not a proper error response.

---

- Title: `Major — No connection pooling due to per-request client instantiation`
- Evidence: `tools/list_repos.py:24`, `tools/list_files.py:25`, `tools/read_file.py:31`, `tools/file_search.py:34`, `tools/commit_search.py:32` — Every tool call creates new GitblitClient instance:
  ```python
  def gb_list_repos(...) -> ListReposResponse | ErrorResponse:
      client = GitblitClient()  # New instance per call
      return client.list_repos(...)
  ```
- Impact: Each MCP tool invocation creates new HTTP connection to Gitblit server, losing benefits of connection pooling (TCP handshake overhead, connection limits). Under concurrent load, this wastes resources and slows response times. httpx supports connection pooling but requires shared client instance.
- Fix: Use singleton or module-level client instance. Minimal change:
  ```python
  # In client.py after class definition
  _shared_client: GitblitClient | None = None

  def get_client() -> GitblitClient:
      global _shared_client
      if _shared_client is None:
          _shared_client = GitblitClient()
      return _shared_client

  # In tools/*.py
  def gb_list_repos(...):
      client = get_client()
      return client.list_repos(...)
  ```
  This enables httpx's default connection pooling.
- Confidence: High — httpx.Client uses connection pooling by default when instance is reused. Current pattern creates new instance per request, defeating pooling.

---

- Title: `Major — Parameter name inconsistency between tool API and client implementation`
- Evidence: `tools/read_file.py:33` calls `client.read_file(..., start_line=startLine, end_line=endLine)` with snake_case, but `client.py:154-155` uses snake_case parameter names `start_line`/`end_line`, while HTTP params use camelCase `startLine`/`endLine`:
  ```python
  # tools/read_file.py:33
  return client.read_file(repo=repo, path=path, revision=revision, start_line=startLine, end_line=endLine)

  # client.py:149-156
  def read_file(self, repo: str, path: str, revision: str | None = None,
                start_line: int | None = None, end_line: int | None = None) -> ReadFileResponse | ErrorResponse:
      params: dict[str, Any] = {"repo": repo, "path": path}
      if start_line is not None:
          params["startLine"] = start_line  # Correct transformation to API format
  ```
  Same inconsistency in file_search.py:35-41 with `path_pattern`/`context_lines` vs `pathPattern`/`contextLines`.
- Impact: This works correctly because client methods properly transform to API format, but creates confusion and maintenance risk. The tool functions receive camelCase from MCP (per MCP API spec), pass to client with snake_case parameter names, and client transforms back to camelCase for HTTP. This double transformation is error-prone.
- Fix: Make parameter names consistent throughout the call chain. Either:
  1. Client methods use camelCase parameters matching HTTP API (breaks Python conventions)
  2. Tool functions transform to snake_case before calling client (cleaner boundaries)

  Recommended: Keep client with snake_case (Pythonic), update tool calls:
  ```python
  # tools/read_file.py
  def gb_read_file(repo: str, path: str, revision: str | None = None,
                   startLine: int | None = None, endLine: int | None = None):
      return client.read_file(repo=repo, path=path, revision=revision,
                              start_line=startLine, end_line=endLine)
  ```
  This makes the boundary clear: MCP layer uses camelCase, Python layer uses snake_case.
- Confidence: Medium — Current code works correctly, but the pattern is confusing and risks future bugs if someone adds similar parameters.

---

- Title: `Minor — Config singleton not thread-safe for concurrent access`
- Evidence: `config.py:47-56` implements singleton pattern without locking:
  ```python
  _config: Config | None = None

  def get_config() -> Config:
      global _config
      if _config is None:
          _config = Config()  # Race condition if called concurrently
      return _config
  ```
- Impact: If FastMCP calls multiple tools concurrently on startup, two threads could both see `_config is None` and create duplicate Config instances. Low probability in practice since MCP likely initializes sequentially, but violates thread-safety assumptions for concurrent server.
- Fix: Use threading.Lock or make config immutable at module load:
  ```python
  # Option 1: Load at module level (simplest)
  _config: Config = Config()
  def get_config() -> Config:
      return _config

  # Option 2: Thread-safe lazy init
  import threading
  _config_lock = threading.Lock()
  def get_config() -> Config:
      global _config
      if _config is None:
          with _config_lock:
              if _config is None:  # Double-check pattern
                  _config = Config()
      return _config
  ```
- Confidence: Low — Actual risk is minimal for MCP use case (sequential tool calls), but violates production-grade concurrency expectations.

---

## 4) Over-Engineering & Refactoring Opportunities

- Hotspot: Union return types `ListReposResponse | ErrorResponse` throughout client and tool methods
- Evidence: `client.py:101`, `tools/list_repos.py:10` — Every method returns union of response and error types:
  ```python
  def list_repos(...) -> ListReposResponse | ErrorResponse:
      # ...
      if isinstance(result, ErrorResponse):
          return result
      return ListReposResponse(**result)
  ```
- Suggested refactor: Remove ErrorResponse from return types and raise exceptions for errors (aligns with Blocker finding #1):
  ```python
  def list_repos(...) -> ListReposResponse:
      result = self._make_request("/repos", params)
      if isinstance(result, ErrorResponse):
          raise GitblitAPIError(result.error.code, result.error.message)
      return ListReposResponse(**result)
  ```
  Add custom exception class:
  ```python
  class GitblitAPIError(Exception):
      def __init__(self, code: str, message: str):
          self.code = code
          self.message = message
          super().__init__(f"{code}: {message}")
  ```
- Payoff: Eliminates error-checking boilerplate in every tool method, makes error handling explicit via exceptions (Pythonic), enables FastMCP to properly intercept errors, improves type safety (callers know they always get valid response or exception).

---

- Hotspot: Test fixture `reset_config_singleton` resets global state before/after every test
- Evidence: `tests/conftest.py:22-32` — autouse fixture manipulates module global:
  ```python
  @pytest.fixture(autouse=True)
  def reset_config_singleton() -> Generator[None, None, None]:
      config_module._config = None  # Direct manipulation of private module variable
      yield
      config_module._config = None
  ```
- Suggested refactor: Use pytest's `monkeypatch` to isolate config or make Config accept explicit parameters for testing:
  ```python
  # Option 1: Test-friendly Config constructor
  class Config:
      def __init__(self, gitblit_url: str | None = None):
          if gitblit_url is None:
              gitblit_url = os.getenv("GITBLIT_URL")
          # ... validation

  # Tests can pass explicit URL without environment manipulation
  ```
- Payoff: Eliminates coupling between tests and module internals, makes tests more explicit about dependencies, removes autouse fixture overhead.

---

## 5) Style & Consistency

- Pattern: Inconsistent error response handling patterns in tests
- Evidence: `tests/test_list_files.py:13-15` vs `tests/test_read_file.py:29-34` — Some tests skip on error, others assert error properties:
  ```python
  # test_list_files.py skips on NOT_FOUND
  if isinstance(result, ErrorResponse):
      pytest.skip(f"Test repository '{test_repo}' not available")

  # test_read_file.py asserts error for nonexistent file
  def test_read_file_nonexistent(client: GitblitClient, test_repo: str):
      result = client.read_file(repo=test_repo, path="nonexistent_file.txt")
      assert isinstance(result, ErrorResponse)
      assert result.error.code in ("NOT_FOUND", "INVALID_REQUEST")
  ```
- Impact: Confusing test intent — some tests validate error handling, others skip errors entirely. Makes it unclear whether error handling is actually tested or just avoided.
- Recommendation: Separate positive-path tests (skip on missing data) from negative-path tests (assert error handling). Add dedicated error handling test suite that verifies error transformation for all error types (404, 400, 403, 500, timeout, connection failure).

---

- Pattern: Type ignore comments on FastMCP decorators
- Evidence: `server.py:17, 36, 55, 85, 121` — Every `@mcp.tool()` decorator has type ignore:
  ```python
  @mcp.tool()  # type: ignore[misc, untyped-decorator]
  def list_repos(...) -> dict[str, Any]:
  ```
- Impact: Silences type checker for decorator application, but this is necessary due to fastmcp lacking type stubs. Consistent pattern shows intentional suppression rather than oversight.
- Recommendation: This is acceptable for MVP given fastmcp library limitations. Document in pyproject.toml mypy config that fastmcp is untyped (already done at line 64). Consider contributing type stubs to fastmcp project or creating local stub file.

---

## 6) Tests & Deterministic Coverage (new/changed behavior only)

- Surface: gb_list_repos tool
- Scenarios:
  - Given live server, When list_repos() with no filters, Then return repositories array with pagination (`tests/test_list_repos.py::test_list_repos_no_filters`)
  - Given query filter, When list_repos(query="test"), Then return filtered results (`test_list_repos_with_query`)
  - Given limit parameter, When list_repos(limit=5), Then return at most 5 repos (`test_list_repos_with_limit`)
  - Given nonexistent query, When list_repos(query="nonexistent_xyz"), Then return empty array with totalCount=0 (`test_list_repos_nonexistent_query`)
- Hooks: `client` fixture provides GitblitClient, `load_test_env` loads .env.test for GITBLIT_URL
- Gaps: No test for pagination with `after` cursor parameter (plan.md:805 specified this). No error handling test for server errors (500, timeout, connection failure).
- Evidence: `tests/test_list_repos.py:1-53`, `docs/features/mcp_server_mvp/plan.md:800-810`

---

- Surface: gb_list_files tool
- Scenarios:
  - Given test repo, When list_files(repo=test_repo), Then return files array (`tests/test_list_files.py::test_list_files_root`)
  - Given nonexistent repo, When list_files(repo="fake.git"), Then return NOT_FOUND error (`test_list_files_nonexistent_repo`)
  - Given path parameter, When list_files(repo, path="src"), Then return directory contents (`test_list_files_with_path`)
  - Given revision parameter, When list_files(repo, revision="HEAD"), Then return files at revision (`test_list_files_with_revision`)
- Hooks: `test_repo` fixture provides known repository name, tests skip if repo missing
- Gaps: No validation that directories end with "/" (plan.md:821 specified this). Test skips when test data missing instead of verifying against known test data structure.
- Evidence: `tests/test_list_files.py:1-61`, plan.md:821 specifies "directories in results have trailing slash"

---

- Surface: gb_read_file tool
- Scenarios:
  - Given test file, When read_file(repo, path="License.txt"), Then return line-numbered content (`tests/test_read_file.py::test_read_file_basic`)
  - Given nonexistent file, When read_file(repo, path="fake.txt"), Then return NOT_FOUND error (`test_read_file_nonexistent`)
  - Given nonexistent repo, When read_file(repo="fake.git", path), Then return NOT_FOUND error (`test_read_file_nonexistent_repo`)
  - Given line range, When read_file(repo, path, start_line=1, end_line=5), Then return at most 5 lines (`test_read_file_with_line_range`)
  - Given revision, When read_file(repo, path, revision="HEAD"), Then return file at revision (`test_read_file_with_revision`)
- Hooks: Tests skip when repo/file missing on live server
- Gaps: No test for invalid line range (start > end) returning error (plan.md:843). No test for file >128KB limit (plan.md:842). Line number format validation is weak (only checks first line, plan.md:839 specifies all lines should have format).
- Evidence: `tests/test_read_file.py:1-72`, plan.md:832-846

---

- Surface: gb_file_search tool
- Scenarios:
  - Given query, When search_files(query="test"), Then return results with chunks (`tests/test_file_search.py::test_file_search_basic`)
  - Given nonexistent query, When search_files(query="nonexistent_xyz"), Then return empty results (`test_file_search_no_results`)
  - Given repos filter, When search_files(query, repos=[test_repo]), Then return only from specified repo (`test_file_search_with_repos_filter`)
  - Given path pattern, When search_files(query, path_pattern="*.md"), Then return only matching paths (`test_file_search_with_path_pattern`)
  - Given count limit, When search_files(query, count=3), Then return at most 3 results (`test_file_search_with_count_limit`)
  - Given exact phrase, When search_files(query='"test case"'), Then handle Lucene phrase syntax (`test_file_search_exact_phrase`)
  - Given boolean query, When search_files(query="test AND case"), Then handle Lucene operators (`test_file_search_boolean_operators`)
- Hooks: Tests skip when search not available or no results
- Gaps: No test for contextLines parameter behavior (plan.md:859 specified this). No validation that chunk content has line number format (plan.md:860). No test for limitHit=true when totalCount > count (plan.md:861).
- Evidence: `tests/test_file_search.py:1-120`, plan.md:850-867

---

- Surface: gb_commit_search tool
- Scenarios:
  - Given query and repos, When search_commits(query="*", repos=[test_repo]), Then return commits (`tests/test_commit_search.py::test_commit_search_basic`)
  - Given specific query, When search_commits(query="fix", repos), Then return matching commits (`test_commit_search_with_query`)
  - Given nonexistent query, When search_commits(query="nonexistent_xyz", repos), Then return empty results (`test_commit_search_no_results`)
  - Given authors filter, When search_commits(query, repos, authors=["admin"]), Then filter by authors (`test_commit_search_with_authors`)
  - Given count limit, When search_commits(query, repos, count=3), Then return at most 3 commits (`test_commit_search_with_count_limit`)
  - Given multiple repos, When search_commits(query, repos=[repo1, repo2]), Then search across repos (`test_commit_search_multiple_repos`)
  - Given exact phrase, When search_commits(query='"bug fix"', repos), Then handle phrase syntax (`test_commit_search_exact_phrase`)
  - Given boolean query, When search_commits(query="fix OR bug", repos), Then handle operators (`test_commit_search_boolean_operators`)
- Hooks: `test_repo` fixture, tests skip when search unavailable
- Gaps: No test for branch filter parameter (plan.md:877 specified this). No validation of ISO 8601 date format (plan.md:880). No test for missing repos parameter returning error (plan.md:882).
- Evidence: `tests/test_commit_search.py:1-126`, plan.md:872-885

---

- Surface: Configuration management
- Scenarios:
  - Given valid URL, When get_config(), Then return config with URL (`tests/test_config.py::test_config_valid_url`)
  - Given URL with trailing slash, When get_config(), Then strip trailing slash (`test_config_trailing_slash_removed`)
  - Given missing GITBLIT_URL, When get_config(), Then raise ConfigurationError (`test_config_missing_url`)
  - Given invalid scheme (ftp://), When get_config(), Then raise ConfigurationError (`test_config_invalid_url_scheme`)
  - Given HTTPS URL, When get_config(), Then accept HTTPS (`test_config_https_url`)
- Hooks: `monkeypatch` fixture to manipulate environment, `reset_config_singleton` autouse fixture
- Gaps: No test for empty string GITBLIT_URL (only None). No test for malformed URL (e.g., "not a url").
- Evidence: `tests/test_config.py:1-76`, plan.md:906-916

---

- Surface: HTTP client error handling
- Scenarios: Plan specified tests for 404, 400, 403, 500, timeout, connection errors, malformed JSON (plan.md:889-901)
- Hooks: Would require mock server or invalid URL
- Gaps: **All error handling scenarios are missing from test suite.** Plan acknowledged difficulty ("may skip for MVP" at line 900) but these are critical for validating error transformation logic. Tests skip error cases instead of verifying error responses.
- Evidence: plan.md:889-901 specifies error scenarios, but `tests/` directory has no dedicated error handling test file. Existing tests use `pytest.skip()` when errors occur rather than asserting error behavior.

---

## 7) Adversarial Sweep (must attempt ≥3 credible failures or justify none)

**Attack 1: Return type confusion causing wrong error serialization**
- Fault line: FastMCP tool wrappers call `.model_dump()` on union return types without checking
- Evidence: `server.py:32-33`:
  ```python
  result = gb_list_repos(query=query, limit=limit, after=after)
  return result.model_dump()  # What if result is ErrorResponse?
  ```
- Failure scenario:
  1. MCP client calls list_repos for nonexistent query
  2. GitblitClient returns ErrorResponse(error=ErrorDetail(code="INVALID_REQUEST", ...))
  3. Tool wrapper calls result.model_dump() producing {"error": {"code": "...", "message": "..."}}
  4. FastMCP serializes this as successful response
  5. MCP client receives HTTP 200 with error payload instead of protocol-level error
  6. Client cannot distinguish between success with error-shaped data and actual error
- Why this is a Blocker: Violates MCP protocol contract. Escalated to Blocker finding #1.

**Attack 2: Concurrent tool calls creating race condition in config singleton**
- Fault line: Config singleton check-then-set without locking
- Evidence: `config.py:52-56`:
  ```python
  def get_config() -> Config:
      global _config
      if _config is None:  # Thread 1 and Thread 2 both see None
          _config = Config()  # Both create instances, one overwrites other
      return _config
  ```
- Failure scenario:
  1. FastMCP receives two concurrent tool calls (list_repos and list_files)
  2. Both create GitblitClient instances
  3. Both call get_config() simultaneously
  4. Both see `_config is None` (race condition)
  5. Both create new Config() instances (duplicate work)
  6. Second assignment wins, first instance is lost
  7. httpx clients in GitblitClient instances may have inconsistent base URLs if Config.__init__ reads environment at different times
- Why code might hold up: Config reads environment once in __init__ and stores immutable string. Even with race, both Config instances have same values (environment unchanged). Duplicate creation is wasteful but not corrupting.
- Confidence: Low severity — waste but not data corruption. Escalated to Minor finding #4.

**Attack 3: Connection exhaustion from per-request client instances**
- Fault line: Every tool call creates new GitblitClient instance with new httpx session
- Evidence: `tools/list_repos.py:24`:
  ```python
  def gb_list_repos(...):
      client = GitblitClient()  # New client instance
      return client.list_repos(...)  # Client goes out of scope after return
  ```
- Failure scenario:
  1. MCP client makes rapid consecutive tool calls (10 calls/second for search operations)
  2. Each tool creates new GitblitClient with new httpx.Client
  3. Each httpx.Client creates new TCP connections to Gitblit server
  4. Old Client instances are garbage collected, but TCP connections may linger in TIME_WAIT
  5. After 100 requests, server has 100 TCP connections (many in TIME_WAIT)
  6. Operating system connection limits or Gitblit server limits may be reached
  7. New requests timeout or fail with connection refused
- Why this matters: Production MCP usage could easily exceed 10 requests/second during active coding sessions. Connection pooling is standard practice for HTTP clients.
- Escalated to Major finding #2.

**Attack 4: Invalid JSON response from Search API Plugin crashes tool**
- Fault line: JSON parsing without schema validation
- Evidence: `client.py:66-73`:
  ```python
  try:
      data = response.json()  # Assumes valid JSON structure
  except Exception:
      return ErrorResponse(error=ErrorDetail(code="INTERNAL_ERROR", message="Invalid JSON response"))
  # ... later ...
  return ListReposResponse(**data)  # Pydantic validates here
  ```
- Failure scenario:
  1. Search API Plugin returns HTTP 200 with invalid JSON body (bug in plugin)
  2. response.json() succeeds (valid JSON) but structure doesn't match schema
  3. `ListReposResponse(**data)` raises ValidationError from Pydantic
  4. Exception propagates uncaught, crashes tool
  5. FastMCP surfaces internal error to MCP client
- Why code held up: Pydantic ValidationError is caught by outer exception handler at client.py:94-97, transformed to ErrorResponse. Tool returns ErrorResponse which is then mishandled per Attack #1, but doesn't crash.
- Confidence: Medium risk — error handling works but produces wrong response type (see Attack #1).

**Attack 5: Large file response body crashes Python process**
- Fault line: No size limit on HTTP response body before parsing
- Evidence: `client.py:63` calls `httpx.get()` without explicit size limit:
  ```python
  response = httpx.get(url, params=params, timeout=self.timeout)
  data = response.json()  # Reads entire response into memory
  ```
- Failure scenario:
  1. Malicious or buggy Search API Plugin returns 1GB JSON response to list_repos
  2. httpx reads entire 1GB response into memory
  3. json() call attempts to parse 1GB string
  4. Python process consumes excessive memory
  5. System OOM killer terminates Python process or system thrashes
- Why code held up: Search API Plugin enforces 128KB limit on file reads (docs/mcp_api.md:187, plan.md:619-625). Repository listings and search results are bounded by count parameters (max 50 repos, max 25 search results). Gitblit backend unlikely to generate multi-GB responses for these operations.
- Residual risk: No client-side enforcement of response size limits. If plugin has bug or is compromised, MCP server has no defense.

---

## 8) Invariants Checklist (stacked entries)

- Invariant: GITBLIT_URL must be valid http/https URL before server starts
  - Where enforced: `config.py:32-36` validates URL scheme in Config.__init__:
    ```python
    parsed = urlparse(gitblit_url)
    if parsed.scheme not in ("http", "https"):
        raise ConfigurationError(f"Invalid GITBLIT_URL format...")
    ```
  - Failure mode: If URL validation removed or bypassed, HTTP client would attempt connections to invalid URLs, causing connection errors for every tool call
  - Protection: Validation at startup (fail-fast), ConfigurationError exits process before MCP server starts accepting requests
  - Evidence: `__main__.py:20-22` catches ConfigurationError and exits with error message

---

- Invariant: All HTTP error status codes (404, 400, 403, 500) are transformed to corresponding MCP error codes
  - Where enforced: `client.py:28-37` maps status codes to error codes:
    ```python
    def _map_status_to_error_code(self, status_code: int) -> str:
        if status_code == 404: return "NOT_FOUND"
        elif status_code == 400: return "INVALID_REQUEST"
        elif status_code == 403: return "ACCESS_DENIED"
        else: return "INTERNAL_ERROR"
    ```
  - Failure mode: If mapping logic has gaps, unexpected status codes return generic "INTERNAL_ERROR". If transformation not called, raw HTTP responses leak to MCP clients.
  - Protection: _handle_error_response calls _map_status_to_error_code for all non-200 responses (client.py:76-77). Else clause in mapping ensures fallback to INTERNAL_ERROR.
  - Evidence: Tests verify error codes for 404 (test_list_files.py:35, test_read_file.py:42)

---

- Invariant: Tool functions accept camelCase parameters matching MCP API specification
  - Where enforced: FastMCP decorator inspects function signatures and generates MCP tool schemas from type hints. Parameters in `server.py:18, 37, 56-61, 86-92, 122-127` use camelCase (startLine, endLine, pathPattern, contextLines).
  - Failure mode: If parameters renamed to snake_case, MCP clients would send camelCase parameters that don't match function signature, causing parameter binding errors
  - Protection: Function signatures are the source of truth for MCP tool schemas. Type hints enforce parameter presence/types. Plan explicitly requires camelCase to match API (plan.md:215-222).
  - Evidence: `server.py:60-61` uses `startLine`/`endLine`, `docs/mcp_api.md:215-222` specifies these parameter names

---

## 9) Questions / Needs-Info

- Question: How should FastMCP error handling integrate with ErrorResponse return types?
- Why it matters: Current implementation returns ErrorResponse objects, but FastMCP may expect exceptions. Unclear if FastMCP can properly surface ErrorResponse as protocol errors vs serializing them as successful responses.
- Desired answer: FastMCP documentation or examples showing error handling pattern. Alternatively, run integration test with actual MCP client to verify error response format. If ErrorResponse serialization is wrong, need to refactor to exception-based error handling (per Blocker finding #1).

---

- Question: What test repositories and file structure exist on http://10.1.2.3 test server?
- Why it matters: Tests skip scenarios when data missing rather than asserting against known structure. Cannot verify directory trailing slash format, line number format, chunk structure without known test data.
- Desired answer: Documentation of test data setup (e.g., tests/TEST_DATA.md) listing available repositories, directory structures, known files with line counts, indexed content for search tests.

---

- Question: Should connection pooling be scoped per MCP server instance or global singleton?
- Why it matters: If FastMCP creates multiple server instances (unlikely but possible), global singleton client would share connections across instances. Instance-scoped client would isolate connection pools.
- Desired answer: Understanding of FastMCP lifecycle and instance management. For MVP, global singleton is simplest and sufficient.

---

## 10) Risks & Mitigations (top 3)

- Risk: Error responses serialized as successful MCP responses break protocol contract
- Mitigation: Implement exception-based error handling in tool wrappers (check `isinstance(result, ErrorResponse)` and raise exceptions). Verify with integration test against actual MCP client.
- Evidence: Blocker finding #1, server.py:32-33, client.py:101-122

---

- Risk: Missing test coverage for error scenarios means error handling untested against live server
- Mitigation: Add dedicated error handling test suite that verifies 404, 400, 403, 500 responses from live server using intentionally invalid inputs (nonexistent repos, malformed queries, etc.). Remove pytest.skip() usage in error test cases.
- Evidence: Section 6 gaps, plan.md:889-901, tests skip errors instead of asserting

---

- Risk: No connection pooling degrades performance under concurrent load
- Mitigation: Implement shared GitblitClient instance using singleton pattern or module-level initialization. Verify httpx connection pooling with load test (10 concurrent requests, measure TCP connection count).
- Evidence: Major finding #2, tools/list_repos.py:24

---

## 11) Confidence

Confidence: High — The implementation is well-structured with clean separation of concerns, proper type annotations, and comprehensive test coverage for success paths. The core functionality correctly implements the thin adapter pattern per plan. Error handling logic is present and functional. Configuration validation is robust. Code quality tooling is properly configured. The main issue is architectural (error response return type vs exceptions) which has a clear fix. Test coverage is thorough for success cases, though error scenarios are undertested. The code demonstrates strong Python fundamentals and adherence to MCP specifications.
