# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| "Test-driven development", "red-green-refactor", "integration tests" | tdd | C:\Users\Andres\.agents\skills\tdd\SKILL.md |
| "REST API", "OpenAPI", "endpoint design", "HTTP JSON", "resource naming", "versioning", "pagination", "error format" | rest-api-guidelines | C:\Users\Andres\.agents\skills\rest-api-guidelines\SKILL.md |
| "FastAPI", "Pydantic", "SSE", "dependency injection", "async path operations", "serve frontend" | fastapi | C:\Users\Andres\.agents\skills\fastapi\SKILL.md |
| "full stack", "monorepo", "pnpm workspace", "React + Hono", "shared types" | fe-fullstack-dev | C:\Users\Andres\.agents\skills\fe-fullstack-dev\SKILL.md |
| "dockerize", "containerize", "docker-compose", "Dockerfile", "health checks", "security hardening" | docker-init | C:\Users\Andres\.agents\skills\docker-init\SKILL.md |
| "JWT", "authentication", "token", "stateless auth", "refresh token" | jwt-auth | C:\Users\Andres\.agents\skills\jwt-auth\SKILL.md |
| "archive change", "openspec archive", "finalize change" | openspec-archive-change | C:\Users\Andres\.agents\skills\openspec-archive-change\SKILL.md |
| "SQLAlchemy", "ORM", "async engine", "upsert", "relationships", "Alembic" | python-sqlalchemy | C:\Users\Andres\.agents\skills\python-sqlalchemy\SKILL.md |
| "Jest", "Vitest", "Testing Library", "unit test", "integration test", "mock", "TDD JavaScript" | javascript-testing-patterns | C:\Users\Andres\.agents\skills\javascript-testing-patterns\SKILL.md |
| "PostgreSQL search", "pgvector", "BM25", "JSONB index", "asyncpg", "full-text search", "vector similarity" | mastering-postgresql | C:\Users\Andres\.agents\skills\mastering-postgresql\SKILL.md |
| "React 19", "Vite", "Tailwind", "antd", "Zustand", "Jotai", "TanStack Query", "ahooks" | fe-react-dev-stack | C:\Users\Andres\.agents\skills\fe-react-dev-stack\SKILL.md |
| "validate", "Zod", "Pydantic", "schema", "sanitize", "XSS", "injection", "coercion" | loom-data-validation | C:\Users\Andres\.agents\skills\loom-data-validation\SKILL.md |
| "persistent memory", "mem_save", "mem_search", "session summary" | engram-memory | C:\Users\Andres\.agents\skills\engram-memory\SKILL.md |

## Compact Rules

### tdd
- Tests verify behavior through public interfaces (seams), never implementation details
- Agree on seams before writing tests — test only at confirmed seams
- Red before green: write failing test first, then minimal implementation
- One slice at a time: one seam, one test, one implementation per cycle
- No horizontal slicing (all tests then all code) — use vertical slices
- No implementation-coupled tests (mocks internals, tests private methods)
- No tautological tests (expected values derived same way as code)
- Refactoring is separate from the red→green loop

### rest-api-guidelines
- Use resource-oriented URIs with noun-based paths (not verbs)
- Path-based major versioning: `/v1/users`
- Use `PATCH` as default update method with `application/merge-patch+json`
- Pagination: token/cursor with `pageSize`, `pageToken`, `nextPageToken`
- Errors: `application/problem+json` format
- Use opaque external string IDs (not internal sequential IDs)
- RFC 3339 timestamps in UTC
- New fields = additive/safe; removals/renames/semantic changes = breaking

### fastapi
- Use `Annotated[..., Depends(...)]` for all dependencies and parameters
- Prefer return types over `response_model`; use `response_model` only when public schema differs
- Use `async def` only when logic is fully async-compatible; default to `def`
- Router-level prefix, tags, and shared dependencies on `APIRouter` itself
- No `ORJSONResponse`/`UJSONResponse` — Pydantic handles Rust-side serialization
- Serve frontend with `app.frontend("/")` or `router.frontend("/")` (not `StaticFiles`)
- SSE: `response_class=EventSourceResponse` + `yield ServerSentEvent(...)`
- No `...` ellipsis for required params or model fields
- One HTTP operation per function (separate GET/POST handlers)
- No `RootModel` — use regular type annotations with `Annotated`
- OpenTelemetry: use FastAPI native, install `fastapi[standard]`

### fe-fullstack-dev
- Monorepo structure: `web/` (React+Vite), `server/` (Hono), `packages/shared/` (types/validators)
- pnpm workspace with `pnpm-workspace.yaml` listing all packages
- Vite proxy `/api` → `http://localhost:3000`
- Shared types/validators in `packages/shared` imported via `@project/shared`
- Prisma for DB: `pnpm --filter server prisma generate|db push|migrate dev`
- API routes in `server/src/routes/`, validators in `server/src/validators/`
- Frontend services in `web/src/services/`, hooks with `useRequest` (ahooks)
- Root scripts: `dev`, `build`, `lint`, `clean` run across workspace

### docker-init
- Scan manifests first (`package.json`, `pyproject.toml`, etc.) before proposing services
- Read existing Docker files before modifying — never overwrite unread services
- Only official images with pinned tags (alpine/slim variants)
- Every service: healthcheck with interval/timeout/retries/start_period
- Security: `security_opt: [no-new-privileges:true]` on all services
- Resource limits: `deploy.resources.limits` for cpus and memory
- Credentials as `${VAR}` refs to `.env`; required vars use `${VAR:?required}`
- Named volumes for data; networks only for segmentation (frontend/backend/db)
- Kafka defaults to KRaft mode (single-node), not Zookeeper
- Dockerfile: multi-stage, non-root user, no secrets, HEALTHCHECK for HTTP apps
- No `version:` field in compose (deprecated)

