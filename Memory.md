# Memory.md — FasalSetu permanent project state

Update rules: Execution.md §8. Never record results that were not produced by an executed command. Last updated: 2026-10-01 (Phase 3 completion).

## 1. Project identity

| Field | Value |
|---|---|
| Project | FasalSetu — AI-assisted direct agricultural supply-chain coordination platform |
| Hackathon | Smart India Hackathon 2026 — **SIH26033** "Multiple intermediaries reduce farmers earnings and increase consumer prices" |
| Creator / org | Sarim Moin — Ministry of Consumer Affairs, Food & Public Distribution; dept: Ministry of Education's Innovation Cell (MIC); bucket: Agriculture, FoodTech & Rural Development; category: Software |
| Sole developer / owner | Shubham Kumar (no parallel coding) |
| Core loop | PREDICT → MATCH → MOVE → SELL → ANALYSE |
| Demo region | Delhi-NCR belt, 5 crops (Tomato, Onion, Potato, Cauliflower, Green Chilli), 5 demand hubs |

## 2. Current status

| Item | State |
|---|---|
| Documentation package (14 files + AGENTS.md) | **Complete** (moved to `docs/` with README, Memory, AGENTS at root) |
| Source code | **Phase 4 complete** (Buyer Module + Buyer Profile + Requirement Lifecycle + Landed Price Guidance + Seed R1-R8 + Buyer UI) |
| Current implementation phase | **Phase 4 complete — next: Phase 5** (Unified Marketplace + Discovery) |
| Tests executed | **63 backend tests passed** (`pytest -v`), **17 frontend tests passed** (`vitest`), **0 lint errors** (`ruff check .`), **0 build errors** (`npm run build`) |
| Measured metrics | **Data & Model verified**: 8 requirements seeded (`R1`–`R8`); buyer profile retrieval and bounded update verified; object-level authorization verified (403 on cross-buyer & producer access); Rule D-021 dynamic expiry on GET/PATCH verified (409 on expired mutation); educational landed-cost guidance verified |



## 3. Completed documentation

PRD.md · Research.md · Architecture.md · Data.md · ML.md · Rules.md · Phases.md · Design.md · API.md · Testing.md · Demo.md · Execution.md · Memory.md · README.md (docs live in `docs/`, README.md and Memory.md at repo root).

## 4. Architecture decisions (do not re-debate; change only via Rules AI-6)

| ID | Decision |
|---|---|
| D-001 | Modular monolith; no microservices, queues, websockets, workers |
| D-002 | Frontend: React 18 + Vite + TypeScript + Tailwind + React Router + TanStack Query + Recharts + Leaflet |
| D-003 | Backend: FastAPI (Python 3.11), SQLAlchemy 2.x, Pydantic v2 |
| D-004 | DB: SQLite default, schema kept PostgreSQL-compatible; **Supabase rejected for MVP** |
| D-007 | Forecast model family: LightGBM (XGBoost not used; RF only as optional reference) |
| D-008 | Deployment: one Docker image serving API + built SPA; laptop is the primary demo machine |
| D-009 | Auth: email+password, bcrypt, JWT HS256; roles PRODUCER/BUYER/ADMIN |
| D-013 | Route optimization: OR-Tools capacitated pickup-and-delivery VRP (not OSRM `trip`) |
| D-014 | Distances: haversine × circuity 1.35 by default; OSRM optional with fallback |
| D-015 | **No `demand_forecasts` table**; forecasts computed on demand with in-memory cache |
| D-016 | Route plans are PROPOSED → APPROVED/DISCARDED; shipments created only on approval |
| D-017 | ADMIN (operator) may perform order transitions on behalf of parties (logged) |
| D-018 | All date logic in Asia/Kolkata via `core/dates.today_ist()` |
| D-019 | Assumptions live in `backend/config/*.yaml` |
| D-020 | No Alembic in MVP; schema recreated by `setup_demo` |
| D-021 | Listing expiry evaluated at query time; no scheduler |
| D-022 | Route cost allocated to orders by kg-km share |
| D-023 | Maps: Leaflet + OSM tiles with attribution; schematic fallback |
| D-024 | LightGBM deployed only if it beats both baselines (validation ×0.95 and test); else fallback is honestly shown |
| D-025 | Route savings are measured only against a **modelled** baseline (dedicated round trips) |
| D-026 | Each listing is attributed to its nearest hub for supply-vs-demand |
| D-027 | Pure geo/cost utilities are built in Phase 1 (needed by marketplace and matching) |

