# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| SQLAlchemy 2.0, ORM, Alembic | python-sqlalchemy | .agents/skills/python-sqlalchemy/SKILL.md |
| React 19, Vite, Tailwind, antd | fe-react-dev-stack | .agents/skills/fe-react-dev-stack/SKILL.md |
| Full stack, monorepo, pnpm | fe-fullstack-dev | .agents/skills/fe-fullstack-dev/SKILL.md |
| PostgreSQL search, pgvector, BM25 | mastering-postgresql | .agents/skills/mastering-postgresql/SKILL.md |
| Dockerize, compose, healthchecks | docker-init | .agents/skills/docker-init/SKILL.md |
| JWT, authentication, tokens | jwt-auth | .agents/skills/jwt-auth/SKILL.md |
| REST API, OpenAPI, endpoints | rest-api-guidelines | .agents/skills/rest-api-guidelines/SKILL.md |
| Validation, Zod, Pydantic | loom-data-validation | .agents/skills/loom-data-validation/SKILL.md |
| FastAPI, Pydantic, SSE, DI | fastapi | .agents/skills/fastapi/SKILL.md |
| TDD, red-green-refactor | tdd | .agents/skills/tdd/SKILL.md |
| Jest, Vitest, Testing Library | javascript-testing-patterns | .agents/skills/javascript-testing-patterns/SKILL.md |
| Generate AGENTS.md/CLAUDE.md | agents-md-generator | .agents/skills/agents-md-generator/SKILL.md |
| Project foundation flow | active-orchestrator | ~/.config/opencode/skills/active-orchestrator/SKILL.md |
| Discover/install skills | find-skill | ~/.config/opencode/skills/find-skill/SKILL.md |
| Create knowledge base | kb-creator | ~/.config/opencode/skills/kb-creator/SKILL.md |
| Generate CHANGES.md | roadmap-generator | ~/.config/opencode/skills/roadmap-generator/SKILL.md |
| Create/modify skills | skill-creator | ~/.config/opencode/skills/skill-creator/SKILL.md |
| Archive OpenSpec changes | openspec-archive-change | .agents/skills/openspec-archive-change/SKILL.md |
| Design taste, anti-slop, UI typography | design-taste-frontend | .agents/skills/design-taste-frontend/SKILL.md |
| Emil design, UI polish, micro-interactions | emil-design-eng | .agents/skills/emil-design-eng/SKILL.md |
| UI/UX design intelligence, accessibility, styles | ui-ux-pro-max | .agents/skills/ui-ux-pro-max/SKILL.md |
| React performance, composition, clean hooks | vercel-react-best-practices | .agents/skills/vercel-react-best-practices/SKILL.md |

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`.

### python-sqlalchemy
- Use `select()` from SQLAlchemy 2.0, never legacy `Session.query()`
- Define models with `Mapped` + `mapped_column` on a `DeclarativeBase` subclass
- Repositories flush, never commit — transaction ownership belongs to the use case
- Use dialect-specific upsert (`on_conflict_do_update` for PostgreSQL) with returning clause
- For JSON columns, use `MutableDict.as_mutable(JSON)` to detect in-place mutations
- Relationships: use `relationship(back_populates=...)` with string forward refs for circular refs
- Async: prefer sync `def` unless fully async I/O path; use `async_sessionmaker` when needed

### fe-react-dev-stack
- Functional components only — no class components, no `this`, no lifecycle methods
- Use ahooks / TanStack Query hooks instead of raw `useEffect` for data fetching
- Page components: default export, PascalCase files in `src/pages/`
- Shared components: named export, PascalCase files in `src/components/`
- Import order: React → third-party → internal components → hooks/stores/services → types
- Tailwind for layout/spacing, shadcn / headless Radix for component styling — avoid custom CSS
- TypeScript strict mode (`strict: true` in tsconfig), no `any` type

### fe-fullstack-dev
- Monorepo or clean separation: `backend/` and `frontend/`
- Vite proxy `/api` → `http://localhost:8000` in `frontend/vite.config.ts`
- Shared contracts, DTO types and Zod validators matching backend OpenAPI schemas
- Run dev: backend on port 8000, frontend on port 5173

### mastering-postgresql
- Enable `pgvector` and `pg_trgm` extensions for vector search and trigram fuzzy search
- Full-text search: `tsvector` generated column + GIN index + `ts_rank`/`websearch_to_tsquery`
- Vector similarity: `embedding vector(1536)` + HNSW index (`m=16`, `ef_construction=100`)
- JSONB: GIN index for general queries, `jsonb_path_ops` for `@>` containment only
- Python drivers: `asyncpg` for max async performance, `psycopg3` for sync+modern, SQLAlchemy with asyncpg
- Index choice: HNSW for recall, IVFFlat for fast build, ScaNN on AlloyDB, pg_diskann on Azure
- Always `ANALYZE` after bulk loads; set `hnsw.ef_search` at query time for recall tuning

