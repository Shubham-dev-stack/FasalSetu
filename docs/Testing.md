# Testing — FasalSetu

Status: IN PROGRESS. Phase 0 and Phase 1 test suites executed and recorded below.

## 1. Strategy

| Layer | Tool | Scope | Priority |
|---|---|---|---|
| Unit | pytest | Pure functions: geo, cost, scoring, allocation, pricing, features, metrics, state machine | MUST |
| API | pytest + FastAPI `TestClient` + temp SQLite per test session | Every endpoint: success, validation, authz, error envelope | MUST |
| Database | pytest | Constraints, atomic reservation, seed determinism | MUST |
| ML | pytest | Leakage, interval ordering, fallback, model-card flags | MUST |
| Matching | pytest on seed + fixtures | Filters, ranking, allocation | MUST |
| Routing | pytest | Capacity, precedence, unassigned, fallback | MUST |
| Integration | pytest (`tests/integration/test_demo_path.py`) | Demo path via API from fresh seed | MUST |
| UI | Vitest + Testing Library (components), manual checklist (screens) | Forms, states, badges | SHOULD / MUST (manual) |
| Responsive | Manual at 360 / 768 / 1280 px | Layout, no horizontal scroll | MUST |
| E2E | Playwright | Demo path | NICE |

Commands (from README): `pytest -q` (backend), `npm run test` and `npm run build` (frontend), `ruff check .`.

Test data: the deterministic seed (Data.md §12) plus tiny hand-written fixtures in `backend/tests/fixtures/` (SYNTHETIC). Fixtures use fixed dates passed into functions (no hidden `today`).

## 2. Acceptance criteria — Auth / system / data / security

| ID | Criterion |
|---|---|
| AC-AUTH-01 | Valid login returns token, role, user; token decodes with expected claims and expiry |
| AC-AUTH-02 | Wrong password and unknown email both return 401 `UNAUTHENTICATED` with identical message |
| AC-AUTH-03 | Role guard: BUYER calling `POST /listings` → 403; PRODUCER calling `POST /routes/optimize` → 403; no token → 401 |
| AC-AUTH-04 | With `DEMO_MODE=false`, `POST /auth/demo-login` and `POST /system/reset-demo` → 404 `DEMO_DISABLED` |
| AC-SYS-01 | `GET /health` returns status and db state without auth |
| AC-SYS-02 | Every non-2xx response matches the error envelope; validation errors list `details[].field` |
| AC-SYS-03 | Simulated DB failure returns 503 `DATABASE_UNAVAILABLE`, no stack trace |
| AC-DATA-01 | After seed, every row in demo tables has `is_demo=true`; synthetic datasets have `is_synthetic=true` / `source` set |
| AC-DATA-02 | `model_card.json` has `data_source:"SYNTHETIC"` and a disclaimer; `GET /forecasts/*` carry `data_source` |
| AC-DATA-03 | Running seed twice yields identical entity counts and identical IDs for reference/demo entities |
| AC-DATA-04 | DB CHECK constraints reject: negative/zero quantity, available>total, min_order>quantity, price≤0, until<from |
| AC-SEC-01 | Passwords stored hashed (no plaintext in DB or logs) |
| AC-SEC-02 | Expired or tampered JWT → 401 |
| AC-SEC-03 | Object-level authz: producer A cannot PATCH producer B's listing; buyer A cannot read buyer B's requirement/order (403) |
| AC-SEC-04 | SQL-injection-like strings in query params/body do not alter behaviour (parameterised queries) |
| AC-SEC-05 | No secrets in repo (`git grep` for `SECRET_KEY=` values, keys); `.env` ignored |
| AC-SEC-06 | CORS: in `prod` mode no wildcard origin; responses contain no stack traces |

## 3. Listings and requirements

