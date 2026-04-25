# Bytloop POS — Implementation Plan

A unified multi-vertical POS platform covering the 55 variants in [pos-variants.md](pos-variants.md).

---

## 1. Stack Decision: FastAPI OpenAPI → TS Client ✅

tRPC is TypeScript-only. Decision: FastAPI auto-generates OpenAPI; `openapi-ts` emits a fully-typed `fetch`-based TS client consumed via React Query. End-to-end type safety, idiomatic Python backend.

---

## 2. Architecture: Modular Core + Vertical Plugins

80% of POS logic is shared (products / orders / payments / inventory / customers / staff / reports). Only 20% is vertical-specific. Build core once; each vertical is a thin plugin (data models + screens + reports + settings). Per-tenant feature flags enable verticals.

```
Core POS Engine ─┬─ Retail pack (apparel, grocery, pharmacy, jewelry, ...)
                 ├─ F&B pack (restaurant, QSR, bar, café, ...)
                 ├─ Hospitality pack (hotel, spa, event, ...)
                 ├─ Services pack (garage, gym, salon, laundry, ...)
                 └─ Specialty pack (museum, cinema, rental, ...)
```

---

## 3. Multi-Tenant SaaS ✅

- Single deployment, row-level isolation via `tenant_id` on every table
- Subdomain routing: `acme.bytloop-pos.com`
- Per-tenant feature flags gate vertical packs
- Markets: **Bangladesh + Global** — multi-currency and dual payment provider groups, all driven from the Global Configuration SSOT (see §4a)

---

## 4. Tech Stack

### Backend (Python)
- **FastAPI** (OpenAPI auto-gen)
- **SQLAlchemy 2.x** async + **Alembic** migrations
- **Pydantic v2** (`alias_generator=to_camel`, `populate_by_name=True` → camelCase API I/O, snake_case internally)
- **PostgreSQL** — local via pgAdmin; prod Neon (connection string)
- **Redis** — cache, pub/sub, rate limit, sessions, resend cooldown
- **Celery** (IO / background / CPU) + **Celery Beat** (cron/scheduled)
- **structlog** — pretty console in dev, JSON in prod; Sentry (prod, added later)
- **Auth:** JWT (15m access in memory + 30d refresh in httpOnly cookie), Argon2 hashing, Google + GitHub OAuth
- **Email:** pluggable `EmailAdapter` (Strategy) — SMTP/MailHog (dev) + **Mailgun (prod primary)** + SendGrid (future stub)
- **pytest** + **mypy strict**

### Frontend (Next.js)
- **Next.js 16** (App Router) + TypeScript **strict**, no `any` anywhere
- **Server Components by default.** Client Components only when strictly needed (interactivity, browser APIs, stores).
- **SSR + prefetch** via React Query `HydrationBoundary` on Server Components
- **TailwindCSS** + **shadcn/ui**
- **React Query** (server state) + **Zustand** (client state)
- **React Hook Form** + **Zod** (same schemas used for backend validation)
- **openapi-ts** generated client + typed React Query hooks
- **next-intl** (Bangla + English, RTL-ready)
- **ESLint strict** — CI blocks on any lint error
- **Avoid `useEffect`** unless strictly required

### Infra & Ops
- **Modular monolith** — single repo, two folders (`backend/`, `frontend/`), no monorepo tooling (no Turborepo, no pnpm workspaces)
- **No Docker for local dev.** All services run natively on Windows:
  - **PostgreSQL** — native Windows install, managed via pgAdmin
  - **Redis** — **Memurai** (free Developer edition, Redis-compatible Windows service)
  - **MailHog** — native Windows binary, run as a background process / Windows service
  - Backend via `uvicorn --reload` in a `uv` venv; frontend via `pnpm dev`
  - Celery worker + Celery Beat as background processes in the same venv
- **Docker is optional for prod only** (build artifact for Railway/Fly) — never required to run the stack locally
- **GitHub Actions** CI: lint · typecheck · test · build
- Vercel (frontend) · Railway/Fly (backend) · Neon (Postgres) · Upstash (Redis) · Mailgun (email) · Sentry (errors) · PostHog (analytics — recommended)

---

## 4a. Global Configuration (Single Source of Truth)

Every tunable behavior in the system is defined in **one** place and loaded from environment variables. No magic numbers scattered across the codebase, no hardcoded provider lists, no duplicated currency arrays in frontend and backend.

### Backend — `core/config.py` (Pydantic `BaseSettings`)

