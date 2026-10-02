# Data — KrishiSetu

Status: PLANNED. Consistent with Architecture.md (tables, config files, scripts) and feeds ML.md and API.md.

## 1. Data principles

1. **Every record is either REAL (with provenance) or SYNTHETIC/DEMO (labelled).** Never blended silently.
2. Labelling is structural: boolean `is_demo` / `is_synthetic` columns, a `source` enum on price data, `generator_version` on synthetic history, and a UI badge (Design.md).
3. Illustrative constants (vehicle rates, margins, shelf life) live in YAML and are labelled `ASSUMPTION` in docs and UI tooltips.
4. No number in the product or docs may be presented as a measured real-world result unless it came from a real dataset documented here.

## 2. Dataset inventory

| ID | Dataset | Real / Synthetic | Source | Used for | Status |
|---|---|---|---|---|---|
| DS-01 | `demand_history.csv` — daily bulk demand (kg) per hub × crop, plus daily avg price | **SYNTHETIC** (generator v1) | `ml/generate_data.py` + `config/generator.yaml` | Train/validate/test demand model; forecast chart history | PLANNED (MUST) |
| DS-02 | `market_prices` — daily min/modal/max ₹/kg per hub reference market × crop, last 90 days | **SYNTHETIC** by default (`source=SYNTHETIC_DEMO`); **REAL** (`source=AGMARKNET_SNAPSHOT`) if DS-03 is ingested | Generator (derived from DS-01 price series) or DS-03 | Price benchmark, fair band, waterfall | PLANNED (MUST synthetic; NICE real) |
| DS-03 | `data/raw/agmarknet_snapshot.csv` | **REAL** (optional) | data.gov.in "Current Daily Price of Various Commodities from Various Markets (Mandi)" — https://data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi (derived from Agmarknet, http://agmarknet.gov.in). Free account + API key reported to be required; API availability for this resource must be verified on the day (Research §7). Licence: check the OGD licence on the resource page before redistributing. | Optional replacement for DS-02 | PLANNED (NICE) |
| DS-04 | Demo entities: users, producers, buyers, listings, requirements, orders, vehicles | **SYNTHETIC/DEMO** (fictional names, suffix "[DEMO]") | `db/seed.py` (deterministic) | Demo, tests | PLANNED (MUST) |
| DS-05 | `crops` reference | **ASSUMPTION** attributes (shelf life, transit limit) | `db/seed.py` | Matching freshness, filters | PLANNED (MUST) |
| DS-06 | `demand_hubs` reference | Approximate real city coordinates; hub demand itself synthetic | `db/seed.py` | Forecast, hub ranking | PLANNED (MUST) |
| DS-07 | Logistics constants | **ASSUMPTION** | `config/logistics.yaml` | Cost, time | PLANNED (MUST) |
| DS-08 | `config/market_hub_map.csv` | Manual mapping real mandi name → hub | Developer | Only needed for DS-03 | PLANNED (NICE) |
| DS-09 | `ml/artifacts/model_card.json` | Derived (metrics on synthetic data) | `ml/train.py` | Model card endpoint | PLANNED (MUST) |
| DS-10 | `tests/fixtures/*` | SYNTHETIC tiny fixtures | Hand-written | Automated tests | PLANNED (MUST) |

**Not available / not used:** real buyer-level demand; real farm-gate prices; real retail prices; real freight quotes; real FPO registries.

## 3. Training / validation / test / demo split

| Split | Content | Rule |
|---|---|---|
| Training | DS-01 rows, oldest → (T−84 days) | Chronological |
| Validation | (T−83) → (T−28) — 56 days | Early stopping, model selection, deployment gate |
| Test | last 28 days ending at T | Reported once per training run; never used for tuning |
| Demo | DS-04 entities + forecasts generated for T+1…T+7 | Independent of the ML splits; forecast targets have no ground truth |

`T` = last history date = generation date − 1 day (`generate_data.py --end-date` overrides).

## 4. Synthetic demand generator (DS-01) — documented process

Fixed seed (`seed: 42`). Panel = 5 hubs × 5 crops × 730 days (≈ 18,250 rows before dropout). For hub *h*, crop *c*, day *d*:

