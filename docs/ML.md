# ML.md — Demand forecasting, matching, logistics, routing, pricing formulas

Status: PLANNED. Consistent with Data.md (datasets, splits, seed) and Architecture.md (module boundaries). Numeric constants marked *(cfg)* live in `backend/config/*.yaml` and are ASSUMPTIONS.

## 1. What uses ML and what does not

| Component | Technique | ML? | Reason |
|---|---|---|---|
| Demand forecast (PREDICT) | LightGBM gradient boosting, quantile models for interval | **Yes** | Has a supervised target, lag/calendar features, tabular time series |
| Matching (MATCH) | Hard filters + weighted scoring + greedy allocation | **No** (D-011) | No training signal; explainability is the requirement; ML would be decoration |
| Logistics cost (MOVE) | Closed-form cost model | No | Transparent arithmetic |
| Route optimization (MOVE) | OR-Tools capacitated pickup-and-delivery VRP | No (optimization / "AI" in the OR sense) | Combinatorial problem; ML inappropriate |
| Price transparency (SELL) | Formulas over config + benchmark | No | Must be auditable |
| Analytics (ANALYSE) | SQL aggregates | No | — |

## 2. Demand forecasting — problem definition

- **Target:** `demand_kg(hub, crop, date)` — bulk-buyer demand for a crop in a demand hub on a given day.
- **Horizon:** 1–7 days ahead of last observed date `T`. **One model serves all horizons** because every feature is computed from information at least 7 days before the target date (direct strategy, no recursion).
- **Granularity:** daily, 5 hubs × 5 crops = 25 series.
- **Data:** DS-01, **synthetic** (Data.md §4). All reported metrics validate the pipeline only.

## 3. Training data, preprocessing, split

As Data.md §3 and §9: chronological split — train (oldest → T−84), validation (T−83 → T−28, 56 days), test (last 28 days). Imputed rows excluded from loss and metrics. Rows lacking any lag feature (first ~35 days per series) are dropped.

## 4. Features (for target date `d`, hub `h`, crop `c`; `x[t]` = demand at date `t` in the same series)

| Group | Feature | Definition |
|---|---|---|
| Categorical | `hub_id`, `crop_id` | LightGBM categorical |
| Calendar | `dow`, `month`, `week_of_year`, `is_weekend`, `doy_sin`, `doy_cos` | from `d` |
| Lags | `lag_7`, `lag_14`, `lag_28` | `x[d−7]`, `x[d−14]`, `x[d−28]` |
| Rolling (shifted) | `roll_mean_7`, `roll_std_7`, `roll_mean_28` | mean/std over `x[d−13 … d−7]` and mean over `x[d−34 … d−7]` |
| Price | `price_lag_7`, `price_roll_mean_7`, `price_change_7` | `p[d−7]`; mean `p[d−13 … d−7]`; `p[d−7]/p[d−14] − 1` |

Excluded on purpose: festival/holiday flags (no sourced calendar; FUTURE), weather (no data), same-day price (unknown in the future).

**Leakage rule (tested):** features for `d` computed from a series truncated at `d−7` must equal features computed from the full series (AC-FC-04).

## 5. Baselines, models, selection, deployment gate

| Model | Role |
|---|---|
| B1 Seasonal naive | `ŷ[d] = x[d−7]` — mandatory baseline and runtime **fallback** |
| B2 Trailing mean | mean of `x[d−13 … d−7]` |
| RF | `RandomForestRegressor(n_estimators=200, min_samples_leaf=5)` — comparison only (NICE), not deployed |
| **LGBM-point** | `LGBMRegressor(objective="regression", n_estimators≤800, learning_rate=0.05, num_leaves=31, min_child_samples=20, subsample/colsample 0.8)`, early stopping on validation |
| **LGBM-q10 / LGBM-q90** | same features, `objective="quantile"`, `alpha=0.1 / 0.9` |

