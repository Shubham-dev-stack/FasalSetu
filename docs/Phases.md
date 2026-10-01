# Phases — FasalSetu build roadmap

Sequential, single developer (Shubham Kumar). No parallel phases. Each phase = backend slice + frontend slice + tests + doc/Memory update. Effort figures are **planning estimates for AI-assisted work, not measurements**. Acceptance-criteria IDs (AC-…) are defined in Testing.md.

**Structure note (recorded in Memory.md):** pure distance/cost functions (`core/geo.py`, `logistics/cost.py`) were built in Phase 1 because downstream modules need landed-price estimates. Phase 2 establishes the synthetic demand & price generator and Agmarknet snapshot ingestion, providing forecasting-ready data and price benchmarks before listing/marketplace/ML phases.

## 1. Overview

| Phase | Name | Effort (h) | Day |
|---|---|---|---|
| 0 | Repository + project setup | 1.0 | 1 |
| 1 | Foundation + database + auth + pure logistics utils | 3.0 | 1 |
| 2 | Synthetic demand & price generator + Agmarknet snapshot ingestion | 1.5 | 1 |
| 3 | Farmer/FPO module (profile, listings) | 2.0 | 1 |
| 4 | Buyer module (profile, requirements) | 1.5 | 1 |
| 5 | Marketplace + orders | 2.5 | 1 |
| 6 | Demand forecasting (model, API, UI) | 3.5 | 2 |
| 7 | Smart matching | 2.5 | 2 |
| 8 | Logistics (estimate API, vehicles, UI) | 1.0 | 2 |
| 9 | Route optimization | 3.5 | 2 |
| 10 | Price transparency | 1.5 | 3 |
| 11 | Analytics dashboard | 2.0 | 3 |
| 12 | Integration | 2.0 | 3 |
| 13 | Testing + polish + demo readiness | 4.0 | 3 |
| | **Total planned** | **32.0** | |

Timeboxing rule: if a phase reaches 1.5× its estimate, stop and apply the cut list (§15).

---

## 2. PHASE 0 — Repository + project setup (1.0 h)

- **Objective:** runnable empty skeleton for backend and frontend, repo hygiene, agent context files.
- **Dependencies:** this documentation package.
- **Deliverables:** git repo; folder layout from Architecture.md §3; `AGENTS.md`, `Memory.md`, `docs/*`; backend FastAPI app with `GET /api/v1/health`; frontend Vite+React+TS+Tailwind "hello" page calling health via proxy; `.gitignore`, `.env.example` (both), `requirements.txt`, `package.json`; pinned versions after successful install; `pytest` runs one health test.
- **Files/modules:** `backend/app/main.py`, `backend/app/core/config.py`, `backend/tests/api/test_health.py`, `frontend/src/main.tsx`, `frontend/vite.config.ts`, `frontend/src/api/client.ts`.
- **Acceptance:** AC-SYS-01; backend `pytest -q` green; `npm run build` succeeds; both dev servers start; wheel availability for `ortools` and `lightgbm` confirmed on the dev OS.
- **Test cases:** health returns `{status:"ok"}`; frontend displays backend status.
- **Exit criteria:** commit on `main`, tag `phase-00-done`, Memory.md updated.
- **Risks:** wheel/Python-version mismatch for OR-Tools/LightGBM → use Python 3.11; if wheels fail, resolve now, not on Day 2.

## 3. PHASE 1 — Foundation + database + auth + pure logistics utils (3.0 h)