## 5. Model decisions

Primary ML problem: 7-day demand forecast per hub × crop; target = daily bulk demand kg; features use lags ≥ 7 only (single model for all horizons); LightGBM point + q10 + q90 (80% interval); baselines = seasonal naive (lag 7) and trailing mean; chronological split (train → T−84, validation 56 d, test 28 d); metrics MAE, RMSE, WAPE (primary %), MAPE (y≥10), bias, interval coverage; fallback = seasonal naive. Matching = deterministic (weights price .40 / distance .20 / freshness .20 / fill .20). Pricing and logistics are closed-form. **No LSTM/Transformer, no ML matching.**

## 6. Data decisions

| ID | Decision |
|---|---|
| D-005 | Individual households are not direct users in MVP; consumers served via `CONSUMER_GROUP` buyers |
| D-006 | No payments/escrow/invoicing; settlement outside the platform |
| D-010 | Demand history is **synthetic** (documented generator, seed 42); always disclosed |
| D-011 | Matching is deterministic, not ML |
| D-012 | Price benchmark is synthetic by default; real Agmarknet snapshot ingestion is optional (NICE); farm-gate and retail prices are modelled, not sourced |

Seed spec (Data.md §12) is authoritative: 5 crops, 5 hubs, 6 producers, 5 buyers, 5 vehicles, 14 listings, 8 requirements, 6 confirmed + 4 delivered orders; live demo listing L15 created on stage.

## 7. Important assumptions (see PRD §22, Research §10)

A-01…A-12. Key ones: no public buyer-level demand data (A-04); Agmarknet prices per quintal (A-05, verify); vehicle rates/speeds/margins/shelf-life are illustrative config (A-06); mixed loads allowed (A-07); the SIH26033 text in the owner's brief matches the portal (A-10).

## 8. Limitations (current by design)

Synthetic demand and prices; no payments; no live tracking; estimated distances; one region and five crops; greedy per-requirement matching; SQLite single-writer; modelled baseline/scenario depend on assumptions; competitors (Ninjacart, eNAM, DeHaat) already offer parts of this — no uniqueness claim.

## 9. Known bugs

None (no code exists).

## 10. Important files

`docs/PRD.md` (scope, FRs) · `docs/Research.md` (evidence tags, sources) · `docs/Architecture.md` (stack, modules, repo layout) · `docs/Data.md` (schema, seed) · `docs/ML.md` (formulas, algorithms) · `docs/API.md` (42 endpoints) · `docs/Design.md` (screens) · `docs/Testing.md` (AC IDs, execution log) · `docs/Demo.md` (script, verification log) · `docs/Phases.md` (roadmap + feasibility audit) · `docs/Rules.md` · `docs/Execution.md` · `AGENTS.md` (to create in Phase 0).

## 11. Completed / incomplete features

Completed:
- Phase 0: System skeleton, initial setup, health endpoint, directory layout.
- Phase 1: Database schema (15 models), seed logic (12 users, 5 crops, 5 hubs, 5 vehicles), auth service & endpoints (/login, /demo-login, /me, /register), reference endpoints (/reference), logistics cost calculator, geo utilities, custom errors, frontend auth context, LoginPage with 6 demo personas, AppShell with role-based navigation and DEMO DATA badge.
- Phase 2: Synthetic demand generator (`generate_data.py`), benchmark price generator (`DEMO-PRICE-ANCHOR`), Agmarknet snapshot ingestion script (`ingest_agmarknet.py`), seed integration, generator configuration (`generator.yaml`, `market_hub_map.csv`), deterministic dropout, seed reproducibility, snapshot preservation guarantees.
- Phase 3: Producer / Farmer / FPO module: `ProducerProfileOut`/`ProducerProfileUpdate` schemas, `GET/PATCH /producers/me`, `POST/GET/PATCH /listings`, `GET /listings/{id}` with `ListingDetailResponse`, nearest hub market price lookup (real `AGMARKNET_SNAPSHOT` prioritized over `SYNTHETIC_DEMO`), `PRICE_FAR_ABOVE_BENCHMARK` warning, object-level authorization (`AC-SEC-03`, `AC-LST-06`), query-time dynamic expiration (Rule D-021), deterministic seeding of listings `L1`–`L14`, frontend `ListingsPage`, `NewListingPage` with live benchmark hint & `DemandPanelPlaceholder`, `EditListingModal`, and `ProducerProfilePage`.