No large hyper-parameter search (small grid over `num_leaves ∈ {15,31,63}` is allowed, chosen on validation MAE only).

**Deployment gate (honesty control):** deploy LightGBM only if `val_MAE(LGBM) < 0.95 × min(val_MAE(B1), val_MAE(B2))` **and** `test_MAE(LGBM) < min(test_MAE(B1), test_MAE(B2))`. Otherwise `model_card.deployed_method = "SEASONAL_NAIVE"` and the UI shows the fallback label. After the gate passes, the point and quantile models are **refit on train+validation ONLY** for deployment (the held-out test set is strictly excluded from training); reported metrics are from the validation and held-out test splits.

## 6. Evaluation metrics

Reported overall and per crop, on validation and test, for baselines and LightGBM:

| Metric | Definition |
|---|---|
| MAE | mean |y − ŷ| (kg/day) |
| RMSE | sqrt(mean (y − ŷ)²) |
| WAPE (primary %) | Σ|y − ŷ| / Σ y |
| MAPE | mean |y − ŷ|/y over rows with y ≥ 10 kg (guards divide-by-near-zero); secondary |
| Bias | mean(ŷ − y) |
| Interval coverage | share of test rows with q10 ≤ y ≤ q90 (nominal 80%) — reported as measured, **not** claimed calibrated |

### Measured Results (`python -m ml.train` on Dataset DS-01)

- Dataset SHA256: `212f40084745d2e23e69e35ecc812b77c5164e4a96fba155aa7ffdad0139b755`
- Model Version: `1.0.0`
- Deployed Method: `LIGHTGBM`
- Deployed Scope: `TRAIN_PLUS_VALIDATION_ONLY`
- Deployment Gate: **PASSED** (val_MAE 105.42 < 127.81 threshold; test_MAE 104.66 < 126.45 baseline)

| Split | Model | MAE (kg/d) | RMSE (kg/d) | WAPE % | MAPE % | Bias | 80% Coverage |
|---|---|---|---|---|---|---|---|
| Validation | **LightGBM** | **105.42** | 165.91 | 10.62% | 11.16% | -8.57 | 77.91% |
| Validation | B1 Seasonal Naive | 142.89 | 230.39 | 14.40% | 14.91% | 12.57 | — |
| Validation | B2 Trailing Mean | 134.54 | 212.54 | 13.56% | 14.32% | 14.64 | — |
| Test (Held-out) | **LightGBM** | **104.66** | 173.67 | 11.12% | 10.65% | -13.62 | 79.62% |
| Test (Held-out) | B1 Seasonal Naive | 137.55 | 226.63 | 14.62% | 14.11% | 3.81 | — |
| Test (Held-out) | B2 Trailing Mean | 126.45 | 202.99 | 13.44% | 13.62% | 11.97 | — |

Per-crop held-out test performance (LGBM):
- Tomato: MAE 89.50 kg/d, WAPE 9.77%, 80% Coverage 81.29%
- Onion: MAE 197.61 kg/d, WAPE 11.61%, 80% Coverage 72.66%
- Potato: MAE 190.60 kg/d, WAPE 11.58%, 80% Coverage 74.10%
- Cauliflower: MAE 27.76 kg/d, WAPE 10.36%, 80% Coverage 84.17%
- Green Chilli: MAE 15.90 kg/d, WAPE 10.18%, 80% Coverage 86.03%

## 7. Confidence / uncertainty

80% prediction interval = [q10, q90] from quantile models. Post-processing: clip ≥ 0, enforce `q10 ≤ ŷ ≤ q90` by sorting the triple. UI shows a band; fallback method returns no interval (`lo/hi = null`).

## 8. Inference flow