| ID | Criterion |
|---|---|
| AC-LST-01 | Valid listing creates `ACTIVE` listing with `quantity_available_kg = quantity_kg` |
| AC-LST-02 | Quantity ≤0, >100000 or non-numeric → 422 with field `quantity_kg` (**invalid quantity**) |
| AC-LST-03 | Price ≤0 or >100000 → 422 (**invalid price**); ask >3× benchmark → 201 with `PRICE_FAR_ABOVE_BENCHMARK` warning |
| AC-LST-04 | `min_order>quantity`, `until<from`, `until<today`, harvest in future or >30 days old → 422 |
| AC-LST-05 | Unknown `crop_id` → 422/404 per API.md |
| AC-LST-06 | Non-owner PATCH → 403 |
| AC-LST-07 | Expired/withdrawn/sold-out listings are excluded from default marketplace results (**unavailable produce**) |
| AC-REQ-01 | Valid requirement → `OPEN` with `quantity_fulfilled_kg=0` |
| AC-REQ-02 | `needed_by` in the past → 422 |
| AC-REQ-03 | Invalid quantity or max price → 422 |
| AC-REQ-04 | Owner can cancel; cannot reduce quantity below fulfilled; non-owner → 403 |

## 4. Marketplace and orders

| ID | Criterion |
|---|---|
| AC-MKT-01 | Filters (crop, grade_min, state, max_price, harvest age) return only matching listings; `sort` orders correctly |
| AC-MKT-02 | `landed_estimate` present for BUYER callers (and when `buyer_lat/lng` given) and equals ask + transport + fee (±0.01) |
| AC-MKT-03 | No results → `{items:[],total:0}`; UI shows empty state |
| AC-ORD-01 | Direct order reserves quantity atomically: `available` decreases by ordered qty |
| AC-ORD-02 | Ordering more than available → 409 `INSUFFICIENT_QUANTITY`; nothing written |
| AC-ORD-03 | Ordering below `min_order_kg` → 422 |
| AC-ORD-04 | Two sequential orders that together exceed availability: second fails; available never negative (**no oversell**) |
| AC-ORD-05 | Allowed transitions succeed per API.md §7 matrix; every other transition → 409 `INVALID_TRANSITION`; each writes an `order_events` row; ADMIN override logged with `actor_role=ADMIN` |
| AC-ORD-06 | Reject/cancel restores `quantity_available_kg` and recomputes requirement fulfilment/status |
| AC-ORD-07 | Order on withdrawn/expired/sold-out listing → 409 `LISTING_UNAVAILABLE` |

## 5. Forecasting / ML

| ID | Criterion |
|---|---|
| AC-FC-01 | `GET /forecasts/demand` returns `horizon_days` points; for LIGHTGBM `lo ≤ yhat ≤ hi` and all ≥ 0 |
| AC-FC-02 | With artifacts removed or model load raising, endpoint returns 200 with `method="SEASONAL_NAIVE_FALLBACK"`, `lo/hi=null` (**ML prediction failure**) |
| AC-FC-03 | Unknown hub/crop → 404 |
| AC-FC-04 | **Leakage test:** features for date d from series truncated at d−7 equal features from the full series |
| AC-FC-05 | `model-info` returns metrics, split ranges, `deployed_method`, synthetic disclaimer; metrics file is produced by `ml.train` (not hand-written) |
| AC-FC-06 | History <14 days → 422 `INSUFFICIENT_HISTORY` (**missing dataset values**); 14–34 days → fallback; gap-filling flags imputed rows and excludes them from metrics |
| AC-FC-07 | `GET /forecasts/hubs` returns hubs sorted by `opportunity_score`; status = SHORTAGE if ratio<0.7, SURPLUS if >1.3, else BALANCED; each listing counted once (nearest hub) |
| AC-FC-08 | Metric functions (MAE, RMSE, WAPE, MAPE with y≥10 guard, coverage) verified on hand-computed tiny arrays |
| AC-FC-09 | Deployment gate logic: LightGBM deployed only when it beats both baselines on validation (×0.95) and test (unit-tested with stub metrics) |

## 6. Matching

| ID | Criterion |
|---|---|
| AC-MAT-01 | Candidates sorted by `scores.total` desc with deterministic tie-break |
| AC-MAT-02 | Each hard filter (grade, budget, distance, freshness/transit, availability, expiry) excludes correctly and appears in `near_misses` with the right `excluded_reason` |
| AC-MAT-03 | **Partial quantity match:** seed R3 (Cauliflower, grade A, 1,000 kg) yields `PARTIAL` with shortfall; UI shows shortfall banner |
| AC-MAT-04 | **No buyer match:** seed R8 (budget below every Grade-A ask) yields `NONE`, empty allocations, near-misses explain budget gap |
| AC-MAT-05 | Multi-source: allocations sum ≤ requested, each ≤ available, each ≥ `min_order_kg`; seed R2 uses >1 listing |
| AC-MAT-06 | `accept` revalidates server-side and creates orders atomically with `origin=MATCHING`; requirement fulfilment updated |
| AC-MAT-07 | If a listing's availability changed between view and accept → 409 `STALE_ALLOCATION`, zero orders created |
| AC-MAT-08 | Every candidate carries four factor scores, weights and ≥1 reason |