- **Objective:** schema, config loading, auth/roles, error envelope, seed skeleton, pure geo/cost functions.
- **Dependencies:** Phase 0.
- **Deliverables:** all 15 tables (Data.md §6) in `db/models.py`; session/dependency; YAML config loader; error handlers (envelope, Architecture.md §13); `auth` (login, me, demo-login, register stub → S); role guards; object-ownership helpers; `db/seed.py` for reference data (crops, hubs), users/profiles, vehicles; `reference` endpoint; `core/geo.py` (haversine, circuity); `logistics/cost.py` (`road_distance_km`, `select_vehicles`, `estimate_dedicated_trip`); `core/dates.py`; frontend: login page with demo personas, auth context, protected routes, app shell (layout, nav by role, DEMO badge).
- **Files:** `backend/app/{core,db,schemas,modules/auth,modules/reference,modules/logistics/cost.py}`, `backend/config/*.yaml`, `backend/scripts/setup_demo.py` (DB + reference seed), `frontend/src/{lib/auth.tsx,pages/login,components/layout}`.
- **Acceptance:** AC-AUTH-01…04; AC-SYS-02, AC-SYS-03; AC-DATA-01 (for seeded entities so far), AC-DATA-03, AC-DATA-04; AC-LOG-01…04 (pure-function level); AC-SEC-01…03.
- **Test cases:** login OK/bad password; role guard 403; demo-login disabled when `DEMO_MODE=false`; haversine known pair; vehicle selection table; DB CHECK constraints reject bad rows; error envelope shape.
- **Exit criteria:** persona login works in browser; `setup_demo` recreates DB deterministically; tag `phase-01-done`.
- **Risks:** over-building auth (keep to spec); SQLite FK pragma forgotten.

## 4. PHASE 2 — Synthetic demand & price generator + Agmarknet snapshot ingestion (1.5 h)

- **Objective:** establish reliable, reproducible, forecasting-ready demand and market-price data.
- **Dependencies:** Phase 1.
- **Deliverables:** `backend/ml/generate_data.py` (+ `generator.yaml`), `backend/scripts/ingest_agmarknet.py`, `backend/config/market_hub_map.csv`; complete pre-dropout panel (18,250 rows) + deterministic post-dropout dataset (~1% dropout); seed `demand_history` and `market_prices` (`source=SYNTHETIC_DEMO`); Agmarknet snapshot ingestion into `market_prices` (`source=AGMARKNET_SNAPSHOT`, `is_synthetic=false`); metadata files (`demand_history.meta.json`, `prices.meta.json`).
- **Files:** `backend/ml/generate_data.py`, `backend/scripts/ingest_agmarknet.py`, `backend/config/market_hub_map.csv`, `backend/data/raw/sample_agmarknet_snapshot.csv`, update `backend/app/db/seed.py` and `backend/scripts/setup_demo.py`.
- **Acceptance:** AC-DATA-01, AC-DATA-03; AC-GEN-01, AC-GEN-02; AC-PRC-02.
- **Test cases:** pre-dropout panel has exactly 18,250 rows; post-dropout has ~1% dropout with all 5 hubs and 5 crops represented; seed reproducibility (counts, values, ordering); price anchoring (last 30 days within ±10% base); Agmarknet unit conversion (÷100); multi-variety aggregation; synthetic reseeding preserves real `AGMARKNET_SNAPSHOT` rows.
- **Exit:** generator and ingestion scripts run cleanly; `demand_history` and `market_prices` seeded deterministically; tag `phase-02-done`.
- **Risks:** accidental deletion of real snapshot data (mitigation: filter by `is_synthetic=True` on synthetic reseeding).

## 5. PHASE 3 — Farmer/FPO module (2.0 h)

- **Objective:** producers can view profile and create/manage listings.
- **Dependencies:** Phases 1, 2 (market prices needed for benchmark validation).
- **Deliverables:** `GET/PATCH /producers/me`; listings `POST/GET(list, mine filter)/GET one/PATCH`; validation per Data.md §8; ask price warning vs Phase 2 benchmark (`AC-LST-03`); expiry evaluated at query time; seed listings L1–L14; frontend: producer listings page, **new-listing form** (demand-intelligence side panel is a placeholder slot until Phase 6), listing status chips, empty/loading/error states.
- **Files:** `modules/{profiles,listings}`, `schemas/listing.py`, `frontend/src/pages/producer/*`, `components/domain/ListingCard.tsx`.
- **Acceptance:** AC-LST-01…07; AC-UI-02 (producer pages).
- **Test cases:** invalid quantity, invalid price, min order > quantity, dates inverted, past `available_until`, foreign listing edit (403), expired listing hidden, withdraw.
- **Exit:** create listing in browser persists; tag `phase-03-done`.
- **Risks:** form validation drift between zod and Pydantic → mirror Data.md §8 exactly.