```python
class AuthConfig(BaseSettings):
    access_token_ttl_seconds: int = 86400        # 1 day default — env: AUTH_ACCESS_TOKEN_TTL_SECONDS
    refresh_token_ttl_seconds: int = 2592000     # 30 days default — env: AUTH_REFRESH_TOKEN_TTL_SECONDS
    activation_token_ttl_seconds: int = 86400    # 1 day — env: AUTH_ACTIVATION_TOKEN_TTL_SECONDS
    resend_cooldown_seconds: int = 300           # 5 min — env: AUTH_RESEND_COOLDOWN_SECONDS
    password_min_length: int = 8
    argon2_time_cost: int = 3
    argon2_memory_cost_kib: int = 65536

class CurrencyConfig(BaseSettings):
    supported: list[str] = ["BDT", "USD"]        # env: CURRENCY_SUPPORTED (CSV)
    default: str = "BDT"                         # env: CURRENCY_DEFAULT
    exchange_rate_provider: str = "exchangerate_host"

class PaymentConfig(BaseSettings):
    bd_providers: list[str] = ["bkash", "nagad", "sslcommerz", "rocket"]
    global_providers: list[str] = ["stripe", "paypal"]
    default_by_country: dict[str, str] = {"BD": "bkash", "default": "stripe"}

class EmailConfig(BaseSettings):
    provider: Literal["smtp", "mailgun", "sendgrid"] = "smtp"  # env: EMAIL_PROVIDER
    from_address: str
    # provider-specific settings (smtp_host, mailgun_api_key, …) under env namespaces

class FeatureFlags(BaseSettings):
    enable_offline_pos: bool = False
    enable_vertical_marketplace: bool = False
    # ... per-tenant overrides live in DB, read at runtime

class RedisConfig(BaseSettings):
    url: str = "redis://localhost:6379"          # env: REDIS_URL
    db_index: int = 0                            # env: REDIS_DB (test suite uses 15)
    max_app_connections: int = 15                # FastAPI pool
    max_celery_broker_connections: int = 8
    max_celery_result_connections: int = 4
    socket_timeout_seconds: float = 2.0
    socket_connect_timeout_seconds: float = 1.0
    op_timeout_seconds: float = 1.0              # wrapper hard timeout
    circuit_breaker_threshold: int = 5
    circuit_breaker_cooldown_seconds: int = 30

class DatabaseConfig(BaseSettings):
    url: str                                     # env: DATABASE_URL — local: postgresql+asyncpg://…localhost…; prod: Neon pooled endpoint
    pool_size: int = 8
    max_overflow: int = 4
    pool_recycle_seconds: int = 300
    pool_timeout_seconds: int = 5
    pool_pre_ping: bool = True

class Settings(BaseSettings):
    auth: AuthConfig = AuthConfig()
    currency: CurrencyConfig = CurrencyConfig()
    payments: PaymentConfig = PaymentConfig()
    email: EmailConfig = EmailConfig()
    features: FeatureFlags = FeatureFlags()
    redis: RedisConfig = RedisConfig()           # env: REDIS_URL etc.
    database: DatabaseConfig = DatabaseConfig()  # env: DATABASE_URL etc.
    # sentry, posthog, etc.

settings = Settings()   # single module-level instance, imported everywhere
```

All `.env.example` keys map 1:1 to these fields. The **only** place `auth.access_token_ttl_seconds` is read. Every module that needs a TTL imports `settings.auth.access_token_ttl_seconds` — no local defaults, no duplicated constants.

### Frontend — public config endpoint

Backend exposes a **public read-only** `GET /config` endpoint returning only the client-safe subset:

```json
{
  "currencies": { "supported": ["BDT", "USD"], "default": "BDT" },
  "payments": { "providers_by_country": { "BD": ["bkash", "nagad", "sslcommerz", "rocket"], "default": ["stripe", "paypal"] } },
  "auth": { "resend_cooldown_seconds": 300, "password_min_length": 8 },
  "features": { "offline_pos": false }
}
```

Frontend loads this once at app boot (Server Component root layout) and exposes it via a `ConfigProvider` + `useConfig()` hook. No currency list, no provider list, no cooldown number is hardcoded in frontend code — all read from config.

### Per-tenant overrides
Tenants can override a whitelisted subset (e.g. `default_currency`, `enabled_payment_providers`, `default_locale`) via the `tenants.config` JSONB column. Resolved at request time: global `settings` → tenant overrides → (later) user preferences.

---

## 5. Conventions

### Naming

| Layer | Case | Example |
|---|---|---|
| DB tables & columns | `snake_case` | `product_variants.sku_code` |
| Python variables, functions | `snake_case` | `get_user_by_id` |
| Python classes | `PascalCase` | `ProductRepository` |
| SQLAlchemy entity attributes | `snake_case` | `product.sku_code` |
| Pydantic schema fields (internal) | `snake_case` | `sku_code` |
| **API payload fields (over the wire)** | `camelCase` via alias generator | `skuCode` |
| TS variables, object properties, Zod fields, entity properties in FE | `camelCase` | `skuCode` |
| TS types, React components | `PascalCase` | `ProductCard` |
| **File names** | `kebab-case` | `product-card.tsx`, `product-repository.py` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |

**Boundary mapping:** Pydantic `alias_generator=to_camel` + `populate_by_name=True` auto-converts between snake_case Python and camelCase JSON. Generated TS client sees camelCase everywhere. No manual field mapping in routers.

### Coding rules
- **No `any`** in TS (`"@typescript-eslint/no-explicit-any": "error"`)
- **No `useEffect`** unless strictly needed — prefer Server Components, React Query, event handlers, derived state
- All forms: React Hook Form + Zod; schemas live in `packages/schemas` and are shared with backend where possible
- All DB writes in transactions; bulk ops chunked (e.g., 500 rows)
- Reads use `selectinload` / `joinedload` to avoid N+1
- Private routes protected by auth + RBAC; roles/permissions from single source of truth (`core/permissions.py` backend → mirrored `src/lib/rbac.ts` frontend, placeholder roles for now)
- No ESLint violations permitted in CI
- **Package manager is pnpm** (never npm, never yarn). `frontend/package.json` has `"packageManager": "pnpm@<version>"` and the repo ships a `.npmrc` with `engine-strict=true`. A `preinstall` script (`npx only-allow pnpm`) blocks `npm install` / `yarn install` with a clear error.

---

## 6. Architectural Patterns

### Entity / Service / Repository (per module)
```
apps/api/src/modules/products/
├── entity.py         SQLAlchemy model + ProductHelpers (entity-level helpers/formatters/invariants)
├── repository.py     DB access only — no HTTP, no business logic
├── service.py        Business logic, orchestration, transactions
├── schemas.py        Pydantic I/O (camelCase alias)
├── router.py         FastAPI endpoints — thin; delegates to service
└── tests/
```

- **Router** stays thin: auth + permission deps + schema binding + call service.
- **Service** owns business logic + transactions + cross-repository orchestration.
- **Repository** owns DB access — nothing else.
- **Entity helpers** class: per-entity helper functions (derived values, formatters, domain checks) kept off the ORM model.

