# Architecture — KrishiSetu

Status: PLANNED (no code exists). Builds on PRD.md and Research.md. Decisions are numbered `D-xxx` and mirrored in Memory.md.

---

## 1. Stack evaluation (not blindly accepting the suggested stack)

| Layer | Suggested | Alternatives considered | Decision | Why (3-day, single developer) |
|---|---|---|---|---|
| Frontend | React + Vite | Next.js; Streamlit; plain HTML | **React 18 + Vite + TypeScript** (D-002) | Mobile-first, role-based multi-screen UX needs a real SPA. Next.js SSR adds nothing. Streamlit is faster to start but cannot deliver the mobile-first, role-gated UX reliably. TypeScript gives AI agents a typed contract to code against. |
| Styling | Tailwind | CSS modules; MUI | **Tailwind CSS** | Utility classes are agent-friendly; tokens defined in Design.md |
| Backend | FastAPI | Flask; Django; Node | **FastAPI (Python 3.11)** (D-003) | ML, OR-Tools and API in one language and one process |
| DB | Postgres/Supabase | SQLite; Postgres in Docker | **SQLite via SQLAlchemy 2.x; schema kept Postgres-compatible** (D-004) | Zero setup, file DB, reproducible seed. Supabase rejected for MVP: extra network dependency during the demo, separate auth model, no benefit to the story. Postgres via `DATABASE_URL` is a config switch (FUTURE-tested). |
| ML | pandas, sklearn, XGBoost/LightGBM | Prophet; LSTM | **LightGBM** (+ sklearn baselines) (D-007) | Native quantile objectives, fast, small artifacts |
| Optimization | OR-Tools | OSRM trip; custom heuristic | **OR-Tools routing** (D-013) | Only option here that supports capacity + pickup/delivery pairing |
| Maps | OSM-based | Google Maps; Mapbox | **Leaflet + OSM tiles** (D-023) | No key, free; attribution required; schematic fallback when tiles fail |
| Routing distances | OSRM/OpenRouteService | Haversine | **Haversine × circuity default; OSRM optional** (D-014) | Offline, deterministic, demo-safe; public OSRM is rate-limited (Research §6) |
| Charts | Recharts | Chart.js | **Recharts** | React-native, enough |
| Migrations | — | Alembic | **None in MVP** (D-020) | Schema is recreated by `setup_demo`; Alembic is FUTURE |
| Deployment | simplest reliable | Vercel+Render split; K8s | **One Docker image: FastAPI serves API + built SPA** (D-008) | One process, one URL, no CORS in prod |

## 2. High-level architecture

```
                ┌────────────────────────── Browser (mobile-first SPA) ─────────────────────────┐
                │ React + TS + Tailwind · React Router · TanStack Query · Recharts · Leaflet    │
                └───────────────────────────────┬────────────────────────────────────────────────┘
                                                │ HTTPS /api/v1  (JSON, Bearer JWT)
┌───────────────────────────────────────────────▼────────────────────────────────────────────────┐
│ FastAPI application (single process, modular monolith)                                         │
│  routers ─► services ─► SQLAlchemy models ─► SQLite (PostgreSQL-compatible)                    │
│                                                                                                │
│  M1 identity  M2 listings  M3 requirements  M4 orders/market  M11 reference/seed               │
│  M5 forecasting ──► ml/ (LightGBM artifacts, feature code shared with training)                │
│  M6 matching    ──► M7 logistics(cost, geo) , M5 (context only)                                │
│  M8 routes      ──► OR-Tools + M7 geo/cost  ──► [optional] OSRM HTTP (timeout, fallback)       │
│  M9 pricing     ──► M7 cost + market_prices + pricing.yaml                                     │
│  M10 analytics  ──► SQL aggregates + M9 + M5 (read-only)                                       │
│  config/*.yaml (matching, logistics, pricing) · static SPA mount (prod)                        │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
Offline (developer machine): scripts/setup_demo.py → ml/generate_data.py → ml/train.py → seed DB
```