## 6. PHASE 4 — Buyer module (1.5 h)

- **Objective:** buyers manage profile and requirements.
- **Dependencies:** Phase 1.
- **Deliverables:** `GET/PATCH /buyers/me`; requirements `POST/GET list/GET one/PATCH` (cancel = PATCH status); seed R1–R8; frontend: requirements list, new-requirement form (max **landed** price explained), status chips.
- **Files:** `modules/requirements`, `schemas/requirement.py`, `frontend/src/pages/buyer/*`.
- **Acceptance:** AC-REQ-01…04; AC-UI-02 (buyer pages).
- **Test cases:** past `needed_by` (422), quantity bounds, cancel, cross-buyer access 403.
- **Exit:** requirement created and visible; tag `phase-04-done`.
- **Risks:** confusing "max landed price" — copy text in Design.md.

## 7. PHASE 5 — Marketplace + orders (2.5 h)

- **Objective:** browse listings with landed-price estimate; order lifecycle with atomic reservation.
- **Dependencies:** Phases 3, 4; Phase 1 cost utils.
- **Deliverables:** `GET /listings` filters (crop, grade, state, price range, freshness, `buyer_lat/lng` optional for landed estimate); `orders` service (reserve, release, transitions, event log, requirement fulfilment recompute); `POST /orders`, `GET /orders`, `GET /orders/{id}`, `POST /orders/{id}/transition`; seed O1–O6, H1–H4 via the service; frontend: market page (cards + filters), order list, order detail (timeline; price panel placeholder), confirm/reject/cancel buttons; listing detail (S) and direct order button (S).
- **Files:** `modules/orders`, extend `modules/listings`, `frontend/src/pages/{market,orders}`, `components/domain/{OrderTimeline,StatusChip}.tsx`.
- **Acceptance:** AC-MKT-01…03; AC-ORD-01…07.
- **Test cases:** oversell blocked; concurrent reservation (two sequential requests exhausting quantity); min-order; unavailable listing; invalid transitions; cancel restores quantity; operator override recorded.
- **Exit:** a buyer can order and a producer can confirm in the browser; tag `phase-05-done`. **End of Day 1.**
- **Risks:** race conditions (use single conditional UPDATE); status/quantity drift (derive fulfilment from orders).

## 8. PHASE 6 — Demand forecasting (3.5 h)

- **Objective:** train LightGBM demand model from Phase 2 data → API → UI beside the listing form and in a forecast dashboard.
- **Dependencies:** Phase 2 (for `demand_history`), Phase 3 (for listing form DemandPanel).
- **Deliverables:** `ml/features.py`, `ml/train.py` (baselines, LightGBM point/q10/q90, time split, gate, RF reference optional), `ml/evaluate.py`, `ml/predict.py`, artifacts + `model_card.json`; `forecasting` module: `GET /forecasts/demand`, `/forecasts/hubs`, `/forecasts/model-info`; frontend: forecast chart component (history + forecast + 80% band), hub ranking list, **demand-intelligence panel in the listing form**, forecast page, model-info drawer with synthetic disclosure banner.
- **Files:** `ml/*`, `modules/forecasting`, `frontend/src/components/charts/ForecastChart.tsx`, `pages/forecast`, `components/domain/DemandPanel.tsx`.
- **Acceptance:** AC-FC-01…09; AC-DATA-02.
- **Test cases:** interval ordering; fallback when artifacts removed; invalid hub/crop; leakage test; insufficient history; metrics file flagged synthetic; hub-ranking status thresholds.
- **Exit:** panel updates when crop/quantity changes; `model_card.json` exists with real measured metrics; tag `phase-06-done`.
- **Risks:** time sink in tuning (cap: no tuning beyond the `num_leaves` grid); gate fails → ship fallback honestly; LightGBM native lib (`libgomp`) in Docker.