### Strategy / Adapter for pluggable services
```
apps/api/src/integrations/email/
├── base.py             EmailAdapter (ABC)
├── smtp-adapter.py     local / MailHog
├── mailgun-adapter.py  prod primary
├── sendgrid-adapter.py future
└── factory.py          returns adapter from config
```
Same pattern for **payments**, **SMS**, **storage**. Services depend on the abstract interface, not a concrete provider — swap providers via config, no code changes.

### Modular Monolith (backend)
- **One deployable FastAPI app**, internally partitioned into strict **bounded-context modules** (`identity`, `catalog`, `inventory`, `sales`, `customers`, `reporting`, ...)
- **Module isolation rules (enforced):**
  - Each module owns its tables. No cross-module DB reads — ever.
  - Modules communicate only via another module's **public `api.py`** (exported service functions / DTOs). Internals (`entity.py`, `repository.py`, `web/`) are off-limits to other modules.
  - Cross-module events flow through an internal event bus (`app/events/`) for loose coupling.
  - Shared cross-cutting concerns (tenant, auth, errors, logging) live in `app/core/` — not a module.
- **Enforced in CI via `import-linter`** with a contract file (`importlinter.ini`): violations fail the build.
- **Future-proof:** any module can later be extracted into its own service with minimal refactor (its public `api.py` becomes the network boundary).

### KISS / DRY / SOLID
- Single responsibility per layer (Router / Service / Repository)
- Backend Pydantic = single source of truth for API schemas; OpenAPI generates TS types + Zod runtime schemas into the frontend (via `openapi-ts` + zod plugin) — no hand-maintained duplication
- Small composable components, not monoliths — break everything into focused parts

---

## 7. Repository Structure (Modular Monolith, no Docker)

Single repo, two self-contained applications. No Turborepo, no pnpm workspaces, no `docker-compose.yml`.

```
bytloop-pos/
├── backend/                 FastAPI modular monolith
│   ├── src/
│   ├── tests/
│   ├── migrations/          Alembic
│   ├── pyproject.toml       uv-managed
│   ├── importlinter.ini     module boundary contracts (CI-enforced)
│   └── .env.example
├── frontend/                Next.js 16
│   ├── src/
│   ├── package.json         pnpm
│   ├── next.config.ts
│   ├── eslint.config.mjs
│   └── .env.example
├── scripts/
│   ├── dev-start.ps1        starts MailHog + backend + frontend (+ reminds about Memurai/Postgres services)
│   └── generate-api-client.ps1   reads backend OpenAPI, regenerates frontend/src/lib/api-client
├── docs/
│   ├── pos-variants.md
│   └── PLAN.md              this file
└── README.md
```

Generated TS client lives directly in `frontend/src/lib/api-client/` — no shared package.


---

## 8. Backend Structure (Modular Monolith)

```
backend/
├── src/
│   ├── main.py                FastAPI app wiring
│   ├── core/                  Cross-cutting — NOT a module
│   │   ├── config.py
│   │   ├── db.py              async engine + session factory
│   │   ├── auth.py            JWT issuance/parsing/deps
│   │   ├── tenant.py          tenant resolution middleware
│   │   ├── errors.py          AppError hierarchy + global handlers
│   │   ├── logging.py         structlog config
│   │   ├── correlation.py     correlation-ID middleware + contextvars
│   │   ├── permissions.py     ROLES + PERMISSIONS single source of truth
│   │   ├── events.py          internal event bus
│   │   └── deps.py            shared FastAPI deps
│   ├── modules/               bounded contexts — strict isolation
│   │   ├── identity/          users, auth, sessions, OAuth accounts
│   │   │   ├── api.py         PUBLIC interface — other modules import ONLY from here
│   │   │   ├── entity.py      SQLAlchemy + entity-helpers class
│   │   │   ├── repository.py  DB access (private)
│   │   │   ├── service.py     business logic
│   │   │   ├── schemas.py     Pydantic I/O (camelCase alias)
│   │   │   ├── router.py      FastAPI endpoints
│   │   │   └── tests/
│   │   ├── catalog/           products, variants, categories
│   │   ├── inventory/         stock, locations, movements
│   │   ├── sales/             orders, order items, payments, receipts
│   │   ├── customers/
│   │   ├── staff/
│   │   ├── reporting/
│   │   ├── tax/
│   │   ├── promotions/
│   │   ├── printing/
│   │   └── audit/
│   ├── verticals/             vertical plugin packs
│   │   ├── retail/ fnb/ hospitality/ services/ specialty/
│   ├── integrations/          pluggable adapters (Strategy)
│   │   ├── email/             SMTP / Mailgun / SendGrid
│   │   ├── payments/          bKash / Nagad / SSLCommerz / Rocket / Stripe / PayPal
│   │   ├── storage/           S3 / local
│   │   └── sms/
│   └── tasks/                 Celery task definitions + Beat schedule
├── tests/                     cross-module / integration / contract
├── migrations/                Alembic
├── importlinter.ini           enforces: other modules may only import <module>.api
└── pyproject.toml             uv-managed
```

**Module boundary contract (`importlinter.ini`):** for every module `M`, disallow imports from outside `M` into `M.entity`, `M.repository`, `M.service`, `M.router`, `M.schemas`. Only `M.api` is exportable. CI fails on violation.

---