### jwt-auth
- Stateless: no server-side session storage
- Use HMAC (HS256) or RSA (RS256) for signing
- Embed claims in payload; set appropriate expiration
- Store tokens in httpOnly cookies (browser)
- Implement refresh token mechanism
- Validate signature and expiration on every request
- Never store sensitive data in JWT payload
- Never use weak secret keys
- Plan for token revocation (blocklist, short expiry, rotation)

### openspec-archive-change
- Always prompt for change selection if not provided — never guess
- Check artifact completion via `openspec status --json`
- Check task completion in `tasks.md` (incomplete vs complete)
- Assess delta spec sync state if delta specs exist
- Archive to `openspec/changes/archive/YYYY-MM-DD-<name>`
- Preserve `.openspec.yaml` when moving to archive
- Show summary with change name, schema, archive location, sync status

### python-sqlalchemy
- Use SQLAlchemy 2.0 `select()` — not legacy `Session.query()`
- Models: `Mapped` + `mapped_column` with `DeclarativeBase`
- Session: `sessionmaker` + context manager; app owns transaction (`with session.begin()`)
- Repositories flush/add; they do NOT commit
- Upsert: PostgreSQL `insert().on_conflict_do_update()` with returning
- Relationships: `relationship(back_populates=...)` on both sides
- JSON: use `MutableDict.as_mutable(JSON)` for in-place mutation detection
- Alembic for migrations — review autogenerated revisions

### javascript-testing-patterns
- Follow AAA pattern: Arrange, Act, Assert
- One assertion per test (or logically related)
- Descriptive test names explaining what is tested
- Use `beforeEach`/`afterEach` for setup/teardown
- Mock external dependencies (keep tests isolated)
- Test edge cases, not just happy paths
- Test behavior, not implementation details
- Use test factories (`@faker-js/faker`) for consistent data
- Aim for 80%+ coverage
- Prefer `safeParse` over `parse` at boundaries (Zod/Vitest)
- Dependency injection for testing (interfaces for repositories)
- Integration tests: truncate tables in `beforeEach`, tear down in `afterAll`

### mastering-postgresql
- Docker: `pgvector/pgvector:pg17` with `pgvector` and `pg_trgm` extensions
- Search: `tsvector` + GIN index + `ts_rank` / `websearch_to_tsquery`
- Vectors: `vector(N)` + HNSW index (`m=16`, `ef_construction=64`, `ef_search=40`)
- JSONB: GIN index (general) or `jsonb_path_ops` (@> only)
- Arrays: GIN index
- Drivers: `psycopg2` (sync), `psycopg3` (async+modern), `asyncpg` (max perf), SQLAlchemy+asyncpg (ORM)
- Always `ANALYZE` after bulk loads; increase `maintenance_work_mem` for HNSW build
- Cloud: AlloyDB (ScaNN), Azure (pg_diskann), Neon/Supabase (serverless)

### fe-react-dev-stack
- Stack: React 19 + TS strict + Vite + Tailwind + antd + Zustand/Jotai + TanStack Query + ahooks
- Only functional components + hooks — NO class components, NO `this`, NO lifecycle methods
- Replace `useEffect` with ahooks: `useMount`, `useUnmount`, `useUpdateEffect`, `useEventListener`, `useDebounce`, `useRequest`, `useAntdTable`
- API calls in `services/` layer; state in `stores/` (Zustand/Jotai)
- Tailwind + antd `className` for styling — avoid raw CSS/style props
- Import order: React → 3rd party → internal components → hooks/stores/services → types
- Naming: pages default export, components named export, hooks `useXxx`, stores `useXxxStore`, services `fetchXxx/createXxx`, types `PascalCase`
- Unique stable keys for lists (never index)
- Ramda only for data transformation pipelines

### loom-data-validation
- Parse, don't validate: return typed value (`Result<User>`), not bool
- Validate at boundary once, then trust typed value inward
- Server-side authoritative; client-side is UX only
- Allowlist (enums, char classes) > denylist
- Canonicalize before validating: NFC, lowercase host, resolve paths, decode
- Encoding ≠ validation — encode at sink for sink's context
- Limits: cap length, array size, object depth, payload bytes (DoS prevention)
- Zod: `.strict()` on request bodies (reject unknown keys), `safeParse` at boundaries
- Pydantic v2: `extra="forbid"`, `ConfigDict`, `@field_validator` + `@classmethod`
- Never build SQL/HTML/shell by string concatenation
- Path traversal: `path.resolve(base, user)` + `startsWith(base + sep)`
- XSS: output-encode at every sink; sanitize stored HTML with allowlist (DOMPurify)
- ReDoS: avoid nested quantifiers, cap input length, use RE2 for untrusted patterns
- File uploads: validate by magic bytes, cap size, store outside webroot, server-generated names

### engram-memory
- ALWAYS ACTIVE — save decisions, conventions, bugs, discoveries proactively
- Save AFTER: decisions/conventions, bug fixes, features, discoveries, user confirmations
- `mem_save`: title (verb+what), type (bugfix/decision/architecture/discovery/pattern/config/preference), scope (project/personal/global), topic_key (stable key for evolving topics), content (What/Why/Where/Learned)
- Search: `mem_context` first, then `mem_search` with keywords
- Session close: MUST call `mem_session_summary` with Goal/Instructions/Discoveries/Accomplished/Next Steps/Relevant Files
- After compaction: immediately `mem_session_summary` with compacted content, then `mem_context`

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| (none found) | | No AGENTS.md, CLAUDE.md, .cursorrules, GEMINI.md, or copilot-instructions.md found in project root |