## 9. PHASE 7 — Smart matching (2.5 h)

- **Objective:** ranked, explained candidates with partial/multi-source allocation and accept.
- **Dependencies:** Phases 4, 5, 6 (context), Phase 1 cost utils.
- **Deliverables:** `matching/scoring.py` (pure), `matching/service.py`, `GET /matching/requirements/{id}/candidates`, `POST /matching/accept`, `GET /matching/listings/{id}/opportunities` (S); `matching.yaml`; frontend match screen (candidates table/cards with factor bars, allocation summary, shortfall banner, near-misses, accept), producer opportunities section (S).
- **Files:** `modules/matching/*`, `frontend/src/pages/buyer/MatchPage.tsx`, `components/domain/{CandidateCard,ScoreBreakdown}.tsx`.
- **Acceptance:** AC-MAT-01…08.
- **Test cases:** filter each rule (grade, budget, distance, freshness, availability); partial; none; min-order skip; multi-source sum ≤ Q; accept revalidation and atomicity; stale allocation 409; R3 partial and R8 none on seed.
- **Exit:** accept creates PLACED orders; tag `phase-07-done`.
- **Risks:** scoring ties (deterministic tie-break); unit errors in landed price.

## 10. PHASE 8 — Logistics (1.0 h)

- **Objective:** expose logistics estimate and fleet, show cost on UI.
- **Dependencies:** Phase 1 utils, Phase 5.
- **Deliverables:** `POST /logistics/estimate`, `GET /logistics/vehicles`; `NO_VEHICLE_AVAILABLE` handling; frontend: logistics estimate card on listing detail/market card and vehicles table on ops page.
- **Files:** `modules/logistics/{router,service}.py`, `frontend/src/components/domain/LogisticsEstimate.tsx`.
- **Acceptance:** AC-LOG-01…05.
- **Exit:** estimates consistent between marketplace, matching and endpoint (same function); tag `phase-08-done`.
- **Risks:** duplicated formulas (Rules C-14).

## 11. PHASE 9 — Route optimization (3.5 h)

- **Objective:** consolidated, capacity-aware routes with baseline comparison and approve/discard.
- **Dependencies:** Phases 5, 8.
- **Deliverables:** `routes/distance.py` (haversine matrix; OSRM optional behind flag), `routes/optimizer.py` (OR-Tools model per ML.md §10 + greedy fallback), `routes/service.py`; endpoints `POST /routes/optimize`, `GET /routes/plans`, `GET /routes/plans/{id}`, `POST /routes/plans/{id}/approve`, `POST /routes/plans/{id}/discard`, `GET /routes/shipments/{id}`, `POST /routes/shipments/{id}/transition`; frontend: ops logistics page (orders pool with checkboxes, vehicles, Optimize), plan page (Leaflet map, per-vehicle stop list, KPIs: km, ₹, utilisation, savings vs baseline, unassigned), approve/discard, dispatch/deliver (S).
- **Files:** `modules/routes/*`, `frontend/src/pages/ops/*`, `components/map/RouteMap.tsx`.
- **Acceptance:** AC-RTE-01…10.
- **Test cases:** capacity at every stop; pickup precedes drop on same vehicle; oversize order chunking; insufficient fleet → unassigned with reason; no eligible orders 422; solver time-limit respected; fallback path; OSRM failure fallback (if implemented); approve links orders; discard leaves orders untouched; seed scenario optimized ≤ baseline (or reported honestly).
- **Exit:** seeded pool (O1–O6) produces a plan end-to-end; tag `phase-09-done`. **End of Day 2.**
- **Risks:** **highest technical risk** — timebox formulation to 2 h, then ship greedy fallback + plan UI; OR-Tools API mismatch (AI-10); map tiles failing (schematic fallback).