## 9. Frontend Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   ├── signup/
│   │   │   ├── activate/
│   │   │   ├── activate-pending/
│   │   │   ├── forgot-password/
│   │   │   └── reset-password/
│   │   ├── (dashboard)/
│   │   │   ├── pos/              main POS terminal
│   │   │   ├── products/
│   │   │   ├── inventory/
│   │   │   ├── orders/
│   │   │   ├── customers/
│   │   │   ├── reports/
│   │   │   ├── staff/
│   │   │   └── settings/
│   │   └── api/                  auth callbacks + webhooks only
│   ├── components/
│   │   ├── shared/               cross-module primitives (DataTable, EmptyState, Filters, SkeletonCard, SeoHead, error components, theme toggle, ...)
│   │   └── modules/              feature-scoped subcomponents
│   │       ├── auth/
│   │       ├── products/
│   │       ├── orders/
│   │       ├── pos/
│   │       ├── restaurant/
│   │       ├── apparel/
│   │       └── ...
│   ├── lib/
│   │   ├── api-client/           generated from backend OpenAPI (openapi-ts + zod plugin)
│   │   ├── api/                  client wrapper + interceptor + error normalizer
│   │   ├── stores/               Zustand stores
│   │   ├── hooks/                shared hooks
│   │   ├── seo.ts                SINGLE SOURCE OF TRUTH metadata factory
│   │   ├── rbac.ts               permission gates mirroring backend
│   │   ├── tracker.ts            analytics wrapper (PostHog)
│   │   └── utils/
│   ├── schemas/                  Zod schemas (from api-client generation + form-specific)
│   ├── types/
│   └── middleware.ts             tenant subdomain resolution + auth redirect
├── next.config.ts
├── tailwind.config.ts
├── eslint.config.mjs             strict, no-any, no unused, etc.
└── package.json
```

Files: `product-card.tsx`, `use-cart-store.ts` (kebab-case). Exports inside: `ProductCard`, `useCartStore`.

**Shared vs module:** used by 2+ features → `shared/`; scoped to one feature → `modules/<feature>/`. Break components down aggressively.

---

## 10. Core Domain Model

Tenant · Location · Terminal · User/Staff · Product · ProductVariant · Category · Inventory · StockMovement · Supplier · PurchaseOrder · Customer · Order · OrderItem · Payment · Discount · TaxRule · Receipt · Shift · AuditLog.

Vertical-specific data: lightweight → `vertical_data: JSONB` on the base entity; structured → sibling table (`restaurant_tables`, `apparel_variant_matrix`, `pharmacy_batches`, ...).

---

## 11. Authentication Flow

### Signup (`/signup`)
- Fields: **First name, Last name, Email, Password, Confirm password, Privacy & Terms checkbox** (required)
- RHF + Zod (shared schema)
- Creates user `email_verified=false` → adapter sends activation email with signed short-lived token

### Activate (`/activate?token=...`)
- Validates token → flips `email_verified=true` → redirect to login

### Login (`/login`)
- Email/Password + Google + GitHub
- **Last-used badge** next to the matching provider (from `localStorage.last_auth_method`)
- Email/password unverified → redirect to `/activate-pending` (no tokens)
- OAuth → auto-verified, tokens issued immediately
- JWTs issued **only** from these three paths

### Activate-pending (`/activate-pending`)
- Resend button with live **5-minute countdown** (`Resend in 4:32`)
- Cooldown enforced server-side via Redis `resend_cooldown:{user_id}` TTL 300s (429 if still active)
- Countdown persists across refresh (remaining TTL fetched from server)

### Forgot/Reset password
- Same token + adapter pattern; same 5-min resend cooldown

### Tokens (all TTLs configurable via env — defaults below, see §4a)
- **Access token:** default **1 day** (`AUTH_ACCESS_TOKEN_TTL_SECONDS=86400`), in memory (Zustand)
- **Refresh token:** default **30 days** (`AUTH_REFRESH_TOKEN_TTL_SECONDS=2592000`), httpOnly secure cookie, rotated on use
- **Activation token:** default **1 day** (`AUTH_ACTIVATION_TOKEN_TTL_SECONDS=86400`)
- **Resend cooldown:** default **5 min** (`AUTH_RESEND_COOLDOWN_SECONDS=300`)
- No TTL constants anywhere else in code — all read from `settings.auth.*` (§4a)

### RBAC (single source of truth)
- Backend: `core/permissions.py` defines `ROLES`, `PERMISSIONS`, role→permission map
- Frontend: `src/lib/rbac.ts` imports generated constants (placeholder roles: `owner`, `manager`, `cashier`, `kitchen`, `staff`)
- Enforcement: FastAPI dep (`requires("orders.create")`) · Next middleware · `<RequirePermission>` component

### Frontend route protection — every route is gated

Three exclusive route groups drive access control. Every page lives under exactly one of them — no unprotected routes.

| Group | Who can access | Wrong state → redirect |
|---|---|---|
| `(public)` | Anyone — marketing, pricing, legal | No redirect |
| `(guest)` | **Only unauthenticated** — `/login`, `/signup`, `/forgot-password`, `/reset-password` | Authed user → `/dashboard` |
| `(auth)` | **Authenticated + verified** — dashboard, POS, products, orders | Unauth → `/login?next=<path>`. Unverified → `/activate-pending` |
| `(admin)` | **Authenticated + permission** — settings, staff, billing, audit log | Unauth → `/login`. Authed without perm → 403 page |
| `/activate?token=…` | Special — token-based, no auth gate | n/a |

**Enforcement (defense in depth — UX layer only; backend is the real gate):**
1. **`src/middleware.ts`** (edge) — reads refresh cookie + lightweight JWT decode; applies redirect rules before any render. No flash of protected content.
2. **Route-group `layout.tsx`** — server-side `redirect()` from `next/navigation` as a second line. Fetches `/auth/me` once per route-group layout; passes user to children via a Server Context. `(guest)/layout.tsx` bounces authed users; `(auth)/layout.tsx` bounces unauth / unverified; `(admin)/layout.tsx` additionally calls `requirePermission("admin.access")`.
3. **`<RequirePermission permission="…">`** component — per-element gating inside pages (hide a button when user lacks `orders.refund`). Uses `lib/rbac.ts` SSOT.
4. **Backend** enforces again on every endpoint (`Depends(requires("…"))`). Frontend gating is UX; backend is authoritative.

---

## 12. Error Handling & Observability

### Backend
- Typed exception hierarchy: `AppError` → `NotFoundError`, `ValidationError`, `UnauthorizedError`, `ForbiddenError`, `ConflictError`, `RateLimitError`. Each carries `code` + `user_message`.
- **Correlation ID** (ULID) per request — middleware, `contextvars`, echoed as `X-Correlation-Id`, in every log line
- **structlog**: pretty console in dev (readable stacktrace in terminal), JSON in prod
- Global handlers for `AppError`, `RequestValidationError`, uncaught `Exception`

### Client-visible response shape (the ONLY shape that leaves the server)
```json
{ "error": { "correlation_id", "code", "message", "details" } }
```
**Whitelist policy** — response serializer emits only those four keys; anything else stripped. No branch of the code is permitted to append extras.

**Never leaked to client:** stacktraces, exception class names, raw `str(exc)`, SQL/constraint/table/column names, ORM internals, library names/versions, internal hostnames/paths/IDs, env vars, upstream dumps, timing internals.

**Pydantic validation errors sanitized** — only top-level field + human message. Internal `type`/`ctx`/`input`/nested paths are dropped.

### Prod hardening
- `debug=False`, disable `/docs`, `/redoc`, `/openapi.json` (served only to build pipeline)
- Strip `Server`, `X-Powered-By`
- Fuzz test every exception path — response must contain only whitelisted keys; forbidden substrings (`Traceback`, `sqlalchemy`, file paths, class names) must be absent
- Sentry (prod, later) keyed by correlation ID

### Frontend
- Central API interceptor normalizes every non-2xx + network error into `ApiError { correlationId, code, message, details }`
- Network failure → client-generated `client_<ulid>` correlation ID
- Error components in `src/components/shared/errors/`:
  - `<ErrorToast>`, `<ErrorDialog>`, `<InlineError>`, `<ErrorBoundary>`
- Each shows message + one-click **Copy ID** button (checkmark confirmation) + ID in monospace text (readable aloud)
- React Query global `onError` → central `showError()` helper routes to the right component

---

## 13. UX & Design Standards

- **Minimalist Maximalism** — restrained palette + whitespace, bold typography, purposeful density, confident accents. Modern, cohesive, opinionated — attention to micro-detail (focus rings, hover lifts, spacing rhythms, cursor affordances).
- **Modern, cohesive, responsive** — mobile-first; POS terminal optimized for tablet landscape + desktop
- **Animated SVG backgrounds** — modern layered SVG compositions with subtle motion (drifting orbs, parallax gradients, flowing particles, grid patterns, blob morphs) on:
  - Marketing / landing / pricing pages
  - Auth pages (login, signup, activate-pending, forgot/reset)
  - Empty states, error pages, 404/500
  - Dashboard greeting header (very subtle)
  - **Never** on the POS terminal screen or any data-dense operational view (distraction + performance cost)
  - Implementation via **Framer Motion** for path/transform animations, pure CSS/SVG `@keyframes` for loops, or **Rive**/Lottie for complex set pieces. Standardized primitives in `frontend/src/components/shared/backgrounds/` (e.g., `<GradientOrbs>`, `<AnimatedMesh>`, `<FloatingBlobs>`, `<GridParticles>`, `<AuroraWaves>`) — composable, themeable, tenant-accent-aware.
  - **Performance guardrails:** every animation wrapped in a `prefers-reduced-motion: reduce` media query → disables motion for users who opted out; GPU-accelerated transforms only (`transform`, `opacity` — never `width`/`height`/`top`/`left`); `will-change` hints sparingly; SVG inlined for small assets, lazy-loaded for large; degrades gracefully on low-end devices via `navigator.hardwareConcurrency` check
  - **a11y:** animations are decorative only — `aria-hidden="true"` on the SVG wrapper, `role="presentation"`. Never convey information through motion alone.
- **Every page** has explicit **loading** (`loading.tsx`), **error** (`error.tsx`), **success**, and **empty** states
- **Lists always include:** pagination (cursor or offset) · filters · **empty state** (illustration + CTA) · **skeleton loaders** matching final layout shape
- **SEO single source of truth:** `src/lib/seo.ts` exposes `buildMetadata({ title, description, path, image, noindex })` — every page calls it
- **Themes** (light/dark + tenant accent) via CSS variables; all shadcn components theme-aware

### Enum display rule (zero raw values in the UI)

Raw enum values (`SHIPPING_ADDRESS`, `IN_PROGRESS`, `order_refunded`) and raw IDs (UUIDs, numeric PKs) **must never be rendered as user-visible text** anywhere — Select options, Badges, Tables, Tooltips, Labels, Toasts, breadcrumbs. Everything the user reads is a human-friendly, i18n-aware label.

**Implementation (SSOT per enum):**

1. Enum TS types generated from backend OpenAPI (via `openapi-ts`). TS type uses the raw key (`'SHIPPING_ADDRESS'`).
2. **Label map + i18n key per enum**, co-located in `frontend/src/lib/enums/`:
   ```ts
   // src/lib/enums/address-type.ts
   import type { AddressType } from '@/lib/api-client';
   import { useTranslations } from 'next-intl';

   export const addressTypeI18nKey = (value: AddressType) => `enums.addressType.${value}`;

   export function useAddressTypeLabel() {
     const t = useTranslations();
     return (value: AddressType) => t(addressTypeI18nKey(value));
   }
   ```
   Translations live in `messages/en.json`, `messages/bn.json` — properly translated, never auto-case-converted as a shortcut.
3. **Shared primitives enforce the rule** (in `frontend/src/components/shared/`):
   - `<EnumSelect<T> options={values} getLabel={fn} value={v} onChange={...} />` — wraps shadcn Select; `SelectItem` `value` is the raw key; visible text from `getLabel`.
   - `<EnumBadge<T> value={v} getLabel={fn} variant="..." />` — shadcn Badge always displaying the human label.
   - `<EntityLabel id="..." entity="product" />` — resolves IDs → names (cached via React Query) for any "render by ID" need.
4. **Dev-only `humanize()`** (`SCREAMING_SNAKE_CASE → 'Screaming snake case'`) exists ONLY for developer surfaces (logs, devtools). Never used in user-visible UI.
5. **ESLint rule** via `no-restricted-syntax` forbids JSX text nodes that are direct references to enum-typed variables — catches `<span>{status}</span>` when `status` is an enum type. Reviewer watches for missed cases.
6. **Testing:** each enum's label map has a Vitest snapshot that asserts every enum member has a translation in every supported locale. Missing translation for any enum member fails CI.

**Reviewer rule:** if a value in the UI looks like code (`SCREAMING_SNAKE_CASE`, UUID, stringified ID), reject the PR.

---

## 14. Cross-Cutting Concerns

- **Offline POS** — IndexedDB queue, client-generated ULID order IDs, sync on reconnect
- **Real-time** — WebSockets (KDS, table status, order updates)
- **Receipt printing** — ESC/POS via browser print API + optional local bridge
- **Barcode** — keyboard-mode scanners (default) + camera fallback
- **Payments** — `PaymentProvider` strategy. Provider list, country defaults, and per-tenant overrides all read from Global Config (§4a). Built-ins: bKash, Nagad, SSLCommerz, Rocket (BD) + Stripe, PayPal (global).
- **Multi-currency** — Supported currencies + default read from Global Config (§4a). BDT + USD day 1, extensible via env. Exchange rate service for reports.
- **i18n** — Bangla + English day 1, RTL-ready
- **Audit log** — every write (user, tenant, entity, before/after JSON)
- **Analytics tracker** — `lib/tracker.ts` wraps PostHog (recommended) behind a stable API so the provider is swappable

---

## 15. Background & Scheduled Tasks

All IO-bound, CPU-intensive, or scheduled work runs in Python workers — never in the request path.

| Type | Tool |
|---|---|
| Async background jobs (email send, webhook retry, reports) | **Celery** on Redis broker |
| Long-running / CPU-intensive (PDF, bulk imports, rollups) | Celery with dedicated queue |
| Scheduled / cron (daily reports, cleanup, renewals) | **Celery Beat** |
| Lightweight in-process scheduling | **APScheduler** fallback |
| Streaming / event fan-out | Redis pub/sub (upgrade path: NATS / Kafka) |

All tasks: exponential backoff, idempotency keys on external calls, correlation ID + stacktrace on failure.

### Data operations
- All mutations in transactions
- Bulk inserts/updates/deletes via chunking (e.g., 500-row batches)
- `selectinload` / `joinedload` to avoid N+1
- Soft delete (`deleted_at`) where audit requires

---

## 15b. Free-Tier Resource Constraints (hard budgets)

Production runs on **Neon free** (≈20 conn, limited compute) and **Redis free** (20 MB memory, 30 conn). Every subsystem respects these budgets and **never blocks the server** when the free tier is saturated or unreachable.

**Environment-driven URLs (see §4a `RedisConfig` / `DatabaseConfig`):**
- Local dev: `REDIS_URL=redis://localhost:6379`, `DATABASE_URL=postgresql+asyncpg://…@localhost/bytloop_pos`
- Prod: `REDIS_URL=<free-tier Redis>`, `DATABASE_URL=<Neon pooled endpoint>`