**Rule:** no microservices, no queues, no websockets, no background workers (D-001). Route optimization runs synchronously in the request with a time limit.

## 3. Repository layout (authoritative)

```
krishisetu/
├─ README.md   Memory.md   AGENTS.md
├─ docs/  PRD.md Research.md Architecture.md Data.md ML.md Rules.md Phases.md
│         Design.md API.md Testing.md Demo.md Execution.md
├─ backend/
│  ├─ app/
│  │  ├─ main.py                     # app factory, routers, static mount, error handlers
│  │  ├─ core/   config.py security.py deps.py errors.py geo.py dates.py
│  │  ├─ db/     base.py session.py models.py seed.py
│  │  ├─ schemas/                    # Pydantic v2 models, one file per module
│  │  └─ modules/
│  │     ├─ auth/        router.py service.py
│  │     ├─ profiles/    router.py service.py        # producers/me, buyers/me
│  │     ├─ listings/    router.py service.py
│  │     ├─ requirements/router.py service.py
│  │     ├─ orders/      router.py service.py        # incl. state machine
│  │     ├─ forecasting/ router.py service.py        # wraps ml/predict.py
│  │     ├─ matching/    router.py service.py scoring.py
│  │     ├─ logistics/   router.py service.py cost.py
│  │     ├─ routes/      router.py service.py optimizer.py distance.py
│  │     ├─ pricing/     router.py service.py
│  │     ├─ analytics/   router.py service.py
│  │     └─ reference/   router.py service.py
│  ├─ ml/  config.py generate_data.py features.py train.py evaluate.py predict.py
│  │       artifacts/  (model_point.joblib, model_q10.joblib, model_q90.joblib, model_card.json)
│  ├─ config/  matching.yaml logistics.yaml pricing.yaml generator.yaml market_hub_map.csv
│  ├─ data/    raw/ processed/ demo/   (app.db is git-ignored)
│  ├─ scripts/ setup_demo.py ingest_agmarknet.py
│  ├─ tests/   unit/ api/ ml/ integration/
│  └─ requirements.txt  .env.example
├─ frontend/
│  ├─ src/ main.tsx App.tsx routes.tsx
│  │  ├─ api/        client.ts types.ts hooks/*.ts
│  │  ├─ components/ ui/ layout/ charts/ map/ domain/
│  │  ├─ pages/      login/ market/ forecast/ analytics/ orders/ producer/ buyer/ ops/
│  │  ├─ lib/        format.ts validators.ts auth.tsx
│  │  └─ styles/     tokens.css
│  └─ vite.config.ts  tailwind.config.ts  .env.example
├─ Dockerfile   .dockerignore   .gitignore
```

## 4. Module architecture

| Module | Router prefix | Owns tables | Depends on (service-level) |
|---|---|---|---|
| auth | `/auth` | users | profiles |
| profiles | `/producers`, `/buyers` | producer_profiles, buyer_profiles | — |
| listings | `/listings` | listings | reference, pricing (soft warning) |
| requirements | `/requirements` | requirements | reference |
| orders | `/orders` | orders, order_events | listings (reservation), requirements (fill recompute) |
| forecasting | `/forecasts` | demand_history (read) | ml/predict, reference, listings (supply) |
| matching | `/matching` | — | listings, requirements, logistics.cost, pricing config, forecasting (context) |
| logistics | `/logistics` | vehicles | core/geo |
| routes | `/routes` | route_plans, shipments, shipment_stops | orders, logistics, core/geo |
| pricing | `/pricing` | market_prices (read) | logistics.cost, orders |
| analytics | `/analytics` | — (read-only) | orders, shipments, route_plans, pricing, forecasting |
| reference | `/reference`, `/system` | crops, demand_hubs | seed |

**Dependency rules.** (1) Routers contain no business logic. (2) Services receive a `Session` and return Pydantic/dict results. (3) A module never writes another module's tables except through that module's service function (`orders` calls `listings.reserve_quantity`). (4) `core/geo.py` (haversine, circuity) and `logistics/cost.py` are pure functions with no DB access. (5) `ml/` is imported only by `forecasting/service.py`.