### docker-init
- Scan manifests (`package.json`, `pyproject.toml`, etc.) before proposing services
- Use official pinned images (alpine/slim variants), no invented image names
- Every service: `healthcheck`, `security_opt: [no-new-privileges:true]`, `deploy.resources.limits`
- Credentials as `${VAR}` refs to `.env`, `${VAR:?required}` for passwords
- No `version:` key in compose (deprecated); named volumes for data; networks for segmentation
- Multi-stage Dockerfiles: build stage with tooling, final stage with non-root user only
- `HEALTHCHECK` for HTTP services; `EXPOSE` real port; exec-form `CMD`
- Production overlay (`docker-compose.prod.yml`): no host ports, `restart: always`, tighter limits

### jwt-auth
- Stateless: no server-side session storage; embed claims in signed token
- Use HS256 or RS256; generate strong secret/key pair
- Issue tokens with standard bearer header or secure cookie
- Implement refresh token rotation with short-lived access tokens
- Always validate signature and expiration in middleware
- Never store sensitive data (passwords, PII) in JWT payload
- Plan for revocation: blocklist, short expiry, or token versioning

### rest-api-guidelines
- Resource-oriented URIs: noun-based paths (`/turnos`, not `/crear-turno`)
- Path major versioning: `/v1/turnos` or standard API paths
- PATCH for partial updates with `application/merge-patch+json`
- Repeated fields in PATCH = whole-list replacement unless subresource exists
- Token/cursor pagination: `pageSize`, `pageToken`, `nextPageToken`
- Errors: `application/problem+json` with `type`, `title`, `status`, `detail`, `instance`
- Opaque external string IDs (not internal sequential IDs)
- RFC 3339 timestamps, UTC; new fields additive, removals/renames = breaking

### loom-data-validation
- Parse, don't validate: return typed value (`Result<T>`), not bool; Zod `.parse()` / Pydantic `.model_validate()`
- Validate at boundary once, then trust typed value inward (HTTP handlers, queue consumers, CLI)
- Server-side authoritative; client-side validation is UX only
- Allowlist > denylist: enumerate permitted values (enums, char classes, known hosts)
- Canonicalize before validating: NFC normalize, lowercase host, resolve paths, decode percent-encoding
- Encoding ≠ validation: encode at sink for sink's context (HTML, attr, JS, URL, CSS, SQL, shell)
- Strict schemas: Zod `.strict()` / Pydantic `extra="forbid"` on request bodies (blocks overposting)
- Coercion pitfalls: `z.coerce.number()` turns `""`→`0`; `z.coerce.boolean()` turns `"false"`→`true`
- Output encode per sink: React auto-escapes text but not `href="javascript:..."` or `dangerouslySetInnerHTML`
- SQL: parameterized queries only; shells: argv arrays; paths: canonicalize + confine with separator check
- Max limits: body bytes, array length, object depth, string length — enforce before deep validation

### fastapi
- Use `Annotated[..., Depends(...)]` for all parameters and dependencies; create type aliases for reuse
- Prefer return types over `response_model`; use `response_model` only when public schema differs
- Router-level config: prefix, tags, shared dependencies on `APIRouter(...)`
- `async def` only when fully async I/O; default to `def` (runs in threadpool)
- Serve frontend: `app.frontend("/", directory="dist")` or `router.frontend()` for SPA assets
- SSE: `response_class=EventSourceResponse` + `yield ServerSentEvent(...)`
- One HTTP operation per function; don't mix GET/POST in same handler
- Pydantic v2: `ConfigDict(extra="forbid", str_strip_whitespace=True)` on request models
- No `RootModel`; use `Annotated[list[int], Field(min_length=1), Body()]` for array bodies

### tdd
- Red before green: write failing test first, then minimal code to pass
- Test behavior through public seams (interfaces), not implementation details
- Vertical slices: one test → one implementation → repeat (no horizontal slicing)
- Refactoring is separate review stage, not part of red→green loop
- Expected values from independent source of truth (literals, worked examples, spec)
- No implementation-coupled tests (mocks internals, tests private methods)
- No tautological tests (recomputing expected value same way as code)