Pool sizes, timeouts, and circuit-breaker thresholds are the **same in dev and prod** so local work exercises the same guardrails and catches regressions early. Only URLs (and Sentry/PostHog wiring) differ per env.

### Redis — 20 MB / 30 conn / non-blocking

**Connection budget (30 total):**
| Consumer | Max pool | Rationale |
|---|---|---|
| FastAPI app (`redis.asyncio.ConnectionPool`) | **15** | shared pool, hot path |
| Celery broker (worker) | **8** | bounded worker concurrency |
| Celery result backend | **4** | small result payloads, short TTL |
| Celery Beat scheduler | **1** | single process |
| Headroom | 2 | buffer for pub/sub transients |

All pools set with `max_connections` explicitly, `socket_timeout=2s`, `socket_connect_timeout=1s`, `retry_on_timeout=False`. No unbounded growth.

**Memory budget (20 MB):**
- **No general-purpose cache in Redis.** Hot-read caching is in-process LRU (`cachetools.TTLCache`) per app worker, invalidated by Redis pub/sub messages (tiny payloads: `{"type":"invalidate","key":"..."}`).
- **Allowed Redis workloads** (tiny keys, short TTLs): rate-limit counters, resend cooldown flags, idempotency keys, Celery broker queues, ephemeral pub/sub, WebSocket presence.
- **Forbidden:** session storage (we use stateless JWT anyway), large object cache, Celery result payloads beyond a tiny status dict.
- **Celery tuning for 20 MB:**
  - `result_expires = 60` (seconds) — clear results fast
  - `task_acks_late = True`, `worker_prefetch_multiplier = 1`
  - Task args/returns stay small (IDs only; fetch data from DB inside the task)
  - `broker_transport_options = {"visibility_timeout": 600, "max_connections": 8}`