```
level(h,c)        = base_kg[c] * hub_scale[h]
seasonal(c,d)     = 1 + amp[c] * sin(2π * (doy(d) - phase[c]) / 365.25)
dow(d)            = dow_factor[weekday(d)]                 # config, e.g. higher toward weekend
trend(d)          = 1 + trend_per_year * (d - start)/365
price(c,d)        = base_price[c] * price_seasonal(c,d) * exp(AR1 noise)   # ₹/kg
price_effect      = (price(c,d)/base_price[c]) ** (-elasticity)           # elasticity = 0.3
shock(d)          = 1.5 with prob 0.01 else 1.0           # random demand spikes (unforecastable)
noise             = lognormal(0, sigma=0.12)
demand_kg(h,c,d)  = level * seasonal * dow * trend * price_effect * shock * noise
```
Post-processing: drop ~1% of rows at random (missing days, exercises cleaning); the **last 30 days of price are mean-reverted to within ±10% of `base_price[c]`** so demo asks/budgets stay coherent (`DEMO-PRICE-ANCHOR`).

Base price levels (illustrative, **ASSUMPTION**, ₹/kg): Tomato 24, Onion 22, Potato 18, Cauliflower 28, Green Chilli 45. Base demand (kg/day per hub, illustrative): Tomato 900, Onion 1,400, Potato 1,600, Cauliflower 350, Green Chilli 120; `hub_scale`: Delhi North 1.6, Gurugram 1.0, Noida 1.0, Ghaziabad 0.9, Faridabad 0.7.

**Disclosure (mandatory, shown in UI/model card):** *"Demand history is synthetic, generated from a documented process. Forecast metrics validate the pipeline, not real-world accuracy."* The model can learn the generator's structure, so metrics will look good; that is expected and must not be presented as real performance.

## 5. Real price snapshot ingestion (DS-03 → DS-02, NICE)

`scripts/ingest_agmarknet.py` (PLANNED, NICE):
1. Read `data/raw/agmarknet_snapshot.csv`. Expected columns (case-insensitive; verify at download time): `state, district, market, commodity, variety, grade, arrival_date, min_price, max_price, modal_price`.
2. Keep rows whose `commodity` ∈ `crops.agmarknet_commodity_name` and whose `market` ∈ `market_hub_map.csv`.
3. Parse `arrival_date` (`dd/mm/yyyy`), convert prices **₹/quintal → ₹/kg (÷100)** `[ASSUMPTION A-05]`, aggregate by (hub, crop, date) using the mean across varieties.
4. Write to `market_prices` with `source=AGMARKNET_SNAPSHOT`, `is_synthetic=false`. Report row coverage; if coverage < 30 days for a hub × crop, keep synthetic rows for that pair.
5. Set `PRICE_SOURCE=agmarknet_snapshot`. UI badge switches from "Synthetic price" to "Agmarknet snapshot (date range)".

## 6. Database schema (authoritative — 15 tables)

Conventions: integer autoincrement PKs; `created_at`/`updated_at` UTC; money `Numeric(10,2)` ₹; quantities `Float` kg with validation; `is_demo` default `false` (seed sets `true`).

**users** — `id`, `email` UNIQUE, `password_hash`, `role` {PRODUCER,BUYER,ADMIN}, `display_name`, `is_demo`, `created_at`.

**producer_profiles** — `id`, `user_id` FK UNIQUE, `producer_type` {FARMER,FPO}, `org_name`, `state`, `district`, `locality` NULL, `lat`, `lng`, `member_farmers` INT NULL (FPO), `is_demo`, `created_at`.

**buyer_profiles** — `id`, `user_id` FK UNIQUE, `buyer_type` {RETAILER,RESTAURANT,PROCESSOR,INSTITUTION,CONSUMER_GROUP}, `org_name`, `hub_id` FK, `city`, `state`, `lat`, `lng`, `is_demo`, `created_at`.

**crops** — `id`, `name` UNIQUE, `category` {VEGETABLE,FRUIT}, `agmarknet_commodity_name`, `shelf_life_days` INT, `max_transit_hours` INT, `perishability` {HIGH,MEDIUM,LOW}, `notes` (ASSUMPTION flag).

**demand_hubs** — `id`, `name` UNIQUE, `city`, `state`, `lat`, `lng`, `reference_market_name` (SYNTHETIC label or real mandi name).