## 7. Logistics and routing

| ID | Criterion |
|---|---|
| AC-LOG-01 | Haversine for a known city pair within ±1 km of the reference value; road distance = haversine × circuity |
| AC-LOG-02 | Vehicle selection picks the smallest type with capacity ≥ qty |
| AC-LOG-03 | **Insufficient vehicle capacity** for one vehicle: qty > largest capacity → multiple trips (n_full largest + remainder fit) |
| AC-LOG-04 | Cost = Σ(fixed + rate × distance × return_factor); `cost_per_kg = cost/qty`; hand-computed fixture matches ±0.01 |
| AC-LOG-05 | No available vehicles → 409 `NO_VEHICLE_AVAILABLE` |
| AC-RTE-01 | For every shipment, load never exceeds vehicle capacity at any stop |
| AC-RTE-02 | For every order chunk, pickup precedes drop and both are on the same vehicle |
| AC-RTE-03 | Route duration (incl. service) ≤ `max_route_minutes` |
| AC-RTE-04 | On the seeded pool (O1–O6) the optimized cost ≤ baseline cost; if not, the response reports negative savings truthfully (test asserts consistency of the numbers, and the observed relationship is recorded in the log) |
| AC-RTE-05 | Infeasible/oversized load → listed in `unassigned` with a reason; call does not crash (**no route available** case) |
| AC-RTE-06 | No CONFIRMED unrouted orders → 422 `NO_ELIGIBLE_ORDERS` |
| AC-RTE-07 | Solver time limit respected (wall time ≤ limit + 3 s); on solver failure `GREEDY_FALLBACK` plan is valid under AC-RTE-01..03 |
| AC-RTE-08 | OSRM unreachable (mocked) → plan still returned with `distance_source="ESTIMATED_HAVERSINE"` (only if OSRM implemented) |
| AC-RTE-09 | Approve creates shipments/stops, sets `orders.shipment_id` and `allocated_transport_cost_total` (kg-km split sums to route cost ±0.01); second approve → 409 |
| AC-RTE-10 | Discard leaves orders unchanged; approve of a plan whose order changed → 409 `STALE_PLAN` |

## 8. Pricing and analytics

| ID | Criterion |
|---|---|
| AC-PRC-01 | `landed = farmgate + transport + platform_fee` (±0.01); `platform_fee = farmgate × pct/100` |
| AC-PRC-02 | Benchmark object always includes `source` and `is_synthetic`; response has `basis:"MODELLED_SCENARIO"` and the full assumptions |
| AC-PRC-03 | Scenario formulas (ML.md §12) verified against a hand-computed fixture; fair band `null` when U ≤ L |
| AC-PRC-04 | Missing benchmark → `benchmark:null, scenario:null`, HTTP 200 (**missing dataset values**) |
| AC-ANL-01 | On the seed, KPIs equal values computed independently by a test using direct SQL/py arithmetic |
| AC-ANL-02 | After accepting an allocation, confirming it and approving a plan, the relevant KPIs change as expected |
| AC-ANL-03 | Empty DB → counts 0, ratios/averages `null`, HTTP 200 |

## 9. UI and responsive

| ID | Criterion |
|---|---|
| AC-UI-01 | At 360 px no page-level horizontal scroll on any screen; tables scroll within containers |
| AC-UI-02 | Every data screen implements loading, empty and error states (manual checklist + component tests) |
| AC-UI-03 | DEMO DATA badge visible on all screens in demo mode; Synthetic/Modelled/Estimated badges present where specified in Design.md |
| AC-UI-04 | Forms mirror Data.md §8 validation; server `details` shown on the right field |
| AC-UI-05 | Keyboard: all interactive elements reachable with visible focus; inputs labelled; touch targets ≥44 px (manual) |

## 10. Integration