## 5. Backend architecture

- **App factory** `create_app()` registers routers under `/api/v1`, exception handlers, CORS (dev only), optional static mount.
- **Config** via `pydantic-settings` (env) + YAML files in `backend/config/` loaded once at startup (D-019). YAML values are the disclosed assumptions.
- **Session handling**: request-scoped SQLAlchemy session dependency; commit in service layer; rollback on exception.
- **Dates**: all "today" logic uses `core/dates.today_ist()` (D-018). Listing expiry is evaluated at query time (`available_until >= today`) — no scheduler (D-021).
- **Atomic reservation**: `UPDATE listings SET quantity_available_kg = quantity_available_kg - :q WHERE id=:id AND status='ACTIVE' AND quantity_available_kg >= :q AND available_until >= :today`; zero rows updated → `409`.
- **Order state machine**: table-driven transitions in `orders/service.py`; every transition appends to `order_events`.
- **Logging**: stdlib `logging`, one line per request (method, path, status, ms) plus solver/model events. No PII in logs.

## 6. Database

- SQLite file `backend/data/app.db` (git-ignored); `PRAGMA foreign_keys=ON`; WAL mode enabled for read concurrency.
- SQLAlchemy 2.x declarative models in `db/models.py`; `Base.metadata.create_all()` at setup; **no Alembic** (D-020). Schema change ⇒ re-run `setup_demo` (seed is deterministic).
- Types chosen for portability: `Integer`, `String`, `Float`, `Numeric(10,2)`, `Date`, `DateTime(timezone=False, UTC stored)`, `JSON`, `Boolean`.
- Full schema: Data.md §6.

## 7. ML pipeline (detail in ML.md)

```
generator.yaml ─► generate_data.py ─► data/processed/demand_history.csv (SYNTHETIC)
                                   └► market_prices rows (SYNTHETIC or AGMARKNET_SNAPSHOT)
features.py ─► train.py (baselines + LightGBM point/q10/q90, time split, gate) ─► artifacts/*
predict.py  ◄─ forecasting/service.py ◄─ GET /forecasts/demand
                 (reads last 35+ days of demand_history from DB; falls back to seasonal-naive)
```
Training is offline (`python -m ml.train`), never on a request path. Artifacts are committed after the final successful run; `setup_demo` retrains only with `--retrain`.

## 8. Matching engine (detail in ML.md §9)

Deterministic: hard filters → weighted score with per-factor explanation → greedy allocation. **Not ML** (D-011). Pure functions in `matching/scoring.py` (unit-testable without DB). `service.py` loads candidates, calls `logistics.cost.estimate_trip(...)` per candidate, and assembles the response. `accept` re-runs the same computation server-side and creates orders in one transaction.

## 9. Logistics engine

`logistics/cost.py` (pure): `road_distance_km(a, b)`, `select_vehicles(quantity_kg, vehicle_types)`, `estimate_dedicated_trip(distance_km, quantity_kg)` → `{vehicle_plan, trips, cost_inr, cost_per_kg, transit_hours}`. Constants from `logistics.yaml`. This function is the single source of transport cost for marketplace cards, matching, pricing and the route **baseline**.

## 10. Route optimization (detail in ML.md §10)

`routes/optimizer.py` builds an OR-Tools `RoutingModel`: nodes = vehicle depots + pickup/drop pairs; capacity dimension; time dimension with max route duration; per-vehicle arc cost and fixed cost; disjunction penalties so infeasible orders become `unassigned`; pickup-before-drop and same-vehicle constraints. Flow: `POST /routes/optimize` → solve (≤ time limit) → store `route_plans` row (status `PROPOSED`, `result_json`) → admin reviews → `approve` creates `shipments`/`shipment_stops` and links `orders.shipment_id` (D-016). Distances from `routes/distance.py` (haversine or OSRM with cache + fallback).

If OR-Tools errors or times out without a solution, a **greedy capacity-aware insertion fallback** produces a plan flagged `method="GREEDY_FALLBACK"`.