**listings** — `id`, `producer_id` FK, `crop_id` FK, `variety` NULL, `grade` {A,B,C}, `quantity_kg`, `quantity_available_kg`, `ask_price_per_kg`, `min_order_kg`, `harvest_date`, `available_from`, `available_until`, `status` {ACTIVE,SOLD_OUT,EXPIRED,WITHDRAWN}, `is_demo`, `created_at`, `updated_at`.
CHECK: `quantity_kg>0`, `0<=quantity_available_kg<=quantity_kg`, `ask_price_per_kg>0`, `min_order_kg>0 AND <=quantity_kg`, `available_until>=available_from`. Index `(crop_id,status,available_until)`.

**requirements** — `id`, `buyer_id` FK, `crop_id` FK, `grade_min` {A,B,C}, `quantity_kg`, `quantity_fulfilled_kg` (default 0), `max_landed_price_per_kg`, `needed_by` DATE, `status` {OPEN,PARTIALLY_FULFILLED,FULFILLED,CANCELLED,EXPIRED}, `notes` NULL, `is_demo`, `created_at`.

**orders** — `id`, `listing_id` FK, `requirement_id` FK NULL, `buyer_id` FK, `producer_id` FK, `crop_id` FK, `quantity_kg`, `agreed_price_per_kg` (farmgate), `transport_cost_estimate_per_kg`, `platform_fee_per_kg`, `delivery_date`, `status` {PLACED,CONFIRMED,REJECTED,CANCELLED,IN_TRANSIT,DELIVERED}, `origin` {MATCHING,MARKETPLACE}, `shipment_id` FK NULL, `allocated_transport_cost_total` NULL (set at plan approval), `is_demo`, `created_at`, `updated_at`. Indexes on `status`, `buyer_id`, `producer_id`.

**order_events** — `id`, `order_id` FK, `from_status` NULL, `to_status`, `actor_user_id` FK, `actor_role`, `note` NULL, `at`.

**vehicles** — `id`, `name`, `vehicle_type` {MINI_TRUCK,PICKUP,MEDIUM_TRUCK}, `capacity_kg`, `cost_per_km`, `fixed_cost_per_trip`, `avg_speed_kmph`, `depot_name`, `depot_lat`, `depot_lng`, `is_available`, `is_demo`.

**route_plans** — `id` (UUID string), `status` {PROPOSED,APPROVED,DISCARDED}, `created_by` FK users, `created_at`, `approved_at` NULL, `method` {ORTOOLS,GREEDY_FALLBACK}, `solver_status` text, `solve_time_ms`, `distance_source` {ESTIMATED_HAVERSINE,OSRM_ROAD}, `order_ids` JSON, `num_orders`, `num_unassigned`, `baseline_km`, `optimized_km`, `baseline_cost`, `optimized_cost`, `result_json` JSON (full plan incl. stops, geometry, unassigned with reasons).

**shipments** — `id`, `plan_id` FK, `vehicle_id` FK, `status` {PLANNED,DISPATCHED,DELIVERED}, `total_distance_km`, `total_cost`, `total_load_kg`, `peak_load_kg`, `utilization_pct`, `est_duration_min`, `created_at`, `dispatched_at` NULL, `delivered_at` NULL.

**shipment_stops** — `id`, `shipment_id` FK, `sequence`, `stop_type` {DEPOT_START,PICKUP,DROP,DEPOT_END}, `order_id` FK NULL, `label`, `lat`, `lng`, `load_after_kg`, `cum_distance_km`, `eta_min_from_start`.

**market_prices** — `id`, `hub_id` FK, `crop_id` FK, `market_name`, `price_date`, `min_price_per_kg`, `modal_price_per_kg`, `max_price_per_kg`, `source` {SYNTHETIC_DEMO,AGMARKNET_SNAPSHOT}, `is_synthetic`. UNIQUE `(hub_id,crop_id,price_date,source)`.

**demand_history** — `id`, `hub_id` FK, `crop_id` FK, `date`, `demand_kg`, `avg_price_per_kg`, `is_synthetic` (always true in MVP), `generator_version`. UNIQUE `(hub_id,crop_id,date)`.

There is **no** `demand_forecasts` table (D-015): forecasts are computed on demand and cached in memory.

## 7. Field definitions, units, enums

