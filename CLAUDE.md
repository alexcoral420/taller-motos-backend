# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Backend + web for "Taller Surtimotos", a motorcycle repair shop. Python/FastAPI backend at the repo root (`app/`), Next.js frontend in `frontend/`. Code, comments, identifiers and commit messages are in Spanish — keep that convention.

## Commands

Backend (Python 3.11+, virtualenv in `.venv/`, config read from `.env`):

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload          # local dev; OpenAPI docs at /docs
python crear_admin.py                  # one-off: seed the first admin user (gitignored, edit ADMIN_* first)
```

Production (Railway) runs the `Procfile`: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

Frontend (`cd frontend`; needs `NEXT_PUBLIC_API_URL` in `frontend/.env.local`):

```bash
npm run dev      # http://localhost:3000
npm run build
npm run lint
```

There is no test suite and no migrations directory in the repo.

## Backend architecture

**Database:** the schema lives in Supabase (Postgres) and is managed there, not by the app. Never add `Base.metadata.create_all`. Models declare the existing `__tablename__`, and Postgres enums use `SqlEnum(..., name="<pg_enum>", create_type=False)`. `DATABASE_URL` must point at the Supabase connection pooler (port 6543), using psycopg2. `SECRET_KEY` and `DATABASE_URL` are required settings with no defaults (`app/core/config.py`).

**Every model must be imported in `app/main.py`** so SQLAlchemy can resolve the foreign keys between tables at startup. Add new models there.

**Three API trees, each with its own auth** (all mounted in `app/main.py`):
- `/api/public/*` (`app/api/public/`): the public website (catalog, quotes, contact, receipts by token). No auth. slowapi applies an IP rate limit (`PUBLIC_RATE_LIMIT`).
- `/api/v1/*` (`app/api/private/`): the internal panel. JWT via `Depends(get_current_user)` / `require_admin` from `app/api/private/deps.py`. Login is `POST /api/v1/auth/login` (OAuth2 password form).
- `/api/integracion/*` (`app/api/integracion/`): machine-to-machine access for the external compraventa (motorcycle resale) system. Uses the `X-API-Key` header, checked against `INTEGRACION_API_KEY` at the router level. It returns 503 if the key is not configured.

New routers must be registered in that tree's aggregator (`app/api/{public,private}/router.py`). The routers that are actually mounted live in `app/api/…`. `app/modules/ordenes/router.py` is an older copy that is **not** mounted; edit `app/api/private/ordenes_router.py` instead.

**Layering per domain module** (`app/modules/<dominio>/`: `model.py`, `schema.py`, `repository.py`, `service.py`):
- router → service → repository → DB.
- Repositories extend `BaseRepository` (`app/base/base_repository.py`). They never raise HTTP errors and return `None` or empty lists instead. Write methods take `commit=True`. Multi-table atomic operations pass `commit=False` (flush only), and the service commits once at the end.
- Services raise domain exceptions defined at the top of each `service.py` (e.g. `OrdenNoEncontrada`, `NoAutorizado`). Routers catch these and map them to `HTTPException` status codes.
- Models use the mixins in `app/base/base_model.py` (`PKMixin`, `TimestampMixin`, `CreatedAtMixin`).

**Domain rules worth knowing:**
- Work orders (`ordenes`) are either `interna` or `externa`. An internal order requires a license plate (`placa`) and has no client: it is a reconditioning cost for a motorcycle in the resale inventory, exposed to the compraventa system through `/api/integracion/gasto-por-placa/{placa}`. An external order creates or saves a `Cliente` and counts as shop revenue. Item prices come from the technician (they are negotiable), not from the catalog. The technician's commission is frozen on each labor item.
- Payments (`pagos`): only external orders can be settled (liquidadas). Only the technician who owns the order can settle it, and only once. Settling creates a `Pago` and sets the order to `liquidada` in the same transaction. Each `Pago` has a `public_token`, which the public receipt endpoint (`/api/public/recibo/{token}`) uses.
- Nequi payments go through Wompi (`app/modules/pagos/wompi.py`, sandbox by default through `WOMPI_URL`). The flow creates a `pendiente` payment, sends the push to the client, and then the panel polls `confirmar_cobro_nequi`, which checks Wompi and sets the payment to `confirmado` (order `liquidada`) or `fallido`. Wompi amounts are in **cents** (pesos × 100).

## Frontend

Next.js 16 / React 19 / Tailwind 4, App Router under `frontend/app/`. **Read `frontend/AGENTS.md` first.** This Next.js version has breaking changes compared with your training data, so check `frontend/node_modules/next/dist/docs/` before writing Next code. Public site pages sit at the top level (`/`, `/cotizar`, `/contacto`). The staff panel is under `/panel`. Panel requests go through `fetchAuth` in `frontend/app/lib/auth.ts`. That helper keeps the JWT in localStorage, attaches the `Bearer` header, and redirects to `/panel/login` on a 401. Public pages call `fetch` directly against `${NEXT_PUBLIC_API_URL}/api/public/...`.