## 12. PHASE 10 — Price transparency (1.5 h)

- **Objective:** benchmark, fair band, per-order waterfall, scenario disclosure.
- **Dependencies:** Phases 2 (market prices), 5 (orders), 9 (allocated cost).
- **Deliverables:** `GET /pricing/breakdown`, `GET /pricing/benchmark`; `pricing.yaml`; frontend: waterfall chart on order detail, scenario assumptions drawer, fair price band on listing form and listing card, source badge.
- **Files:** `modules/pricing/*`, `frontend/src/components/charts/PriceWaterfall.tsx`, `components/domain/PriceBand.tsx`.
- **Acceptance:** AC-PRC-01…04.
- **Exit:** every order detail shows a waterfall with source labels; tag `phase-10-done`.
- **Risks:** wording drifting into real-saving claims (Rules §5).

## 13. PHASE 11 — Analytics dashboard (2.0 h)

- **Objective:** KPIs, supply-vs-demand, modelled price gap, model card.
- **Dependencies:** Phases 6, 9, 10.
- **Deliverables:** `GET /analytics/overview`, `GET /analytics/supply-demand`; frontend analytics page: KPI cards, 14-day orders/volume chart, supply-demand table with status chips, price-gap cards, route-savings card, model-card link; demo-data banner.
- **Files:** `modules/analytics/*`, `frontend/src/pages/analytics/*`.
- **Acceptance:** AC-ANL-01…03.
- **Exit:** KPIs change after accept/confirm/approve; tag `phase-11-done`.
- **Risks:** metric definitions ambiguity → use Data.md §7 definitions.

## 14. PHASE 12 — Integration (2.0 h)

- **Objective:** make the full demo path work from a fresh reset with correct cross-screen links.
- **Dependencies:** Phases 1–11.
- **Deliverables:** `POST /system/reset-demo` (ADMIN, DEMO_MODE); persona switcher in top bar; deep links between screens (listing → forecast → match → order → waterfall → analytics); consistent formatting helpers; fix cross-module bugs; `Dockerfile` and static mount (S); run Demo.md script end-to-end.
- **Acceptance:** AC-INT-01…03; AC-DATA-01, AC-DATA-03 on the full seed.
- **Exit:** Demo.md 3-minute path completes twice in a row from reset; tag `phase-12-done`.
- **Risks:** hidden coupling; date-relative seed edge cases.

## 15. PHASE 13 — Testing + polish + demo readiness (4.0 h)

- **Objective:** close test gaps, responsive/accessibility pass, demo assets, freeze.
- **Dependencies:** Phase 12.
- **Deliverables:** execute Testing.md full matrix and fill the execution log; fix defects; responsive checks at 360/768/1280; loading/empty/error states verified; accessibility pass (focus, labels, contrast check); README final; screenshots + screen recording fallback; `demo-ready` tag; Memory.md final state.
- **Acceptance:** AC-UI-01…05; AC-SEC-04…06; NFR spot checks; all MUST ACs executed.
- **Exit:** code freeze at T−4h before presenting; tag `demo-ready`.
- **Risks:** polishing instead of verifying; last-minute dependency changes (forbidden after freeze).

---

## 16. 3-Day Feasibility Audit (authoritative scope classification)