| Item | Definition |
|---|---|
| Quantity | kilograms, `0 < q ≤ 100,000`, max 1 decimal |
| Price | ₹ per kg, `0 < p ≤ 100,000`, 2 decimals |
| Grade | `A` (best) > `B` > `C`; a requirement with `grade_min=B` accepts A and B |
| Landed price (per kg) | `farmgate + transport_per_kg + platform_fee_per_kg` |
| Farmgate price | `orders.agreed_price_per_kg` = listing ask at order time |
| Modal price | most frequent wholesale price for the day (Agmarknet definition) |
| Hub | city-cluster demand point; buyers belong to one hub |
| Dates | `DATE` in Asia/Kolkata; timestamps UTC |
| Synthetic flag | `is_demo`/`is_synthetic`; any API response carrying forecast or price data also carries `data_source` |

Order statuses counted as **committed** in analytics: `CONFIRMED, IN_TRANSIT, DELIVERED`. Quantities that count toward requirement fulfilment: `PLACED, CONFIRMED, IN_TRANSIT, DELIVERED`.

## 8. Data validation (enforced at API via Pydantic and at DB via CHECK)

| Field | Rule | Error |
|---|---|---|
| quantity_kg | >0, ≤100,000 | `VALIDATION_ERROR` |
| ask/max price | >0, ≤100,000 | `VALIDATION_ERROR` |
| min_order_kg | >0 and ≤ quantity_kg | `VALIDATION_ERROR` |
| crop_id / hub_id | exists | `NOT_FOUND`/422 |
| harvest_date | ≤ today (IST) and ≥ today−30 | 422 |
| available_from/until | from ≤ until; until ≥ today | 422 |
| needed_by | ≥ today | 422 |
| lat/lng | lat 6–38, lng 68–98 (India bounding box) | 422 |
| ask price sanity | if ask > 3× latest benchmark modal → accepted with `warnings:["PRICE_FAR_ABOVE_BENCHMARK"]` | warning, not error |
| email | valid format, unique | 422/409 |
| password | ≥ 8 chars | 422 |

## 9. Preprocessing, missing values, normalization (ML data)

1. Sort by (hub, crop, date); reindex to a complete daily calendar per pair.
2. **Missing days** (~1% dropped by the generator): demand gap-filled for feature computation only by time-linear interpolation, limited to gaps ≤ 3 days; rows created by interpolation get `was_imputed=1` and are **excluded from the loss and metrics** (kept only as lag/rolling context). Gaps > 3 days: the pair's rows in that window are dropped.
3. **Outliers:** no winsorising of the target (shocks are real signal in the DGP); the price series is clipped to `[0.3×, 3×]` of its median to guard against corrupt values.
4. **Normalization:** tree models — none. Categorical `hub_id`, `crop_id` passed as categorical features. Metrics are also reported per-crop as WAPE so scale differences are visible.
5. **Units:** all demand in kg/day; prices ₹/kg.
6. **Real price ingestion:** ÷100 from ₹/quintal; drop rows with `modal<=0` or `min>max`; dedupe on (hub, crop, date).

## 10. Feature engineering

Defined exactly in ML.md §4 (calendar, lag ≥ 7, rolling on shifted series, price lags). Features use only information available ≥ 7 days before the target date (no leakage).

## 11. Update frequency and provenance

| Dataset | Update | Provenance record |
|---|---|---|
| DS-01 | On demand: `setup_demo` (regeneration) | `generator_version`, seed, end-date in `model_card.json` and `data/processed/demand_history.meta.json` |
| DS-02 synthetic | With DS-01 | `source` column |
| DS-02 real | Manual snapshot; not live | Snapshot date range stored in `data/processed/prices.meta.json`, shown in UI |
| DS-04 | Deterministic re-seed (reset endpoint / script) | `is_demo=true` |
| Model | Manual retrain | `model_card.json`: trained_at, data range, git commit (if available), metrics |

No data is described as "live" or "real-time" anywhere.

## 12. Demo seed specification (authoritative for Demo.md and tests)

Dates are relative to the **seed day** (`today`, IST). All names carry `[DEMO]`. All rows `is_demo=true`. Coordinates are approximate district/city centres `[ASSUMPTION A-12]`.

**Crops (ids 1–5)** — name · shelf_life_days · max_transit_hours · perishability (all ASSUMPTION):
1 Tomato · 7 · 12 · HIGH; 2 Onion · 60 · 48 · LOW; 3 Potato · 60 · 48 · LOW; 4 Cauliflower · 5 · 10 · HIGH; 5 Green Chilli · 7 · 12 · HIGH.

