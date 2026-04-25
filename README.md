# Bytloop POS

A multi-tenant SaaS POS platform covering retail, F&B, hospitality, services, and specialty verticals.

Full plan: [docs/PLAN.md](docs/PLAN.md) · Variant catalog: [docs/pos-variants.md](docs/pos-variants.md)

## Architecture

- **Backend:** FastAPI modular monolith (`backend/`) — strict bounded-context modules, enforced via `import-linter`
- **Frontend:** Next.js 16 (`frontend/`) — Server Components by default, SSR + prefetch, shadcn/ui
- **Repo:** plain two-folder layout — no monorepo tooling

## What's in the box

### Core modules (backend)
- `identity` — signup + email activation + login + Google/GitHub OAuth + refresh + `/auth/me`
- `tenants` — multi-tenant workspace isolation (row-level `tenant_id`)
- `catalog` — products + categories (+ JSONB `vertical_data`)
- `inventory` — locations, inventory levels, stock-movement ledger
- `sales` — orders, order items, payments, cash checkout, order history
- `customers` — CRM-lite contact profiles
- `discounts` — percent + fixed via Strategy
- `tax` — configurable rates
- `shifts` — cashier open/close with cash variance
- `reporting` — dashboard sales summaries
- `audit` — immutable event log, correlation-id tagged

### Verticals
Every vertical is a plugin module with its own entity + service + router:
- **F&B** — restaurant (tables, KOT, KDS with WebSocket push)
- **Retail** — apparel (variant matrix), grocery (PLU + weighable)
- **Services** — garage (jobs), gym (memberships + check-in), salon (appointments)
- **Hospitality** — hotel (rooms + reservations with overlap detection)
- **Specialty** — pharmacy (batches + expiry), cinema (shows + seats), rental (assets + contracts), jewelry (karat/weight)

### Integrations
- **Email adapters** (Strategy): SMTP (dev/MailHog) · Mailgun (prod) · SendGrid (stub) · `QueuedEmailAdapter` to route through Celery
- **Payment providers** (Strategy): Cash · bKash (sandbox-ready) · Stripe (PaymentIntents)
- **Payment webhooks** with HMAC signature verification for Stripe + bKash
- **Observability**: structlog, correlation ID middleware, Sentry (prod)
- **Real-time**: Redis pub/sub → WebSocket (KDS live updates)
- **Offline POS**: IndexedDB mutation queue with ULID idempotency keys, auto-drain on reconnect

## Local development (no Docker)

One-time prereqs:

| Tool | Purpose | Install |
|---|---|---|
| PostgreSQL + pgAdmin | Primary DB | https://www.postgresql.org/download/windows/ |
| Memurai | Redis-compatible Windows service | https://www.memurai.com/get-memurai |
| MailHog | Local SMTP catcher | https://github.com/mailhog/MailHog/releases |
| uv | Python tooling | https://docs.astral.sh/uv/getting-started/installation/ |
| Node.js LTS + pnpm | Frontend tooling | https://nodejs.org/ + `corepack enable` |

### First-time setup

```powershell
# 1. Create the databases
psql -U postgres -c "CREATE DATABASE bytloop_pos;"
psql -U postgres -c "CREATE DATABASE bytloop_pos_test;"

# 2. Backend deps + migrations
cd backend
copy .env.example .env                # edit AUTH_JWT_SECRET etc.
uv sync --all-groups
uv run alembic upgrade head

# 3. Frontend deps
cd ..\frontend
copy .env.example .env.local
pnpm install

# 4. Optional: pull shadcn components (already committed, but re-running is idempotent)
# npx shadcn@latest add --all --yes
```

### Running

Start the supporting services (Postgres + Memurai as Windows services; MailHog as a process), then:

```powershell
./scripts/dev-start.ps1                # checks services and opens MailHog if needed

# Terminal 1 — backend API
cd backend
uv run uvicorn src.main:app --reload

# Terminal 2 — Celery worker (for queued emails, scheduled tasks)
cd backend
uv run celery -A src.tasks.app worker --loglevel=info

# Terminal 3 — Celery Beat (cron scheduler)
cd backend
uv run celery -A src.tasks.app beat --loglevel=info

# Terminal 4 — frontend
cd frontend
pnpm dev

# One-time after backend is up: regenerate the TS client
cd frontend
pnpm generate:api
```

- Backend API: http://localhost:8000 (`/docs` for OpenAPI UI in dev)
- Frontend: http://localhost:3000
- MailHog inbox: http://localhost:8025

## Rules

- **Package manager is pnpm only** — npm and yarn are blocked by a preinstall guard.
- **TDD** is mandatory in both apps. Red → Green → Refactor.
- **No `any` in TypeScript.** Enforced by ESLint.
- **No Docker in local development.** Services run natively.
- **No raw enum values or IDs rendered as user-visible text.** Use `<EnumSelect>`, `<EnumBadge>`, `<EntityLabel>`.
- **Module boundaries** in the backend are enforced — other modules may only import from a module's `api.py`.
- **Free-tier aware.** All production settings respect 20 MB Redis + ~20 Neon connections. Circuit breakers keep the app alive when those tier out.

## CI

Every PR runs in GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)):
- Backend: `ruff` + `mypy --strict` + `lint-imports` + `pytest --cov`
- Frontend: `pnpm lint` + `pnpm typecheck` + `pnpm test:coverage` + `pnpm build`

Postgres and Redis run as GitHub Actions `services:` — no Docker required in the dev loop.

## Testing (TDD mandatory)

Backend (pytest with transactional-rollback fixture against a local Postgres test DB):
```powershell
cd backend
uv run pytest
```

Frontend (Vitest + React Testing Library + MSW + Playwright):
```powershell
cd frontend
pnpm test             # Vitest
pnpm e2e              # Playwright (needs backend + frontend running)
```

## Layout

```
bytloop-pos/
├── backend/
│   ├── src/
│   │   ├── core/              config, db, errors, logging, correlation, permissions, security, cache, realtime
│   │   ├── modules/           audit, catalog, customers, discounts, identity, inventory, reporting, sales, shifts, tax, tenants
│   │   ├── verticals/         fnb (restaurant), retail (apparel, grocery), hospitality (hotel), services (garage, gym, salon), specialty (cinema, jewelry, pharmacy, rental)
│   │   ├── integrations/      email (SMTP/Mailgun/queued), payments (cash/bkash/stripe + webhooks), sms, storage
│   │   └── tasks/             Celery app + email tasks + Beat schedule
│   ├── tests/                 core, modules/*, verticals/*
│   └── migrations/            Alembic
├── frontend/
│   ├── src/
│   │   ├── app/               (public), (guest), (auth), (admin) route groups + /activate, /403
│   │   ├── components/
│   │   │   ├── shared/        ui (shadcn), errors, enum-display, backgrounds, layout
│   │   │   └── modules/       identity, catalog, customers, inventory, pos, sales, restaurant, apparel, pharmacy, garage, ...
│   │   ├── lib/               api/*, api-client/, realtime/, offline/, enums/, stores/, hooks/, seo.ts, rbac.ts, tracker.ts, i18n/
│   │   └── schemas/           Zod form schemas
│   ├── messages/              en.json, bn.json
│   └── e2e/                   Playwright
├── scripts/                   dev-start.ps1, generate-api-client.ps1
├── docs/                      PLAN.md, pos-variants.md
└── .github/workflows/ci.yml
```

See [docs/PLAN.md](docs/PLAN.md) for the complete specification.