```
GET /forecasts/demand?hub_id&crop_id&horizon_days
 1. validate hub/crop → 404
 2. load last ≥35 days of demand_history for the pair (DB)        # <14 days → 422 INSUFFICIENT_HISTORY
 3. if artifacts loaded and ≥35 days and deployed_method==LIGHTGBM:
        build features for T+1..T+h → predict point,q10,q90 → post-process
    elif ≥14 days: seasonal-naive fallback (method=SEASONAL_NAIVE_FALLBACK)
 4. return {history(last 28d), forecast[h], method, model_version, data_source:"SYNTHETIC", disclaimer}
```
Any exception in steps 3 falls through to the fallback and is logged (AC-FC-02). In-memory LRU cache keyed `(hub,crop,T,h)`.

## 9. Matching engine (deterministic)

**Inputs:** a requirement `R` (crop, grade_min, Q, P_max, needed_by, buyer location, buyer hub); all `ACTIVE`, unexpired listings `L` of that crop.

**Hard filters** (a failing candidate is not allocated; the first failed rule is returned as `excluded_reason` in `near_misses`):

| # | Rule |
|---|---|
| F1 | `L.status=ACTIVE`, `available_until ≥ today`, `available_qty ≥ 1` |
| F2 | `grade(L) ≥ R.grade_min` (A>B>C) |
| F3 | `road_distance ≤ max_match_distance_km` *(cfg 300)* |
| F4 | `earliest_delivery = max(today, available_from) + floor(transit_hours/24) days ≤ needed_by` |
| F5 | `age_at_delivery = (earliest_delivery − harvest_date) days ≤ crop.shelf_life_days` and `transit_hours ≤ crop.max_transit_hours` |
| F6 | `landed ≤ P_max`, where `landed = ask + transport_per_kg + fee_per_kg`, transport from §11 for the quantity that would be allocated (`min(available, Q)`) |

**Score** (0–1), weights *(cfg)* `w_price 0.40, w_dist 0.20, w_fresh 0.20, w_fill 0.20`:

```
price_score = clamp((1 − landed/P_max) / price_headroom, 0, 1)        # headroom 0.30
dist_score  = clamp(1 − distance_km / max_match_distance_km, 0, 1)
fresh_score = clamp(1 − age_at_delivery / crop.shelf_life_days, 0, 1)
fill_score  = min(available_qty, Q) / Q
score       = w_price·price_score + w_dist·dist_score + w_fresh·fresh_score + w_fill·fill_score
```
Each candidate returns the four factor values, the weights, `landed` breakdown and `reasons[]` (e.g., "Nearest eligible source (58 km est.)", "Landed ₹25.6/kg is 11.7% below your ₹29.0 budget"). Reasons are generated from numbers, never free text from a model.

**Allocation (greedy, deterministic):** sort by score desc (tie-break: lower landed, then lower `listing_id`). `remaining = Q`. For each candidate: `q = min(available, remaining)`; if `q < L.min_order_kg` skip with reason `BELOW_MIN_ORDER`; else allocate and `remaining −= q`; stop at 0. Result: `allocations[]`, `fulfilled_kg`, `shortfall_kg`, `fill_status ∈ {FULL, PARTIAL, NONE}`. `near_misses[]` (max 5) explains the best excluded candidates.

Known limitation: greedy per requirement is not globally optimal across requirements; global min-cost-flow is FUTURE.

**Accept:** server recomputes candidates, verifies each submitted `(listing_id, quantity_kg)` is still feasible and within availability, then in one transaction reserves quantity and creates orders (`origin=MATCHING`, status `PLACED`). Any failure → `409 STALE_ALLOCATION`, nothing written.

**Producer opportunities:** same scoring applied in reverse — for a listing, list compatible open requirements ranked by score (read-only) plus hub forecast context.

## 10. Route optimization (OR-Tools)

**Problem:** given confirmed, unrouted orders and available vehicles (with depots), build routes minimising total cost, subject to capacity, route duration, pickup-before-drop on the same vehicle; drop infeasible orders into `unassigned`.