| ID | Criterion |
|---|---|
| AC-INT-01 | From a fresh reset the full Demo.md path runs via API test: create listing → forecast/hubs → candidates → accept → confirm → optimize → approve → breakdown → analytics |
| AC-INT-02 | Same path in the browser twice in a row without manual DB edits |
| AC-INT-03 | `reset-demo` restores the initial state (counts, availability) |

## 11. Edge cases and failure handling matrix

| Case | Expected | Covered by |
|---|---|---|
| Invalid quantity | 422, field error | AC-LST-02, AC-REQ-03 |
| Invalid price | 422 | AC-LST-03 |
| Unavailable produce | 409 `LISTING_UNAVAILABLE` / excluded from market | AC-ORD-07, AC-LST-07 |
| No buyer match | `NONE` + near-misses | AC-MAT-04 |
| Partial quantity match | `PARTIAL` + shortfall | AC-MAT-03 |
| Insufficient vehicle capacity | multi-trip / unassigned | AC-LOG-03, AC-RTE-05 |
| No route available | unassigned with reason / `NO_ELIGIBLE_ORDERS` | AC-RTE-05, 06 |
| Missing dataset values | fallback / 422 / null benchmark | AC-FC-06, AC-PRC-04 |
| ML prediction failure | fallback method | AC-FC-02 |
| API failure (frontend) | ErrorState with retry | AC-UI-02 |
| Database failure | 503 envelope | AC-SYS-03 |
| Concurrent orders | no oversell | AC-ORD-04 |
| OSRM/tiles failure | haversine / schematic list | AC-RTE-08, Design §12 |
| Stale accept / stale plan | 409 | AC-MAT-07, AC-RTE-10 |

## 12. Security checks (manual + automated)

Run AC-SEC-01…06; additionally review that demo credentials appear only in seed code and README demo section, that logs contain no tokens/passwords, and that `DEMO_MODE=false` hides the persona buttons in the UI build.

## 13. Non-functional spot checks (Phase 12)

Measured and recorded actuals across 50 requests per endpoint and optimizer solve runs on local machine:

| Endpoint / Operation | p50 latency | p95 latency | PRD §15 Target | Status |
|---|---|---|---|---|
| `GET /api/v1/health` | 5.39 ms | 7.64 ms | p95 < 500 ms | PASS |
| `GET /api/v1/reference` | 7.27 ms | 9.02 ms | p95 < 500 ms | PASS |
| `GET /api/v1/listings?limit=50` | 16.69 ms | 20.02 ms | p95 < 500 ms | PASS |
| `GET /api/v1/listings/1` | 12.84 ms | 16.16 ms | p95 < 500 ms | PASS |
| `GET /api/v1/requirements?limit=50` | 12.23 ms | 16.62 ms | p95 < 500 ms | PASS |
| `GET /api/v1/forecasts/demand` | 7.18 ms | 9.91 ms | p95 < 300 ms | PASS |
| `GET /api/v1/matching/requirements/4/candidates` | 14.03 ms | 15.95 ms | p95 < 500 ms | PASS |
| `GET /api/v1/pricing/breakdown` | 13.72 ms | 16.14 ms | p95 < 500 ms | PASS |
| `GET /api/v1/analytics/overview` | 33.41 ms | 43.23 ms | p95 < 500 ms | PASS |
| `GET /api/v1/analytics/supply-demand` | 25.05 ms | 34.53 ms | p95 < 500 ms | PASS |
| `POST /api/v1/routes/optimize` (confirmed pool, OR-Tools) | 5.08 s | 5.08 s | wall time ≤ 10 s | PASS |

## 14. Release gate (before `demo-ready` tag)

All MUST ACs executed; any failure either fixed or recorded in Memory.md "Known bugs" and excluded from the demo path; `npm run build` and `pytest -q` executed after the final commit; Demo.md path run twice; screenshots/video captured.

## 15. Execution log (append-only)