## 11. Authentication and authorization

- Email + password; password hashed with `bcrypt` (direct package, not passlib); JWT HS256 via `PyJWT`, claims: `sub` (user id), `role`, `exp` (default 720 min for demo convenience — config).
- Roles: `PRODUCER`, `BUYER`, `ADMIN`. `ADMIN` is the **operator** and may additionally perform order transitions on behalf of parties (operator override, recorded in `order_events.actor_role`) (D-017).
- `demo-login` exists only when `DEMO_MODE=true`.

| Capability | PRODUCER | BUYER | ADMIN |
|---|---|---|---|
| Create/edit own listing | ✔ | ✘ | ✔ (read) |
| Browse marketplace | ✔ | ✔ | ✔ |
| Create/edit own requirement | ✘ | ✔ | read |
| Run match candidates | ✘ | own requirement | any |
| Accept allocation | ✘ | own requirement | ✘ |
| Direct order | ✘ | ✔ | ✘ |
| Confirm/reject order | own orders | cancel own PLACED | any (override) |
| Forecasts, pricing, analytics (read) | ✔ | ✔ | ✔ |
| Route optimize/approve, shipment transitions | ✘ | ✘ | ✔ |
| Seed reset | ✘ | ✘ | ✔ (DEMO_MODE) |

Object-level checks are mandatory (a producer cannot touch another producer's listing).

## 12. API flow (main path)

```
POST /listings ─► GET /forecasts/hubs, /forecasts/demand, /pricing/benchmark (beside form)
GET /matching/requirements/{id}/candidates ─► POST /matching/accept ─► orders PLACED
POST /orders/{id}/transition CONFIRMED
POST /routes/optimize ─► GET /routes/plans/{id} ─► POST /routes/plans/{id}/approve
POST /routes/shipments/{id}/transition (DISPATCHED, DELIVERED)
GET /pricing/breakdown?order_id ─► GET /analytics/overview, /analytics/supply-demand
```

## 13. Error handling

Uniform envelope (all non-2xx):
```json
{ "error": { "code": "INSUFFICIENT_QUANTITY", "message": "Only 500 kg available.", "details": [{"field":"quantity_kg","issue":"max 500"}] } }
```
Codes: `VALIDATION_ERROR`(422), `UNAUTHENTICATED`(401), `FORBIDDEN`(403), `NOT_FOUND`(404), `INSUFFICIENT_QUANTITY`(409), `LISTING_UNAVAILABLE`(409), `INVALID_TRANSITION`(409), `STALE_ALLOCATION`(409), `STALE_PLAN`(409), `NO_VEHICLE_AVAILABLE`(409), `NO_ELIGIBLE_ORDERS`(422), `INSUFFICIENT_HISTORY`(422), `DEMO_DISABLED`(404), `DATABASE_UNAVAILABLE`(503), `OPTIMIZATION_FAILED`(500), `INTERNAL_ERROR`(500). Pydantic validation errors are mapped into the envelope. External-service failures (OSRM, tiles) never surface as errors — they degrade with a flag in the response (`distance_source`).

## 14. Security

Hashed passwords; JWT expiry; per-object authorization; Pydantic validation on every input; ORM parameterization (no raw string SQL); CORS restricted to configured origins in dev and disabled in prod (same origin); secrets only via env; `.env` git-ignored; no PII beyond business name/contact; demo credentials exist only in seeded demo DB and are disabled when `DEMO_MODE=false`; frontend stores the token in memory + `sessionStorage` (no cookies, so CSRF is not applicable); rate limiting is FUTURE. Security checks list: Testing.md §12.

## 15. Deployment

- **Primary demo:** developer laptop, `uvicorn` + built SPA or Vite dev server.
- **Backup:** one Docker image (multi-stage: Node build → Python runtime with `libgomp1` for LightGBM), run `python -m scripts.setup_demo --no-retrain` at container start, then `uvicorn`. Any Docker-capable PaaS works; free tiers may sleep and lose SQLite on restart — acceptable because the seed is deterministic (Risk R-11).
- **Fallback:** recorded screen capture + screenshots prepared in Phase 12.

## 16. Local development

Two terminals: `uvicorn app.main:app --reload --port 8000` (from `backend/`) and `npm run dev` (from `frontend/`, Vite proxies `/api` → `http://localhost:8000`). Commands are in README.md.

## 17. Environment variables

Backend `.env.example`:

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `dev` | `dev` / `prod` |
| `DEMO_MODE` | `true` | enables demo-login and reset |
| `SECRET_KEY` | (required, no default in prod) | JWT signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `720` | token lifetime |
| `DATABASE_URL` | `sqlite:///./data/app.db` | DB |
| `CORS_ORIGINS` | `http://localhost:5173` | dev only |
| `APP_TIMEZONE` | `Asia/Kolkata` | date logic |
| `ROUTING_PROVIDER` | `haversine` | `haversine` / `osrm` |
| `OSRM_BASE_URL` | `https://router.project-osrm.org` | optional |
| `OSRM_TIMEOUT_S` | `5` | optional |
| `ROAD_CIRCUITY_FACTOR` | `1.35` | overrides yaml |
| `SOLVER_TIME_LIMIT_S` | `5` | default optimizer limit (max 30) |
| `MODEL_DIR` | `ml/artifacts` | model artifacts |
| `PRICE_SOURCE` | `synthetic` | `synthetic` / `agmarknet_snapshot` |
| `AGMARKNET_SNAPSHOT_PATH` | `data/raw/agmarknet_snapshot.csv` | only if ingesting |
| `DATA_GOV_IN_API_KEY` | (empty) | only for the offline download helper |
| `LOG_LEVEL` | `INFO` | logging |

Frontend `.env.example`: `VITE_API_BASE_URL=/api/v1`, `VITE_DEMO_MODE=true`, `VITE_MAP_TILE_URL=https://tile.openstreetmap.org/{z}/{x}/{y}.png`, `VITE_MAP_ATTRIBUTION=© OpenStreetMap contributors`.

## 18. External services

| Service | Required? | Failure behaviour |
|---|---|---|
| OSM tile server | No (visual) | Map shows schematic SVG route list |
| OSRM demo server | No | Fallback to haversine; `distance_source="ESTIMATED_HAVERSINE"` |
| data.gov.in | No (offline helper only) | Synthetic prices used |

## 19. Dependencies (pin exact versions in lockfiles at Phase 0 after a successful install; do not upgrade mid-build)

Backend: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `pydantic`, `pydantic-settings`, `pyjwt`, `bcrypt`, `pyyaml`, `numpy`, `pandas`, `scikit-learn`, `lightgbm`, `joblib`, `ortools`, `httpx`, `pytest`, `pytest-cov`, `ruff`.
Frontend: `react`, `react-dom`, `react-router-dom`, `@tanstack/react-query`, `react-hook-form`, `zod`, `recharts`, `leaflet`, `react-leaflet`, `lucide-react`, `clsx`, `tailwindcss`, `vite`, `typescript`, `vitest`, `@testing-library/react`. **Adding any dependency not in this list requires updating this section first.**

## 20. Future scalability (FUTURE)

Postgres + Alembic; async job queue for optimization; OSRM self-hosted container; model retraining job and forecast-vs-actual logging; object storage for documents; rate limiting; multi-region hubs; event log → analytics warehouse. None is required for the hackathon.

## 21. Design decisions recorded here

D-001 modular monolith · D-002 React/Vite/TS/Tailwind · D-003 FastAPI · D-004 SQLite default, Postgres-compatible, Supabase rejected · D-007 LightGBM · D-008 single-image deploy · D-009 JWT + roles · D-013 OR-Tools · D-014 haversine default/OSRM optional · D-015 no `demand_forecasts` table (inference on demand, in-memory cache) · D-016 route plan PROPOSED→APPROVED · D-017 operator override on orders · D-018 IST · D-019 YAML config · D-020 no Alembic · D-021 expiry at query time · D-023 Leaflet/OSM.
