# Gitblit MCP Server - Agreed Changes

## 1. Lower Default Context Lines

**Current:** `contextLines` defaults to 100

**Change:** Reduce default to 10 lines

**Rationale:** Large context inflates response sizes unnecessarily, contributing to token limit issues.

---

## 2. Default Branch Only When Branch Filter Omitted

**Current:** Searches return results from all branches, causing duplicates when the same file exists in multiple branches.

**Change:** When `branch` parameter is omitted or empty, only search the default branch.

**Rationale:** Eliminates duplicate results and reduces response sizes. Users can still search specific branches by providing the `branch` parameter explicitly.

---

## 3. New `gb_find_files` Operation

**Purpose:** Find repositories that contain files matching a glob pattern (search by file existence, not contents).

**Example use cases:**
- Find all repos containing `sdkconfig` (ESP-IDF projects)
- Find all repos containing `platformio.ini` (PlatformIO projects)
- Find all repos containing `package.json` (Node.js projects)

**Suggested parameters:**
- `pattern` - Glob pattern to match (e.g., `**/sdkconfig`, `CMakeLists.txt`)
- `repos` - Optional list of repos to search (null = all repos)

**Returns:** List of repositories (and optionally matched file paths) where the pattern exists.