| Date | Command / check | Result (paste real output summary) | Notes |
|---|---|---|---|
| 2026-10-01 | `pytest -q tests/api/test_health.py` | `1 passed in 0.45s` | AC-SYS-01: Health check baseline passed |
| 2026-10-01 | `pytest -v` (backend suite) | `24 passed, 9 warnings in 7.79s` | AC-AUTH-01..06, AC-SYS-01..03, AC-GEO-01..02, AC-LOG-01..04, AC-SEC-01..04 passed |
| 2026-10-01 | `ruff check .` (backend linter) | `All checks passed!` | Zero lint or formatting errors across all backend code |
| 2026-10-01 | `npm test` (frontend vitest) | `Test Files: 1 passed (1), Tests: 2 passed (2), Duration: 2.19s` | Demo persona specification and metadata validation |
| 2026-10-01 | `npm run build` (frontend bundle) | `✓ 1494 modules transformed. dist/index.html 0.55 kB, dist/assets/index.js 192.65 kB (gzip: 60.76 kB). ✓ built in 24.47s` | Zero TypeScript or Vite compilation errors |
| 2026-10-01 | `pytest -v` (backend suite - Phase 2) | `31 passed, 9 warnings in 9.38s` | AC-GEN-01..05 (18,250 pre-dropout panel, ~1% dropout, seed reproducibility, positive ranges, benchmark prices), AC-AGM-01..02 (mandi snapshot aggregation/kg conversion, snapshot preservation during synthetic reseeding) |
| 2026-10-01 | `ruff check .` (backend linter - Phase 2) | `All checks passed!` | Zero lint or formatting errors across new Phase 2 code and tests |
| 2026-10-01 | `npm test` (frontend vitest - Phase 2 regression) | `Test Files: 1 passed (1), Tests: 2 passed (2), Duration: 2.19s` | Frontend tests verified unaffected by data layer additions |
| 2026-10-01 | `npm run build` (frontend bundle - Phase 2 regression) | `✓ 1494 modules transformed. dist/assets/index-CJ5Zz8SD.js 192.65 kB (gzip: 60.76 kB). ✓ built in 25.41s` | Frontend production bundle verified cleanly compiling |
| 2026-10-01 | `pytest -v` (backend suite - Phase 3) | `48 passed, 23 warnings in 21.83s` | AC-LST-01..07, AC-SEC-03, AC-AUTH-01..06, AC-SYS-01..03, AC-GEO-01..02, AC-LOG-01..04, AC-GEN-01..05, AC-AGM-01..02 passed; Producer profile, produce listing lifecycle, benchmark price sanity check & warning, dynamic expiry, and L1-L14 seeded lots verified |
| 2026-10-01 | `ruff check .` (backend linter - Phase 3) | `All checks passed!` | Zero lint or formatting errors across all backend code and test files |
| 2026-10-01 | `npm test` (frontend vitest - Phase 3) | `Test Files: 2 passed (2), Tests: 8 passed (8), Duration: 2.15s` | AC-LST-01..04 client-side validation rules and auth tests passed |
| 2026-10-01 | `npm run build` (frontend bundle - Phase 3) | `✓ 1503 modules transformed. dist/index.html 0.55 kB, dist/assets/index.js 230.19 kB (gzip: 68.04 kB). ✓ built in 6.24s` | Zero TypeScript or Vite compilation errors across new producer pages and components |
| 2026-10-01 | `pytest -v` (backend suite - Phase 4) | `63 passed, 30 warnings in 20.74s` | AC-REQ-01..04 passed; Buyer profile (GET/PATCH), requirement creation, listing, detail, lifecycle update, cancellation, Rule D-021 dynamic expiry on GET/PATCH, cross-buyer 403, producer 403 authorization guards, and seeded open requirements R1-R8 verified |
| 2026-10-01 | `ruff check .` (backend linter - Phase 4) | `All checks passed!` | Zero lint or formatting errors across all backend code and test files |
| 2026-10-01 | `npm test` (frontend vitest - Phase 4) | `Test Files: 3 passed (3), Tests: 17 passed (17), Duration: 2.10s` | Buyer requirement validation rules, dynamic expiry, terminal state immutability, educational landed price formula, and coordinate bounds verified |
| 2026-10-01 | `npm run build` (frontend bundle - Phase 4) | `✓ 1510 modules transformed. dist/assets/index-mYlNfQpy.js 262.27 kB (gzip: 73.31 kB). ✓ built in 5.43s` | Zero TypeScript or Vite compilation errors across new buyer pages, components, and router integration |
| 2026-10-01 | `pytest -v` (backend suite - Phase 5) | `74 passed, 69 warnings in 17.62s` | AC-ORD-01..05 passed; Unified marketplace discovery, indicative landed price estimates, atomic reservation on Listing, concurrency-safe requirement fulfillment, order transition state machine (PLACED -> CONFIRMED / REJECTED / CANCELLED), financial snapshotting, object-level authorization, and seeded orders O1-O6 (CONFIRMED) & H1-H4 (DELIVERED) verified |
| 2026-10-01 | `ruff check .` (backend linter - Phase 5) | `All checks passed!` | Zero lint or formatting errors across all backend code and test files |
| 2026-10-01 | `npm test` (frontend vitest - Phase 5) | `Test Files: 4 passed (4), Tests: 22 passed (22), Duration: 1.46s` | Marketplace and order placement validation rules, landed cost formula with 2% fee, transition permissions, and requirement compatibility checks verified |
| 2026-10-01 | `npm run build` (frontend bundle - Phase 5) | `✓ 1518 modules transformed. dist/assets/index-Bl-ZM4-m.js 303.11 kB (gzip: 80.76 kB). ✓ built in 5.26s` | Zero TypeScript or Vite compilation errors across MarketplacePage, OrdersPage, OrderDetailPage, and Order components |
| 2026-10-01 | `pytest -v tests/unit/test_forecast_ml.py` | `5 passed in 4.42s` | AC-FC-04 (strictly causal imputation, future leakage invariance), AC-FC-08 (pure metric functions hand-computed fixtures), AC-FC-09 (honesty deployment gate logic), chronological split temporal separation, quantile monotonicity |
| 2026-10-01 | `python -m ml.train` | `Point iteration 138, Val MAE: LGBM=105.42 (B2=134.54), Test MAE: LGBM=104.66 (B2=126.45), Gate Passed: True` | Model trained on Train, evaluated on Val & held-out Test; deployed model refit on Train+Val ONLY. Artifacts saved: model_point, model_q10, model_q90, feature_spec.json, model_card.json |
| 2026-10-01 | `pytest -v tests/api/test_forecasts.py` | `7 passed, 2 warnings in 13.90s` | AC-FC-01 (point + 80% interval), AC-FC-02/06 (seasonal naive fallback), AC-FC-03 (404s), AC-FC-05 (model card metadata), AC-FC-07 & Rule D-026 (nearest hub supply attribution without double-counting) |
| 2026-10-01 | `pytest -v` (backend suite - Phase 6) | `86 passed, 70 warnings in 41.62s` | All 86 backend tests passing; zero regressions across Auth, Profiles, Listings, Requirements, Orders, Marketplace, ML & Forecasting |
| 2026-10-01 | `ruff check .` (backend linter - Phase 6) | `All checks passed!` | Zero lint or formatting errors across all backend code and test files |
| 2026-10-01 | `npm test -- --run` (frontend vitest - Phase 6) | `Test Files: 5 passed (5), Tests: 27 passed (27), Duration: 12.89s` | AC-FC-01..07 client domain rules, horizon validation, interval monotonicity, Rule D-026 supply attribution, fallback null intervals verified |
| 2026-10-01 | `npm run build` (frontend bundle - Phase 6) | `✓ 2320 modules transformed. dist/assets/index-DpqPDomn.js 743.07 kB (gzip: 199.97 kB). ✓ built in 18.02s` | Zero TypeScript or Vite compilation errors across ForecastPage, ForecastChart, DemandPanel, ModelInfoModal |
| 2026-10-02 | `pytest -q` (backend suite - Phase 7) | `102 passed, 499 warnings in 23.39s` | AC-MAT-01..08 passed; Deterministic scoring bounded [0,1], hard filters F1-F6, tie-breaking (-score, price, id), R3 partial fill, R8 budget shortfall, R2 multi-source greedy allocation, atomic acceptance, STALE_ALLOCATION 409 guard, producer opportunities |
| 2026-10-02 | `ruff check .` (backend linter - Phase 7) | `All checks passed!` | Zero lint or formatting errors across Phase 7 matching code |
| 2026-10-02 | `npm test` (frontend vitest - Phase 7) | `Test Files: 6 passed (6), Tests: 34 passed (34), Duration: 1.60s` | Candidate card rendering, score breakdowns, near-miss summaries, shortfall alerts, below-min-order handling, and opportunities modal tested |
| 2026-10-02 | `npm run build` (frontend bundle - Phase 7) | `✓ 2325 modules transformed. dist/assets/index-CUhtSgvq.js 770.67 kB (gzip: 205.51 kB). ✓ built in 9.39s` | Clean compilation across MatchPage, CandidateCard, ScoreBreakdown, ProducerOpportunitiesModal |
| 2026-10-02 | `pytest -q` (backend suite - Phase 8) | `112 passed, 501 warnings in 22.42s` | AC-LOG-01..05 passed; Dedicated trip estimate calculation (fixed + rate*dist*2), multi-trip vehicle allocation, cost-per-kg, transit hours, 409 NO_VEHICLE_AVAILABLE handling, fleet vehicle inventory endpoint GET /logistics/vehicles |
| 2026-10-02 | `ruff check .` (backend linter - Phase 8) | `All checks passed!` | Zero lint or formatting errors across all backend modules |
| 2026-10-02 | `npm test` (frontend vitest - Phase 8) | `Test Files: 7 passed (7), Tests: 38 passed (38), Duration: 1.60s` | Fleet vehicle list, vehicle type formatting, dedicated logistics estimate response mapping, and multi-trip oversize load cost aggregation verified |
| 2026-10-02 | `pytest -q` (backend suite - Phase 10) | `129 passed, 503 warnings in 24.12s` | AC-PRC-01..04 passed; Per-order price waterfall breakdown (farmgate + transport + platform fee = landed ±0.01), APMC reference benchmark with provenance distinction, traditional multi-tier scenario modeling with disclosed assumptions, and deterministic fair price band verified |
| 2026-10-02 | `ruff check .` (backend linter - Phase 10) | `All checks passed!` | Zero lint or formatting errors across pricing module and tests |
| 2026-10-02 | `npm test` (frontend vitest - Phase 10) | `Test Files: 9 passed (9), Tests: 43 passed (43), Duration: 1.82s` | Waterfall price reconciliation, scenario formulas, and fair price band mapping verified |
| 2026-10-02 | `npm run build` (frontend bundle - Phase 10) | `✓ 2330 modules transformed. dist/assets/index.js 785.42 kB. ✓ built in 25.43s` | Clean compilation across OrderPriceBreakdown and DemandPanel price transparency components |
| 2026-10-02 | `pytest -q` (backend suite - Phase 11) | `136 passed, 889 warnings in 66.36s` | AC-ANL-01..03 passed; Platform KPI overview aggregation (committed volume, value, fill rate, logistics cost/kg, route savings, fleet utilization), empty-db null/zero handling, 14-day timeline series, and Hub x Crop supply-demand matrix with Rule D-026 single-hub attribution and status chips verified |
| 2026-10-02 | `ruff check .` (backend linter - Phase 11) | `All checks passed!` | Zero lint or formatting errors across analytics module, schemas, and tests |
| 2026-10-02 | `npm test -- --run` (frontend vitest - Phase 11) | `Test Files: 10 passed (10), Tests: 45 passed (45), Duration: 1.90s` | Analytics overview types, KPI formatting, supply-demand ratio thresholds (SHORTAGE < 0.7, SURPLUS > 1.3), and API mapping verified |
| 2026-10-02 | `npm run build` (frontend bundle - Phase 11) | `✓ 2332 modules transformed. dist/assets/index-BV0k4H5x.js 823.69 kB. ✓ built in 10.00s` | Clean production build of full SPA including AnalyticsPage dashboard |
| 2026-10-02 | `pytest -q` (backend suite - Phase 12) | `140 passed, 627 warnings in 38.49s` | AC-INT-01..03, AC-SYS-01..03, AC-AUTH-03..04, AC-SEC-03, AC-DATA-01..03 passed; Zero-drift reset idempotency verified twice sequentially, complete Demo.md path (PREDICT -> MATCH -> MOVE -> SELL -> ANALYSE) executed, edge cases (R3 partial, R8 budget shortfall, R2 multi-source) verified |
| 2026-10-02 | `ruff check .` (backend linter - Phase 12) | `All checks passed!` | Zero lint or formatting errors across all backend code, routers, and test files |
| 2026-10-02 | `npm test -- --run` (frontend vitest - Phase 12) | `Test Files: 10 passed (10), Tests: 45 passed (45), Duration: 1.98s` | Zero regressions; Navbar reset trigger and client API verified |
| 2026-10-02 | `npm run build` (frontend bundle - Phase 12) | `✓ 2332 modules transformed. dist/assets/index.js 823.69 kB. ✓ built in 16.05s` | Clean production build including SPA static mount and Dockerfile |