- **Eviction policy** on the Redis instance: `allkeys-lru` (set via provider dashboard). Always-expire for everything we write.
- **Key namespacing:** `pos:{env}:{feature}:{id}` — easy audit, easy flush by prefix.

**Non-blocking isolation:**
- Every Redis call goes through `core/cache.py` wrapper with:
  - Hard 1-second timeout (connection + operation)
  - Circuit breaker (open after N consecutive failures, half-open after 30s)
  - **Graceful degradation:** cache miss or timeout = treat as "not cached", fall through to source; rate-limit unreachable = fail-open with a logged warning; pub/sub unreachable = in-process cache stays until TTL
- **Redis is never in the critical path for authentication** — JWT verification requires no Redis read (stateless). Resend cooldown uses Redis, but failure falls back to a safe "deny + retry later" response, never a hang.
- Redis health check at `/health/ready` is separate from the app's liveness probe; Redis being down does not take the app offline.

### Neon — 20 conn / limited compute

**Connection strategy:**
- **Use Neon's pooled endpoint** (PgBouncer-style `...-pooler.neon.tech`) — never the direct endpoint in prod.
- SQLAlchemy async engine:
  - `pool_size = 8`, `max_overflow = 4` for the FastAPI app (bound to `uvicorn --workers=1` in prod; scale via process count only after measuring)
  - `pool_pre_ping = True` (1 trivial query to detect dead conns via pooler)
  - `pool_recycle = 300` (5 min — avoid stale conns behind pooler)
  - `pool_timeout = 5` (fast fail; surfaces to user as a `RateLimitError` rather than hung request)