1. **Chunking:** each order → chunks of `≤ min(largest available vehicle capacity, max_order_chunk_kg)`; each chunk = one pickup/drop request.
2. **Nodes:** one start/end per vehicle at its depot (closed routes); a pickup and a drop node per chunk.
3. **Distances:** `distance_km(i,j)` from `routes/distance.py` (haversine × circuity, or OSRM table for ≤25 nodes with fallback); converted to integer meters.
4. **Time dimension:** `travel_min = km / speed·60`; `service_minutes_per_stop` added at pickup and drop; per-vehicle `max_route_minutes` *(cfg 600)*.
5. **Capacity dimension:** +q at pickup, −q at drop; capacity = `vehicle.capacity_kg`.
6. **Pairing:** `AddPickupAndDelivery(p,d)`; `VehicleVar(p) == VehicleVar(d)`; `CumulVar_time(p) ≤ CumulVar_time(d)`.
7. **Perishability (SHOULD):** `time(d) − time(p) ≤ crop.max_transit_hours·60`.
8. **Cost:** arc cost per vehicle = `round(cost_per_km · km(i,j) · 100)` (paise); `SetFixedCostOfVehicle(round(fixed·100))`.
9. **Disjunction:** every pickup/drop pair optional with penalty = `max(10 × baseline chunk cost, 1_000_000)` paise so dropping is chosen only when infeasible.
10. **Search:** first solution `PATH_CHEAPEST_ARC`; local search `GUIDED_LOCAL_SEARCH`; time limit = request value (default 5 s, max 30 s). Exact OR-Tools API names are verified against the installed version during Phase 8.
11. **Output:** per used vehicle: ordered stops, load after each stop, cumulative km, ETA (minutes from start), cost; plan totals; `unassigned[]` with reason ∈ `CAPACITY | DURATION | NO_FEASIBLE_INSERTION`.
12. **Baseline (FR-81):** each order as its own dedicated round trip from the pickup point using §11 (`2 × direct km` × vehicle rate + fixed, multi-trip if needed). `savings = baseline − optimized` for km and ₹. **The baseline models uncoordinated transport; it is not measured reality.** If savings are ≤ 0 the UI says so.
13. **Cost allocation to orders:** route cost split across the orders it serves in proportion to `qty × direct_km` (kg-km). Stored at approval in `orders.allocated_transport_cost_total`.
14. **Fallback (`GREEDY_FALLBACK`):** sort chunks by descending direct distance; insert each at the cheapest feasible position in existing routes (capacity + duration); else open the cheapest fitting unused vehicle; else unassigned.
15. **Limits:** ≤ 40 orders and ≤ 10 vehicles per run (422 otherwise). Mixed crops share vehicles (A-07).

## 11. Logistics cost model (single order / chunk)

```
distance_km      = haversine_km(a,b) × circuity                      # 1.35 (cfg) ; or OSRM road km
vehicle_plan(q)  : if q ≤ max_cap → smallest type with cap ≥ q (1 trip)
                   else n_full = floor(q / max_cap) trips of the largest type
                        + (remainder r > 0 → smallest type with cap ≥ r)
trip_cost(type)  = fixed_cost + cost_per_km × distance_km × return_leg_factor      # factor 2.0 (cfg)
cost_total       = Σ trip_cost ;  cost_per_kg = cost_total / q
transit_hours    = distance_km / avg_speed_kmph + (2 × service_minutes)/60       # one-way, 30 km/h (cfg)
```
Requires ≥1 available vehicle in the fleet or returns `409 NO_VEHICLE_AVAILABLE`. Distances are **estimates**, always labelled with `distance_source`.

## 12. Pricing formulas (price transparency)