### javascript-testing-patterns
- AAA pattern: Arrange, Act, Assert — one assertion per test (or logically related)
- Vitest config: coverage 80%+ branches/functions/lines/statements
- Mock external deps (fetch, network) via `vi.mock()` or MSW
- Test factories for realistic data with overrides
- Frontend: React Testing Library — semantic queries (`getByRole`, `getByPlaceholderText`)
- Hooks: `renderHook` + `act()` from `@testing-library/react`
- Spies for side effects with `vi.spyOn()` + `mockRestore()` in `afterEach`
- Async: `await` all promises; test error paths, not just happy paths

### design-taste-frontend
- Eliminate AI slop: no generic purple glows, no centered hero bias, no decorative AI clichés
- Typography: sans-serif pairing (`Geist`, `Inter` or clean system stack), tabular numbers for time/slots (`font-mono`)
- Color calibration: 1 primary neutral base (slate/zinc) + max 1 clinical accent color (e.g. teal/emerald/blue)
- Complete UI states: always render loading skeletons (not spinners), clean empty states, and inline error feedback
- Viewport stability: `min-h-[100dvh]` instead of `h-screen` to prevent iOS/mobile layout shifts
- Accessibility: 4.5:1 contrast, explicit focus rings, keyboard accessible elements

### emil-design-eng
- Craft invisible details: subtle borders, crisp transitions (150-200ms ease-out), spatial continuity
- Motion with purpose: motion explains state changes (dialog opens, tab switches); never animate for the sake of animating
- Interactive feedback: active states (`active:scale-[0.98]`), accessible tooltips, clear hover borders
- Medical domain clarity: tables and agendas must breathe, clean borders, high visual legibility

### ui-ux-pro-max
- Minimum touch targets 44x44px for tablet/touch dental screens
- Progressive disclosure: show essential appointment data upfront, expand details on demand
- Predictable navigation and clean breadcrumbs
- Safe areas and zero horizontal scroll on mobile viewports

### vercel-react-best-practices
- Single Responsibility: modular, isolated components in PascalCase
- Compound component patterns for dialogs, dropdowns, and complex form controls
- No `useEffect` for data fetching; use TanStack Query or `useRequest`
- Strict TypeScript: explicit prop interfaces, strict null checks, no `any`
- Skeleton loaders for CLS prevention

### agents-md-generator
- Pre-checks: KB exists (`knowledge-base/02_descripcion_general.md`), CHANGES.md optional
- Read global `~/.claude/CLAUDE.md` first — reference, don't duplicate its rules
- Derive candidate hard rules from actual stack (Python→Pydantic `extra="forbid"`, TS→no `any`, etc.)
- **Interactive confirmation** with user before writing project-specific hard rules
- Output `AGENTS.md` + `CLAUDE.md` at project root (copy, not symlink)
- Map skills to agent roles in table; reference `.atl/skill-registry.md` for compact rules
- Sections: Stack, KB links, Skills→Roles, Roadmap summary, Hard Rules, Workflow

### active-orchestrator
- Runs `openspec init` then dispatches foundation phases in order: discovery → kb → roadmap → find-skill → skill-registry → agent-instruction
- Owns `.active-orchestrator-state.json` with `step` field
- Commands: `/active-orchestrator:init`, `:kb`, `:rules`, `:discovery`, `:openspec`, `:devops`, `:find-skill`
- Use when starting new project from scratch using SDD/OpenSpec foundation flow

### find-skill
- Helps users discover/install skills when they ask "how do I do X" or "is there a skill for X"
- Scans available skills and suggests relevant ones based on query

### kb-creator
- Builds 10 canonical `.md` files at `knowledge-base/` (vision, stack, actors, data model, business rules, features, flows, architecture, decisions, open questions)
- Dual mode: silent generation from `docs/` sources, or interactive creation from scratch
- Trigger: "create knowledge base", "document project", "armar base de conocimiento"

### roadmap-generator
- Generates `CHANGES.md` with dependency tree, parallelism gates, critical path, multi-agent plan
- Per-change: scope, governance level, dependencies, "Leer antes" pointers to KB
- Fire-and-forget, no questions asked
- Trigger: "create roadmap", "armar CHANGES", "generar plan de implementación"

### skill-creator
- Create new skills, modify/improve existing skills, run evals, benchmark performance
- Optimize skill descriptions for triggering accuracy

### openspec-archive-change
- Archive completed change in experimental workflow
- Prompts for change, checks completion, archives with `.openspec.yaml`
- Use when user wants to finalize and archive a change after implementation

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| AGENTS.md | AGENTS.md | Canonical agent rules and stack constraints |
| CLAUDE.md | CLAUDE.md | Synced copy of AGENTS.md |
| knowledge-base/ | knowledge-base/ | 10 canonical domain markdown documents |
| CHANGES.md | CHANGES.md | Canonical OpenSpec roadmap of 18 changes |

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted — no need to read index files to discover more.