- Celery worker separate pool: `pool_size = 2`, `max_overflow = 2`
- **Leave ≥ 3 slots for Alembic migrations, pgAdmin sessions, and emergency debugging.**
- **No autoflush on request boundaries:** explicit commits, short transactions, release connections before I/O (email, external calls) — never hold a DB conn across an HTTP call.

**Compute optimization:**
- **Index discipline:** every `WHERE` filter column has an index; composite indexes lead with `tenant_id`. `EXPLAIN ANALYZE` required on any query reviewed in PR if it's on a hot path.
- **Avoid N+1** — enforced by `sqlalchemy.event` listener in dev that warns on per-row lazy loads; use `selectinload`/`joinedload`.
- **Cursor-based pagination** (keyset) on hot lists — never `OFFSET` beyond page ~10.
- **Selective columns** — use `select(Model.col_a, Model.col_b)` on read-heavy paths, not `select(Model)`.
- **No `COUNT(*)`** on large tables in hot paths — use cached counts, approximate counts (`pg_class.reltuples`), or paginated "show 'has more'" instead of totals.
- **In-process read-through cache** (per worker) for tenant config, product catalog hot keys, enum-type lookups, RBAC role maps. Backed by pub/sub invalidation (tiny Redis footprint).
- **Write batching:** accumulate writes where latency permits (audit log flushes, analytics events) and send as chunked inserts.
- **Background jobs do the heavy lifting** — reports, rollups, bulk imports all go to Celery, never run in the request path.
- **Connection leak canary:** periodic task compares `pool.status()` to expected; alert if checked-out conns exceed threshold.

**Non-blocking isolation:**
- Same circuit-breaker + fast-timeout pattern as Redis (`core/db.py`). If the pooler is saturated, the request fails fast with a `RateLimitError` surfaced to the user as "We're momentarily busy — try again in a moment" rather than a 30-second hang.
- Read-only endpoints can serve stale in-process cache when the pool is saturated (opt-in per endpoint).

### Observability for the budgets

- Metrics exported to the structured logger (and later Sentry/Grafana): `redis_pool_in_use`, `redis_memory_used_bytes`, `db_pool_in_use`, `db_pool_timeouts_total`, `circuit_breaker_state`.
- Load-test scenario in CI (k6 or Locust) that hammers the app and asserts Redis stays under 18 MB, DB pool stays ≤ 15 conns, p99 latency under threshold — blocks release if violated.
- Alert rules (later, when Sentry wired): DB pool > 80% utilized for > 1 min, Redis memory > 90%, circuit breaker open.

### When to upgrade off free tier
Capture triggers in `docs/ops.md`: Redis > 15 MB sustained, DB pool > 80% sustained, circuit breakers tripping in prod, p95 latency regressing. These are the signals to move to paid tiers — not traffic alone.

---

## 15a. Test-Driven Development (mandatory)

TDD is the **default development workflow** for every feature in both apps. Red → Green → Refactor. No code merges without tests that were written first (or at minimum, tests that prove the behavior).

### Backend — Python

**Stack**
- **pytest** + **pytest-asyncio** (async tests for async SQLAlchemy/FastAPI)
- **httpx.AsyncClient** — integration testing against the FastAPI app in-process
- **pytest-cov** — coverage reporting with thresholds enforced in CI
- **factory-boy** or custom factories — deterministic test data creation
- **freezegun** — time-dependent logic
- **pytest-mock** — light mocking where adapter seams aren't enough
- **Local test database** — dedicated Postgres DB (`bytloop_pos_test`) on the developer's native Postgres instance. Schema applied via Alembic before the session. Per-test isolation via **transaction-wrapped fixture rolled back on teardown** (no truncate cost, full parallel-safe when combined with session pooling). No SQLite fakery — we test against real Postgres for dialect-specific features (JSONB, array types, CTEs, etc.).
- **Local test Redis** — test DB index `15` on the developer's native Memurai instance, flushed between tests.
- **schemathesis** — property-based testing against OpenAPI schema (catches contract regressions)

**Test layers per module** (`apps/api/src/modules/<feature>/tests/`)
| Layer | What | Speed |
|---|---|---|
| **Unit — entity** | Entity helpers, invariants, derived values | ms |
| **Unit — service** | Business logic with mocked repository | ms |
| **Integration — repository** | Real DB via testcontainers, transaction-rolled-back fixtures | 10s of ms |
| **Integration — router** | Full HTTP round-trip with real DB, real auth | 10s of ms |
| **Contract** | Schemathesis fuzzes every endpoint against OpenAPI | runs in CI |

**Fixtures**
- `db_session` — transactional, rolled back per test (speed + isolation)
- `test_client` — `httpx.AsyncClient` bound to the FastAPI app
- `tenant_factory`, `user_factory`, `product_factory`, etc.
- `authenticated_client(role="manager")` — returns a client with valid JWT for a test user in a test tenant

**Non-exposure fuzz test** (from §12) lives here — runs every exception path and asserts response body contains only whitelisted keys and no forbidden substrings.

### Frontend — TypeScript / React

**Stack**
- **Vitest** — fast, Vite-native, works cleanly with Next.js 16 + TS
- **React Testing Library** — component tests, user-centric queries
- **MSW (Mock Service Worker)** — API mocking at the network layer (works in Node for tests and browser for dev)
- **@testing-library/user-event** — realistic interactions
- **Playwright** — E2E for critical flows (auth, checkout, POS terminal)
- **axe-core** via `@axe-core/playwright` — a11y assertions in E2E