**Hubs (ids 1–5)** — 1 Delhi North (28.70, 77.17); 2 Gurugram (28.46, 77.03); 3 Noida (28.54, 77.39); 4 Ghaziabad (28.67, 77.45); 5 Faridabad (28.41, 77.31). `reference_market_name` = `"<Hub> Reference Market (SYNTHETIC)"`.

**Producers (P1–P6)**

| Id | Type | Name | Location (lat, lng) | Login persona |
|---|---|---|---|---|
| P1 | FPO | Sonipat Kisan Collective [DEMO] | Sonipat, HR (28.99, 77.02) | `fpo_sonipat` |
| P2 | FPO | Bulandshahr Growers Union [DEMO] | Bulandshahr, UP (28.41, 77.85) | — |
| P3 | FARMER | Alwar Farmer #1 [DEMO] | Alwar, RJ (27.56, 76.61) | — |
| P4 | FPO | Meerut Agri Producers [DEMO] | Meerut, UP (28.98, 77.71) | `fpo_meerut` |
| P5 | FARMER | Karnal Farmer #1 [DEMO] | Karnal, HR (29.69, 76.99) | `farmer_karnal` |
| P6 | FPO | Panipat Vegetable Growers [DEMO] | Panipat, HR (29.39, 76.97) | — |

**Buyers (B1–B5)**

| Id | Type | Name | Hub | Location | Persona |
|---|---|---|---|---|---|
| B1 | RESTAURANT | Gurugram Restaurant Group [DEMO] | Gurugram | (28.47, 77.05) | `buyer_gurugram` |
| B2 | CONSUMER_GROUP | Noida RWA Group-Buying Collective [DEMO] | Noida | (28.57, 77.35) | `buyer_noida` |
| B3 | RETAILER | Delhi Fresh Retail Chain [DEMO] | Delhi North | (28.72, 77.15) | — |
| B4 | PROCESSOR | Ghaziabad Sauce & Pickle Processor [DEMO] | Ghaziabad | (28.68, 77.42) | — |
| B5 | INSTITUTION | Faridabad Institutional Kitchen [DEMO] | Faridabad | (28.42, 77.32) | — |

Operator: `operator` (ADMIN). Emails `<persona>@demo.krishisetu.local`, password `demo1234` (**demo DB only**, disabled when `DEMO_MODE=false`).

**Vehicles (V1–V5)** — depot "Sonipat Transport Hub (SYNTHETIC)" (28.98, 77.03): V1 MT-01 MINI_TRUCK 750 kg · V2 PK-01 PICKUP 1,500 kg · V3 MD-01 MEDIUM_TRUCK 4,000 kg. Depot "Ghaziabad Transport Hub (SYNTHETIC)" (28.66, 77.44): V4 PK-02 PICKUP 1,500 kg · V5 MT-02 MINI_TRUCK 750 kg. Rates (ASSUMPTION): MINI ₹12/km + ₹400/trip; PICKUP ₹16/km + ₹600/trip; MEDIUM ₹26/km + ₹1,200/trip; 30 km/h.

**Listings (L1–L14), all ACTIVE** — `harvest = today−1` and `available today → today+3` for HIGH-perishability crops; `harvest = today−3`, `available today → today+10` for Onion/Potato.

| Id | Producer | Crop | Grade | Qty kg | Ask ₹/kg | Min order |
|---|---|---|---|---|---|---|
| L1 | P2 | Tomato | B | 800 | 22.50 | 100 |
| L2 | P6 | Tomato | A | 1,200 | 24.00 | 200 |
| L3 | P3 | Tomato | C | 600 | 19.50 | 100 |
| L4 | P5 | Tomato | B | 500 | 23.00 | 100 |
| L5 | P4 | Onion | A | 6,000 | 22.50 | 500 |
| L6 | P2 | Onion | B | 3,000 | 21.50 | 500 |
| L7 | P3 | Onion | B | 2,000 | 21.00 | 300 |
| L8 | P4 | Potato | A | 4,000 | 18.00 | 500 |
| L9 | P2 | Potato | B | 2,500 | 17.00 | 300 |
| L10 | P1 | Cauliflower | A | 700 | 28.50 | 100 |
| L11 | P6 | Cauliflower | B | 500 | 27.00 | 100 |
| L12 | P5 | Green Chilli | A | 300 | 46.00 | 50 |
| L13 | P1 | Green Chilli | B | 250 | 43.50 | 50 |
| L14 | P6 | Green Chilli | A | 200 | 47.00 | 50 |