| Feature | Class | Notes |
|---|---|---|
| Login, roles, demo personas (FR-01, 03, 04) | **MUST** | Phase 1 |
| Synthetic demand & price generator + Agmarknet ingest (FR-93) | **MUST** | Phase 2 |
| Producer listing create/manage + validation (FR-10, 11) | **MUST** | Phase 3 |
| Buyer requirements (FR-20) | **MUST** | Phase 4 |
| Marketplace browse + filters + landed estimate (FR-30) | **MUST** | Landed estimate uses pure cost util |
| Order lifecycle + atomic reservation (FR-40, 41) | **MUST** | Direct-order API built here; UI button is SHOULD |
| Demand forecast + interval + fallback + model card (FR-50, 52, 53) | **MUST** | Phase 6 |
| Hub ranking / supply-demand (FR-51, 101) | **MUST** | Phase 6 |
| Matching: candidates, explanations, partial/multi, accept (FR-60, 61, 62) | **MUST** | Phase 7 |
| Logistics estimate + vehicles (FR-70, 71) | **MUST** | Phase 8 |
| Route optimization, baseline, plan approve/discard, unassigned, map (FR-80, 81, 82, 84, 85) | **MUST** | Phase 9 |
| Price waterfall, benchmark, fair band, scenario (FR-90, 91, 92) | **MUST** | Phase 10 |
| Analytics overview + modelled gap (FR-100, 102) | **MUST** | Phase 11 |
| Seed/reset, synthetic labelling, health (FR-110, 111, 112) | **MUST** | Phase 12 |
| Registration (FR-02), requirement edit/cancel UI (FR-21) | SHOULD | Cancel endpoint is MUST-level in tests; registration UI can slip |
| Listing detail page, direct order button (FR-31, 32) | SHOULD | |
| Producer opportunities (FR-63) | SHOULD | |
| Shipment dispatch/deliver (FR-83) | SHOULD | Approve is MUST |
| Perishability constraint in solver | SHOULD | |
| Docker image + deployed backup | SHOULD | |
| Frontend unit tests (Vitest) | SHOULD | Backend tests are MUST |
| OSRM road distances (FR-86) | NICE | Haversine is default |
| Agmarknet snapshot ingestion (FR-93) | MUST (in Phase 2) | Offline snapshot parser included |
| Hindi labels (FR-120) | NICE | Listing flow only |
| RandomForest comparison row | NICE | |
| Playwright E2E, GitHub Actions CI | NICE | |
| Payments, chat, ratings, live tracking, individual consumers, holidays calendar, global min-cost-flow matching, Postgres/Alembic, price forecasting, cold chain, mixed-load rules, mobile apps | **FUTURE** | PRD §18 |

**Cut list (drop in this order when behind):** 1 Hindi labels → 2 OSRM → 3 RF comparison → 4 listing detail page → 5 producer opportunities UI → 6 registration UI → 7 perishability constraint → 8 dispatch/deliver UI → 9 Docker/deployed backup. **Never cut:** any MUST row; the demo path is PREDICT→MATCH→MOVE→SELL→ANALYSE.

**Priority order of the MVP (from the brief):** 1 direct listing → 2 buyer requirements → 3 marketplace → 4 demand forecast → 5 smart matching → 6 logistics calculation → 7 route optimization → 8 price transparency → 9 analytics. Phases 2–11 follow exactly this order.

**Verdict:** 32.0 planned hours fits ~3 days at ~10–11 h/day with ~2.5 h buffer, provided Phase 9 is timeboxed and the cut list is enforced. The plan is tight, not generous.

## 17. 3-day schedule

| Day | Hours | Phases | Day-end checkpoint |
|---|---|---|---|
| Day 1 | ~11.5 | 0, 1, 2, 3, 4, 5 | Producer lists → buyer orders → producer confirms, in browser, with tests green |
| Day 2 | ~10.5 | 6, 7, 8, 9 | Forecast visible; match → accept works; seeded pool yields a route plan |
| Day 3 | ~10.0 | 10, 11, 12, 13 | Full demo path twice from reset; tests executed; freeze + `demo-ready` |

## 18. Phase risks summary

Highest: Phase 9 (OR-Tools), Phase 6 (time sink), Phase 12 (integration surprises). Mitigations are in each phase and in the cut list.