```
fee_per_kg          = farmgate × platform_fee_pct/100                 # 2.0 (cfg), paid by buyer
transport_per_kg    = allocated_route_cost/qty  (if plan approved)  else §11 estimate
landed              = farmgate + transport_per_kg + fee_per_kg
benchmark_modal     = latest market_prices.modal for (buyer hub | nearest hub of producer, crop)
farmer_mandi_net    = benchmark_modal × (1 − commission_agent_pct/100) − producer_to_hub_transport_per_kg
buyer_traditional   = benchmark_modal × (1 + trader_margin_pct/100) × (1 + retail_margin_pct/100) + last_mile_cost_per_kg
Δfarmer_pct         = (farmgate − farmer_mandi_net) / farmer_mandi_net
Δbuyer_pct          = (landed − buyer_traditional) / buyer_traditional       # negative = cheaper
fair_band           = [ L = farmer_mandi_net ,  U = (buyer_traditional − transport_per_kg) / (1 + fee_pct/100) ]   # null if U ≤ L
```
Every output of this section is a **modelled scenario** using disclosed assumptions (Research F-1/F-3 motivate magnitudes only) and carries `basis:"MODELLED_SCENARIO"`. It is never phrased as a measured saving.

## 13. Hub ranking and supply-vs-demand

```
forecast_7d(h,c)   = Σ forecast ŷ over T+1..T+7
supply(h,c)        = Σ available_qty of ACTIVE listings of crop c whose producer's nearest hub is h
ratio              = supply / forecast_7d            → SHORTAGE if < 0.7 ; SURPLUS if > 1.3 ; else BALANCED   (cfg)
# for a producer deciding where to sell (quantity q):
demand_index       = clamp( forecast_7d / max(supply + q, 1) , 0, 2) / 2
net_realisation    = benchmark_modal(h,c) − transport_per_kg(producer→hub centre, q)       # indicative
opportunity_score  = 0.5·demand_index + 0.5·minmax(net_realisation across hubs)
```
Each listing is attributed to its nearest hub to avoid double counting. `net_realisation` is labelled *indicative* (uses the benchmark, not a buyer's price).

## 14. Retraining and model lifecycle

Manual only: `python -m ml.train` (≈ minutes). Triggers: generator config change, new real data (FUTURE). No scheduled or online retraining. Each run overwrites artifacts and `model_card.json`; commit artifacts after a successful run and tag.

## 15. Model storage and model card

`backend/ml/artifacts/`: `model_point.joblib`, `model_q10.joblib`, `model_q90.joblib`, `feature_spec.json`, `model_card.json`.

`model_card.json` fields: `model_version` (timestamp+seed), `trained_at`, `data_source:"SYNTHETIC"`, `generator_version`, `data_range`, `splits{train,val,test ranges}`, `baselines{metrics}`, `lightgbm{val_metrics,test_metrics,coverage_80}`, `rf_reference{metrics}`, `deployed_method`, `gate{passed,reason}`, `disclaimer`.

## 16. API interface (summary — contracts in API.md)

`GET /forecasts/demand`, `GET /forecasts/hubs`, `GET /forecasts/model-info`. Responses always include `data_source:"SYNTHETIC"`, `method`, `model_version`, `disclaimer`.

## 17. Failure handling

| Failure | Behaviour |
|---|---|
| Artifacts missing/corrupt | Fallback seasonal-naive, `method="SEASONAL_NAIVE_FALLBACK"`, warning logged, UI label |
| History 14–34 days | Fallback |
| History < 14 days | 422 `INSUFFICIENT_HISTORY` |
| Gate failed at training | `deployed_method="SEASONAL_NAIVE"`; honest label |
| LightGBM import error at runtime | Fallback |
| Solver no solution / exception | `GREEDY_FALLBACK`; if that also fails `500 OPTIMIZATION_FAILED` |
| OSRM failure | haversine, `distance_source="ESTIMATED_HAVERSINE"` |

## 18. Non-goals for ML

No LSTM/Transformer, no AutoML, no recommender, no LLM agents, no ML-based matching, no claims of real-world accuracy.
