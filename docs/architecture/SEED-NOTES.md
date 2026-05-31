# SEED-NOTES — gitblit-mcp-server

Seed of the first architecture artifact for this repo as a federated producer.
Authored **headless** — interactive triage was skipped; modeling decisions were
made best-effort against the producer manual's inclusion rule and the locked
conventions in the seeding task. Mode: **hand-authored** (no generator; the YAML
is the source of truth, uuid4 mint-once ids).

## Identity (fixed, not re-derived)

- Producer id (envelope key): `gitblit-mcp-server`
- `introduced` = repo's first commit date `2026-01-12`, identical on every element.

## Element inventory

| id | kind | label | notes |
|---|---|---|---|
| `app:gitblit-mcp-server,34404f56-6f1e-4579-b515-728a59747bcc` | ApplicationComponent «SoftwareProduct» | Gitblit MCP Server | The product this repo owns. `sourceRepository: git:pvginkel/GitblitMCPServer`; `stats.image: registry:5000/gitblit-mcp-server`. |
| `svc:gitblit-mcp,bb4a54e8-2b13-4bcb-842e-99f111108ecc` | ApplicationService | Gitblit MCP API | The one exposed network surface — the MCP protocol API (six gb_* tools). |
| `if:gitblit-mcp-sse,33622998-9147-4759-817b-d85b9c23cfce` | ApplicationInterface | MCP SSE endpoint | Single consumer class: MCP clients (AI assistants). SSE transport at `/sse` + `/messages/`. |

All three UUIDs freshly minted with uuid4 during this seed (never re-mint).

## Relations

- `app —Realization→ svc:gitblit-mcp` — product realizes its MCP API.
- `if:gitblit-mcp-sse —Assignment→ svc:gitblit-mcp` — the SSE interface is the
  addressable point on the service. One interface only: every consumer is an MCP
  client; no distinct admin/IaC consumer class exists.
- `app —Association→ cap:source-control` **boundBy `env:GITBLIT_URL`** — the one
  outbound runtime dependency.

## Outbound dependency decision

The MCP server's only outbound call is to its Gitblit instance, reached via the
`GITBLIT_URL` env var (`src/gitblit_mcp_server/config.py:24`,
`api_base_url` → `<GITBLIT_URL>/api/.mcp-internal`). Gitblit is the in-house Git
host = substitutable in-house infra realizing **`cap:source-control`** ("Git
repository hosting and access control"). Per the locked conventions, a
substitutable in-house dependency targets a curated capability with a **required
`boundBy: env:<VAR>`** — here `env:GITBLIT_URL`. Modeled as the consumer
(`app`) → `cap:source-control`, `type: Association`.

- The concrete wire is the **Gitblit Search API Plugin** REST API
  (`/api/.mcp-internal/*`) hosted *inside* the Gitblit instance. The plugin is an
  implementation detail of consuming Gitblit, not a separately-addressable
  provider this repo models — so it is **not** a second edge/element. The base
  URL is `GITBLIT_URL`; the `/api/.mcp-internal` path is appended in code.
- No external SaaS is called → no `svc:` external element minted.
- `grep -rIi '://'` over `src/` surfaced only the `GITBLIT_URL` scheme check and
  the server's own bind-URL log line — no hidden hardcoded base URLs.

## Exposed surface decision

The server exposes one HTTP/SSE MCP endpoint (FastMCP; `MCP_HOST`/`MCP_PORT`/
`MCP_PATH_PREFIX` configure bind + path, default `/sse` and `/messages/`). Modeled
as ONE ApplicationService realized by the product + ONE ApplicationInterface
(consumer class = MCP clients). Per-tool routes are NOT modeled (endpoint
inventory, not architecture).

## Excluded (inclusion-rule / convention)

- **Per-tool MCP routes** (`gb_list_repos`, … six tools) — routes, not distinct
  consumer classes; grouped under the single service/interface.
- **`/sse` vs `/messages/`** as separate interfaces — same consumer class (MCP
  clients), one interface.
- **`../GitblitSearchApiPlugin` companion Java plugin** — at HEAD this repo is
  standalone; the plugin lives in its own repo and is deployed into Gitblit. It
  is part of the Gitblit provider, reached transitively via `cap:source-control`;
  not an element this producer owns. Would be a separate producer if/when it
  onboards.
- **Config knobs** (`MCP_PORT`, `MCP_HOST`, `MCP_PATH_PREFIX`, `REPO_CACHE_TTL`)
  — runtime state, no external named identity. Out per the identity fence.
- **Deployed instances / `environment` / `cluster`** — left unset; per-env
  placement and the `Specialization` instance→product edges belong to the
  deploying producer (helm-charts), not this hand-authored logical artifact.

## Cross-producer references

- `cap:source-control` — curated-enum reference, resolved by bare name (no UUID
  needed). No other producer's UUIDs are referenced, so there are no dangling
  cross-producer refs from this artifact.

## Open questions (would have asked a human)

- **Capability choice.** `cap:source-control` is the best enum fit for "AI read
  access to Git repos via Gitblit." Confirm this over, say, treating the Search
  API Plugin as a distinct in-house provider service (which would need that
  plugin onboarded as its own producer with a `svc:` to reference by UUID).
- **`stats.image`.** Recorded `registry:5000/gitblit-mcp-server` as a
  non-load-bearing stat. Container-image identity is a v0.2 concern; confirm
  whether to keep it here or drop it.
- **Single interface.** Assumed one consumer class (MCP clients). If there's a
  separate privileged/admin consumer in practice, a second `if:` would be
  warranted.