**Seeded orders — routing pool (status CONFIRMED, no shipment, origin MARKETPLACE)**

| Id | Listing | Route | Qty kg | Price |
|---|---|---|---|---|
| O1 | L1 Tomato | P2 → B5 | 600 | 22.50 |
| O2 | L5 Onion | P4 → B4 | 1,200 | 22.50 |
| O3 | L8 Potato | P4 → B3 | 900 | 18.00 |
| O4 | L2 Tomato | P6 → B3 | 500 | 24.00 |
| O5 | L10 Cauliflower | P1 → B2 | 400 | 28.50 |
| O6 | L12 Green Chilli | P5 → B1 | 150 | 46.00 |

**Seeded historical orders (status DELIVERED, delivered 2–10 days ago, origin MARKETPLACE, no shipment)**: H1 L6 Onion 1,000 kg @21.50 → B4; H2 L9 Potato 800 @17.00 → B5; H3 L7 Onion 600 @21.00 → B2; H4 L11 Cauliflower 200 @27.00 → B1. (Transport basis = ESTIMATE; no route data.)

Seeding orders goes through the real reservation service, so **available quantities after seed**: L1 200 · L2 700 · L3 600 · L4 500 · L5 4,800 · L6 2,000 · L7 1,400 · L8 3,100 · L9 1,700 · L10 300 · L11 300 · L12 150 · L13 250 · L14 200.

**Open requirements (R1–R8)**

| Id | Buyer | Crop | Min grade | Qty kg | Max landed ₹/kg | Needed by | Purpose |
|---|---|---|---|---|---|---|---|
| R1 | B1 | Tomato | B | 1,500 | 29.00 | +1 day | Live demo: match before/after new listing |
| R2 | B5 | Onion | B | 6,500 | 28.00 | +3 | Multi-source allocation |
| R3 | B2 | Cauliflower | A | 1,000 | 37.00 | +2 | Partial fill (only L10, 300 kg, is Grade A) |
| R4 | B3 | Potato | B | 3,000 | 24.00 | +2 | Normal match |
| R5 | B4 | Tomato | C | 1,000 | 27.00 | +2 | Low-grade tolerant processor |
| R6 | B1 | Green Chilli | B | 300 | 55.00 | +2 | Small lots |
| R7 | B3 | Cauliflower | B | 400 | 36.00 | +1 | Freshness sensitivity |
| R8 | B5 | Tomato | A | 2,500 | 22.00 | +2 | **No match**: budget below every Grade-A ask |

**Live demo listing (created during the demo, not seeded):** L15 — P1, Tomato, A, 2,000 kg, ask 23.00, min order 200, harvest today, available today → today+3.

Expected behaviours of the seed (verify and record in Demo.md log; none of these are pre-claimed numbers): R8 has no candidate within budget; R3 is a partial fill; R1 before L15 is likely short or over budget because the remaining tomato lots are small and far (this is the aggregation problem the demo illustrates), and after L15 a single-source full fill is expected.

**Market prices:** 90 days × 5 hubs × 5 crops (SYNTHETIC_DEMO), modal anchored near base prices in the last 30 days (`DEMO-PRICE-ANCHOR`).

## 13. Config files (content outline — values are ASSUMPTIONS unless noted)

`config/logistics.yaml`: vehicle types (capacity, `cost_per_km`, `fixed_cost_per_trip`), `avg_speed_kmph: 30`, `service_minutes_per_stop: 20`, `road_circuity_factor: 1.35`, `return_leg_factor: 2.0`, `max_route_minutes: 600`, `max_order_chunk_kg: 4000`.
`config/pricing.yaml`: `platform_fee_pct: 2.0`, `commission_agent_pct: 5.0`, `trader_margin_pct: 8.0`, `retail_margin_pct: 12.0`, `last_mile_cost_per_kg: 1.0`, `price_warning_multiple: 3.0`.
`config/matching.yaml`: weights `price 0.40 / distance 0.20 / freshness 0.20 / fill 0.20`, `price_headroom_fraction: 0.30`, `max_match_distance_km: 300`, `supply_radius_km: 150`, `shortage_ratio: 0.7`, `surplus_ratio: 1.3`.
`config/generator.yaml`: seed, horizon days 730, base kg/prices, hub scales, dow factors, amplitudes/phases, elasticity 0.3, noise sigma 0.12, shock prob 0.01, dropout 0.01.