Incomplete — all PLANNED: every item in PRD §14 per priority in Phases.md §15 (Phases 4 through 13).

## 12. Future work

PRD §18. Highlights: real demand data, Agmarknet/eNAM feeds, payments, individual D2C, global matching optimization, cold-chain rules, live tracking, Postgres + Alembic.

## 13. Next action

1. Proceed to **Phase 4** (Phases.md §6): Buyer Module (`GET/PATCH /buyers/me`, requirements `POST/GET list/GET one/PATCH`, cancellation, seed requirements R1–R8, frontend Requirements list and New Requirement form).



## 14. Decisions that must NOT be repeated / re-opened

- Do not add payments, chat, ratings, social features, blockchain, microservices, queues or websockets.
- Do not use LSTM/Transformer or ML for matching.
- Do not use Supabase/Postgres for the MVP (config switch only).
- Do not claim measured farmer income, measured savings, real-time data, live tracking or real model accuracy.
- Do not claim uniqueness of marketplace/forecasting/route optimization.
- Do not add dependencies outside Architecture §19 without updating it first.
- Do not create a `demand_forecasts` table (D-015).
- Do not duplicate distance/cost formulas (Rules C-14).
- Do not let individual households become a user type in MVP (D-005).

## 15. Changes to architecture / scope (log)

Corrections made while drafting the package (resolved before the files were finalized; documents already agree):

| ID | Change | Affected docs |
|---|---|---|
| C-001 | Removed a planned `demand_forecasts` table; forecasts computed on demand (D-015) | Architecture, Data, API |
| C-002 | Route optimization split into PROPOSED plan → approve/discard (D-016); added `route_plans` table and plan endpoints | Architecture, Data, API, Design, Phases |
| C-003 | ADMIN operator override on order transitions to keep the live demo within 2 persona switches (D-017) | Architecture, API, Demo, Rules |
| C-004 | API groups beyond the brief's list: `reference`, `system`, `pricing` (price transparency is a core SIH-5/6 feature) | Architecture, API |
| C-005 | Added `STALE_PLAN` (409) error code | API, Architecture (updated in consistency audit) |
| C-006 | Pure geo/cost utilities moved from Phase 7 to Phase 1 (D-027) | Phases |
| C-007 | Seed ask prices set inside the modelled fair price band (not below the farmer's mandi-equivalent) so the demo is coherent | Data, Demo |
| C-008 | Dropped festival/holiday features and the `demand_forecasts` table to fit scope | ML, Data |

Scope changes after documentation: none yet.

## 16. Documentation consistency audit (executed 2026-10-01 by script over the 14 files)

| Check | Result |
|---|---|
| Acceptance-criteria IDs referenced in Phases/PRD/Demo exist in Testing.md (85 defined) | PASS — 0 undefined references |
| Data.md tables (15) all appear in Architecture.md and API.md | PASS |
| Decision IDs (D-xxx) used anywhere are defined in §4/§6 of this file | PASS — 0 missing |
| API.md endpoint count equals the index (42) | PASS |
| `demand_forecasts` appears only as a documented removal (D-015) | PASS |
| Fixes applied during audit | C-005 (`STALE_PLAN` added to Architecture error codes); Phases Phase 5 acceptance widened to AC-FC-01…09 |
Semantic cross-checks (PRD↔Research, Design↔API routes/roles, Demo↔seed data, Execution↔Phases) were done by manual reading, not script. Re-run the script-style checks whenever any doc changes.