**Test layers**
| Layer | What | Location |
|---|---|---|
| **Unit** | Pure utils, hooks, Zustand stores, Zod schemas | `*.test.ts` next to source |
| **Component** | Shared and module components with RTL + MSW | `*.test.tsx` next to source |
| **Page integration** | Server Component + Client Component together with MSW handlers | `src/app/**/__tests__/` |
| **E2E** | Full browser flows via Playwright | `apps/web/e2e/` |

**Critical E2E flows (must always pass):**
- Signup → activation email → activate → login
- Login as unverified → activate-pending with countdown → resend (mocked email bridge)
- Google + GitHub OAuth (happy path against stubs)
- "Last used" badge correctly reflects last successful method
- POS: add product → checkout cash → receipt renders → inventory decrements
- Error: trigger 500 → toast shows message + Copy-ID button → clipboard receives correct ID

### Coverage gates (CI-enforced)

| Layer | Minimum |
|---|---|
| Backend `service/` + `core/` | 90% |
| Backend `repository/` + `router/` | 80% |
| Frontend shared utils + stores + hooks | 90% |
| Frontend components | 70% |
| E2E — critical paths | 100% pass rate, no flakes |

### TDD workflow for every feature

1. Write the failing test (unit / component / integration, whichever level is appropriate)
2. Run it — confirm it fails for the right reason
3. Write the smallest code change that makes it pass
4. Refactor with tests green
5. Commit (tests + implementation together)

### CI pipeline (GitHub Actions)

Runs on every PR:
1. `pnpm lint` + `pnpm typecheck`
2. Backend: `pytest --cov` (fails below thresholds) + `mypy --strict`
3. Frontend: `vitest run --coverage` (fails below thresholds)
4. Schemathesis contract tests against ephemeral backend
5. Playwright E2E against the backend + frontend launched natively in the runner (GitHub Actions `services:` Postgres + Redis; backend/frontend as plain processes)
6. No PR merges red.

---

## 16. Phased Delivery

| Phase | Duration | Outcome |
|---|---|---|
| 0 — Foundation | 2–3 wk | Monorepo, CI, Docker, auth, tenant, OpenAPI→TS pipeline, shadcn baseline, error + logging + correlation-ID |
| 1 — Core POS MVP | 4–6 wk | Products, inventory, orders, cash, POS terminal UI, receipt print, General Retail vertical |
| 2 — Expand core | 4 wk | Multi-location, customers, discounts, tax, shifts, reports, bKash + Stripe |
| 3 — First verticals | 6–8 wk | Restaurant (tables/KOT/KDS), Apparel (variant matrix), Grocery (weight/PLU) |
| 4 — Expansion | ongoing | Pharmacy, jewelry, electronics, salon, gym, garage, hotel, cinema, rental, cannabis… ~1–2 wk each |
| 5 — Advanced | — | Offline, kiosk, mobile PWA, white-label, plugin marketplace |

---

## 17. Resolved / Open

**Resolved:** Stack bridge · Market · Deployment · Auth · DB · Timeline · Error handling policy · Naming conventions · Entity/Service/Repository · Strategy/Adapter · Background task approach · UX standards · SEO single source of truth · Email: SMTP (dev) + Mailgun (prod primary) + SendGrid (future stub).

**Open (non-blocking, reasonable defaults in place):**
1. **Analytics tracker** — default **PostHog** (open-source, self-hostable); confirm or swap.
2. **Hardware validation** — receipt printers / scales / cash drawers need physical device testing in a later phase.
3. **Regional compliance** — cannabis (METRC), pharmacy, fuel regulations scoped per vertical rollout.

---

## 18. Immediate Next Steps (execution order)

**Prereqs on the dev machine (install once, no Docker):**
- PostgreSQL (native Windows) + pgAdmin
- Memurai (Redis-compatible Windows service)
- MailHog (native binary, or install as Windows service)
- `uv` (Python), Node.js + pnpm

**Build order:**
1. Init repo: root `README.md`, `docs/PLAN.md`, `.gitignore`, `.editorconfig`, `scripts/dev-start.ps1` + `scripts/generate-api-client.ps1`
2. Scaffold `backend/`:
   - `uv` project, FastAPI + async SQLAlchemy + Alembic + Pydantic v2 (camelCase aliases)
   - `core/` (config, db, auth, tenant, errors, logging, correlation, permissions, events, deps)
   - structlog pretty-dev / JSON-prod
   - Celery + Celery Beat, `.env` with local Postgres/Memurai/MailHog URLs
   - **`importlinter.ini`** with module-boundary contracts
   - pytest + factory-boy + local test DB fixture with transactional rollback
3. Scaffold `frontend/`:
   - Next.js 16 (`src/` layout), Tailwind, shadcn init
   - Strict ESLint (no-any), TypeScript strict mode
   - React Query provider, Zustand, RHF + Zod
   - Vitest + RTL + MSW + Playwright
4. Wire `scripts/generate-api-client.ps1` — reads running backend OpenAPI, writes `frontend/src/lib/api-client/` (openapi-ts + zod plugin)
5. Stand up `integrations/email` with SMTP adapter (local MailHog) + Mailgun adapter behind factory
6. Implement `identity` module end-to-end **TDD-first**: failing router/service tests → signup → email → activate → login → Google/GitHub OAuth → refresh → logout → `me` (with activate-pending + 5-min countdown + last-used badge)
7. Implement shared error components with Copy-ID behavior (component tests first)
8. Build SEO factory · theme · shared primitives (`EmptyState`, `DataTable`, `Filters`, `SkeletonCard`) — tests first
9. Phase 1: `catalog` module (entity/repository/service/router, all TDD) → product list page (Server Component + prefetch + pagination + filters + empty state + skeletons) → POS terminal screen
