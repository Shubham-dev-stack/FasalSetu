# API — KrishiSetu backend contracts

Status: PLANNED. Base path `/api/v1`. Matches Architecture.md §4/§11/§13 and Data.md §6–§8. If an endpoint is not here, it does not exist (Rules C-7). JSON bodies shown are **shape examples; values are illustrative, not system output.**

## 0. Conventions

| Item | Rule |
|---|---|
| Auth | `Authorization: Bearer <JWT>`; "Public" = no token |
| Content | `application/json`; dates `YYYY-MM-DD` (IST), timestamps ISO-8601 UTC |
| Money / qty | ₹ with 2 decimals; kg with ≤1 decimal |
| Lists | `?limit` (default 50, max 200), `?offset`; response `{ "items": [...], "total": n }` |
| Errors | Envelope `{ "error": { "code", "message", "details": [{"field","issue"}] } }` — codes in Architecture.md §13 plus `STALE_PLAN` (409) |
| Data labels | Any forecast/price response carries `data_source` and/or `basis` (`SYNTHETIC`, `MODELLED_SCENARIO`, `ESTIMATE`) |
| Priority | M = MUST, S = SHOULD (Phases.md §15) |

Common errors on every authenticated endpoint: `401 UNAUTHENTICATED`, `403 FORBIDDEN`, `422 VALIDATION_ERROR`, `503 DATABASE_UNAVAILABLE`, `500 INTERNAL_ERROR`. Only endpoint-specific errors are listed below.

Endpoint index (42): system 2 · auth 4 · reference 1 · profiles 4 · listings 4 · requirements 4 · orders 4 · forecasts 3 · matching 3 · logistics 2 · routes 7 · pricing 2 · analytics 2.

---

## 1. System

| M/S | Method & path | Auth | Purpose | Request | Response | Errors | Tables |
|---|---|---|---|---|---|---|---|
| M | `GET /health` | Public | Liveness + dependency status | — | `{status:"ok", db:"ok"\|"error", model:{loaded:bool, deployed_method}, demo_mode:bool, version}` | — | (ping) |
| M | `POST /system/reset-demo` | ADMIN, `DEMO_MODE=true` | Drop/recreate tables and reseed deterministic demo data | — | `{status:"reset", counts:{users, listings, requirements, orders, ...}}` | 404 `DEMO_DISABLED` | all |

## 2. Auth

| M/S | Method & path | Auth | Purpose | Request | Response | Validation / errors | Tables |
|---|---|---|---|---|---|---|---|
| M | `POST /auth/login` | Public | Email+password login | `{email, password}` | `{access_token, token_type:"bearer", expires_in, user:{id,email,role,display_name,profile_id}}` | 401 `UNAUTHENTICATED` on bad credentials (same message for unknown email/wrong password) | users |
| M | `GET /auth/me` | Any | Current user | — | `user` object as above | — | users, *_profiles |
| M | `POST /auth/demo-login` | Public, `DEMO_MODE=true` | Token for a seeded persona | `{persona}` ∈ `fpo_sonipat, fpo_meerut, farmer_karnal, buyer_gurugram, buyer_noida, operator` | same as login | 404 `DEMO_DISABLED`; 422 unknown persona | users |
| S | `POST /auth/register` | Public | Create producer or buyer account with profile | `{email, password(≥8), role:"PRODUCER"\|"BUYER", display_name, profile:{producer_type\|buyer_type, org_name, state, district, lat, lng, hub_id?(buyer), member_farmers?}}` | 201 login-shaped response | 409 email exists; 422 invalid location (India bounding box) | users, profiles |

## 3. Reference

| M | `GET /reference` | Any | Static lookups | — | `{crops:[{id,name,category,shelf_life_days,max_transit_hours,perishability}], hubs:[{id,name,city,state,lat,lng}], enums:{grades, listing_status, requirement_status, order_status, producer_type, buyer_type, vehicle_type}, public_config:{platform_fee_pct, max_match_distance_km, forecast_horizon_days:7, demo_mode}}` | — | crops, demand_hubs |

## 4. Profiles

| M/S | Method & path | Auth | Request → Response | Validation | Tables |
|---|---|---|---|---|---|
| M | `GET /producers/me` | PRODUCER | → producer profile | — | producer_profiles |
| M | `PATCH /producers/me` | PRODUCER | `{org_name?, state?, district?, locality?, lat?, lng?, member_farmers?}` → profile | lat/lng bounding box; `member_farmers` ≥1, FPO only | producer_profiles |
| M | `GET /buyers/me` | BUYER | → buyer profile (incl. `hub`) | — | buyer_profiles |
| M | `PATCH /buyers/me` | BUYER | `{org_name?, city?, state?, lat?, lng?, hub_id?}` → profile | hub exists | buyer_profiles |

## 5. Listings

**Listing object:** `{id, producer:{id,org_name,producer_type,district,state,lat,lng}, crop:{id,name}, variety, grade, quantity_kg, quantity_available_kg, ask_price_per_kg, min_order_kg, harvest_date, available_from, available_until, status, is_demo, harvest_age_days, landed_estimate:{distance_km, distance_source, transport_cost_per_kg, platform_fee_per_kg, landed_price_per_kg, basis:"ESTIMATE"}|null, demand_status:"SHORTAGE"|"BALANCED"|"SURPLUS"|null, created_at}`

| M/S | Method & path | Auth | Purpose | Request | Response | Validation / errors | Tables |
|---|---|---|---|---|---|---|---|
| M | `POST /listings` | PRODUCER | Create listing | `{crop_id, variety?, grade, quantity_kg, ask_price_per_kg, min_order_kg, harvest_date, available_from, available_until}` | 201 `{listing, warnings:[]}`; warning `PRICE_FAR_ABOVE_BENCHMARK` when ask > 3× benchmark | Data.md §8: quantity 0<q≤100000; price 0<p≤100000; `min_order≤quantity`; `harvest_date` in [today−30, today]; `from≤until`; `until≥today`; crop exists | listings, crops, market_prices |
| M | `GET /listings` | Any | Marketplace browse / own listings | Query: `crop_id, grade_min, state, max_price, harvested_within_days, status(default ACTIVE), mine(bool, PRODUCER), sort(landed\|price\|distance\|freshness), buyer_lat, buyer_lng, limit, offset`. BUYER callers get `landed_estimate` using profile location; others need `buyer_lat/lng` | `{items:[Listing], total}`; expired/sold-out excluded unless `status` says otherwise | 422 on bad enum/range | listings, producer_profiles, crops |
| S | `GET /listings/{id}` | Any | Detail | — | Listing (+ same landed/demand fields) | 404 | listings |
| M | `PATCH /listings/{id}` | PRODUCER (owner) | Edit or withdraw | `{ask_price_per_kg?, quantity_kg?, min_order_kg?, available_until?, status?:"WITHDRAWN"}` | Listing | 403 not owner; `quantity_kg` cannot drop below already reserved (`quantity_kg − quantity_available_kg`); cannot edit SOLD_OUT/EXPIRED except withdraw; 409 `LISTING_UNAVAILABLE` if not editable | listings |

## 6. Requirements

**Requirement object:** `{id, buyer:{id,org_name,hub}, crop:{id,name}, grade_min, quantity_kg, quantity_fulfilled_kg, max_landed_price_per_kg, needed_by, status, notes, is_demo, created_at}`

| M/S | Method & path | Auth | Request → Response | Validation / errors | Tables |
|---|---|---|---|---|---|
| M | `POST /requirements` | BUYER | `{crop_id, grade_min, quantity_kg, max_landed_price_per_kg, needed_by, notes?}` → 201 Requirement | quantity 0<q≤100000; price 0<p≤100000; `needed_by ≥ today`; crop exists | requirements |
| M | `GET /requirements` | BUYER (own) / ADMIN (all) | Query `status, crop_id, limit, offset` → `{items,total}` | — | requirements |
| M | `GET /requirements/{id}` | owner BUYER / ADMIN | → Requirement | 403 not owner; 404 | requirements |
| M | `PATCH /requirements/{id}` | owner BUYER | `{quantity_kg?, max_landed_price_per_kg?, needed_by?, status?:"CANCELLED"}` → Requirement | quantity cannot drop below `quantity_fulfilled_kg`; cannot edit CANCELLED/FULFILLED/EXPIRED | requirements |

## 7. Orders

**Order object:** `{id, listing_id, requirement_id|null, buyer:{id,org_name}, producer:{id,org_name}, crop:{id,name}, quantity_kg, agreed_price_per_kg, transport_cost_estimate_per_kg, platform_fee_per_kg, landed_price_per_kg_estimate, delivery_date, status, origin, shipment_id|null, allocated_transport_cost_total|null, events:[{from_status,to_status,actor_role,at,note}], is_demo, created_at}`

| M/S | Method & path | Auth | Purpose | Request | Response | Validation / errors | Tables |
|---|---|---|---|---|---|---|---|
| S | `POST /orders` | BUYER | Direct order from a listing (marketplace) | `{listing_id, quantity_kg, delivery_date}` | 201 Order (`status:PLACED`, `origin:MARKETPLACE`) | `quantity_kg ≥ min_order_kg` (422); `≤ available` else 409 `INSUFFICIENT_QUANTITY`; listing not ACTIVE/expired → 409 `LISTING_UNAVAILABLE`; `delivery_date ≥ today`. Reservation is one atomic conditional UPDATE | orders, listings, order_events, requirements |
| M | `GET /orders` | Any (scoped: PRODUCER own, BUYER own, ADMIN all) | List | Query `status, crop_id, limit, offset` | `{items:[Order],total}` | — | orders |
| M | `GET /orders/{id}` | party / ADMIN | Detail with events | — | Order | 403/404 | orders, order_events |
| M | `POST /orders/{id}/transition` | see matrix | Change status | `{to_status, note?}` | Order | 409 `INVALID_TRANSITION`; 403 role | orders, listings, requirements, order_events |

Transition matrix (endpoint accepts only these `to_status`; `IN_TRANSIT` and `DELIVERED` are set exclusively by shipment transitions, §11):

| From → To | Allowed actor | Side effects |
|---|---|---|
| PLACED → CONFIRMED | owning PRODUCER, ADMIN (override) | event logged |
| PLACED → REJECTED | owning PRODUCER, ADMIN | release reserved qty; recompute requirement fulfilment |
| PLACED → CANCELLED | owning BUYER, ADMIN | release qty; recompute fulfilment |
| CONFIRMED → CANCELLED | owning BUYER, owning PRODUCER, ADMIN — only while `shipment_id` is null | release qty; recompute |

Releasing quantity restores `quantity_available_kg` (and `ACTIVE` if it was `SOLD_OUT` and not expired).

## 8. Demand forecasts

| M/S | Method & path | Auth | Purpose | Request | Response | Errors | Tables |
|---|---|---|---|---|---|---|---|
| M | `GET /forecasts/demand` | Any | Hub × crop forecast | Query `hub_id, crop_id, horizon_days (1–7, default 7)` | `{hub:{id,name}, crop:{id,name}, as_of_date, horizon_days, method:"LIGHTGBM"\|"SEASONAL_NAIVE_FALLBACK", model_version, data_source:"SYNTHETIC", disclaimer, history:[{date,demand_kg}] (28 d), forecast:[{date,yhat_kg,lo_kg,hi_kg}], summary:{forecast_total_kg, previous_period_kg, change_pct}}` (fallback: `lo_kg/hi_kg` null) | 404 hub/crop; 422 `INSUFFICIENT_HISTORY` (<14 days) | demand_history, crops, demand_hubs |
| M | `GET /forecasts/hubs` | Any | Rank hubs for a crop (PREDICT panel) | Query `crop_id, quantity_kg?, lat?, lng?` (PRODUCER callers default to profile location; others must pass lat/lng) | `{crop, as_of_date, method, data_source:"SYNTHETIC", hubs:[{hub, distance_km, distance_source, forecast_7d_kg, supply_kg, ratio, status:"SHORTAGE"\|"BALANCED"\|"SURPLUS", benchmark_modal_per_kg\|null, benchmark_source, transport_cost_per_kg, net_realisation_per_kg:"indicative", opportunity_score}]}` sorted by `opportunity_score` desc | 404 crop; 422 missing location | demand_history, demand_hubs, listings, market_prices |
| M | `GET /forecasts/model-info` | Any | Model card | — | contents of `model_card.json` (ML.md §15) incl. `data_source:"SYNTHETIC"`, `deployed_method`, metrics, `disclaimer` | 404 if no card (fallback-only deployment returns a card stating so) | (file) |

## 9. Matching

| M/S | Method & path | Auth | Purpose | Request | Response | Errors | Tables |
|---|---|---|---|---|---|---|---|
| M | `GET /matching/requirements/{id}/candidates` | owner BUYER / ADMIN | Ranked, explained candidates + allocation plan | Query `max_results` (default 10, max 25) | see below | 404; 403 | requirements, listings, producer_profiles, crops |
| M | `POST /matching/accept` | BUYER (owner) | Create orders from an allocation | `{requirement_id, allocations:[{listing_id, quantity_kg}], delivery_date}` | 201 `{orders:[Order], requirement:{id,status,quantity_fulfilled_kg}}` | 409 `STALE_ALLOCATION` (any line no longer feasible; nothing written); 422 empty allocations / `Σ qty > remaining` / below min order | orders, listings, requirements, order_events |
| S | `GET /matching/listings/{id}/opportunities` | owner PRODUCER / ADMIN | Compatible open requirements for a listing (read-only) | Query `limit` | `{listing, opportunities:[{requirement, buyer:{id,org_name,buyer_type}, distance_km, landed_price_per_kg, scores, reasons:[]}], hub_context:{hub, forecast_7d_kg, status}}` | 403/404 | listings, requirements |

**Candidates response:**
```json
{
  "requirement": { "id": 1, "crop": {"id":1,"name":"Tomato"}, "grade_min":"B", "quantity_kg":1500, "max_landed_price_per_kg":29.00, "needed_by":"2026-10-02" },
  "fill_status": "FULL",                      // FULL | PARTIAL | NONE
  "requested_kg": 1500, "fulfilled_kg": 1500, "shortfall_kg": 0,
  "earliest_delivery_date": "2026-10-01",
  "allocations": [ { "listing_id": 15, "quantity_kg": 1500 } ],
  "candidates": [ {
     "rank": 1, "listing": { "id":15, "producer":{"id":1,"org_name":"…"}, "grade":"A", "ask_price_per_kg":23.00, "harvest_date":"…" },
     "available_kg": 2000, "allocated_kg": 1500,
     "distance_km": 0.0, "distance_source": "ESTIMATED_HAVERSINE", "transit_hours": 0.0, "age_at_delivery_days": 0,
     "ask_price_per_kg": 0.0, "transport_cost_per_kg": 0.0, "platform_fee_per_kg": 0.0, "landed_price_per_kg": 0.0,
     "scores": { "price":0.0, "distance":0.0, "freshness":0.0, "fill":0.0, "total":0.0 },
     "weights": { "price":0.40, "distance":0.20, "freshness":0.20, "fill":0.20 },
     "reasons": ["…generated from numbers…"]
  } ],
  "near_misses": [ { "listing_id": 4, "excluded_reason": "BUDGET", "detail": "Landed ₹x is ₹y over budget", "landed_price_per_kg": 0.0 } ]
}
```
`excluded_reason` ∈ `BUDGET | GRADE | DISTANCE | FRESHNESS | AVAILABILITY | BELOW_MIN_ORDER`. (Numeric zeros above are placeholders for the shape.)

## 10. Logistics

| M/S | Method & path | Auth | Purpose | Request | Response | Errors | Tables |
|---|---|---|---|---|---|---|---|
| M | `POST /logistics/estimate` | Any | Dedicated-trip estimate (ML.md §11) | `{listing_id, quantity_kg, buyer_id?` **or** `dest_lat, dest_lng}` (BUYER default = own profile) | `{distance_km, distance_source, vehicle_plan:[{vehicle_type, capacity_kg, load_kg, trip_cost}], trips, cost_total, cost_per_kg, transit_hours, basis:"ESTIMATE"}` | 404 listing; 409 `NO_VEHICLE_AVAILABLE`; 422 quantity | listings, producer_profiles, vehicles |
| M | `GET /logistics/vehicles` | Any | Fleet | — | `{items:[{id,name,vehicle_type,capacity_kg,cost_per_km,fixed_cost_per_trip,avg_speed_kmph,depot_name,depot_lat,depot_lng,is_available,is_demo}]}` | — | vehicles |

## 11. Routes (ADMIN only unless stated)

| M/S | Method & path | Auth | Purpose | Request | Response | Errors | Tables |
|---|---|---|---|---|---|---|---|
| M | `POST /routes/optimize` | ADMIN | Solve and store a PROPOSED plan | `{order_ids?: int[] (default: all CONFIRMED unrouted orders; max 40), time_limit_s?: 1–30 (default 5), distance_mode?: "HAVERSINE"\|"OSRM"}` | 201 Plan (below) | 422 `NO_ELIGIBLE_ORDERS`; 422 >40 orders; 409 `NO_VEHICLE_AVAILABLE`; 500 `OPTIMIZATION_FAILED` (after fallback also failed) | orders, vehicles, route_plans |
| M | `GET /routes/plans` | ADMIN | List plans | `limit, offset` | `{items:[{plan_id,status,created_at,method,num_orders,num_unassigned,optimized_km,optimized_cost,baseline_cost}],total}` | — | route_plans |
| M | `GET /routes/plans/{plan_id}` | ADMIN (PRODUCER/BUYER: only if they own an order in an APPROVED plan; response then limited to their stops) | Plan detail | — | Plan | 404 | route_plans, shipments, shipment_stops |
| M | `POST /routes/plans/{plan_id}/approve` | ADMIN | Create shipments/stops, link orders | — | `{plan, shipments:[Shipment]}` | 409 `INVALID_TRANSITION` (not PROPOSED); 409 `STALE_PLAN` (an order no longer CONFIRMED/unrouted) | route_plans, shipments, shipment_stops, orders |
| M | `POST /routes/plans/{plan_id}/discard` | ADMIN | Discard PROPOSED plan (orders untouched) | — | plan | 409 `INVALID_TRANSITION` | route_plans |
| M | `GET /routes/shipments/{shipment_id}` | ADMIN / party with an order in it | Shipment with stops and orders | — | Shipment | 404 | shipments, shipment_stops |
| S | `POST /routes/shipments/{shipment_id}/transition` | ADMIN | Manual status | `{to_status:"DISPATCHED"\|"DELIVERED"}` | Shipment | 409 `INVALID_TRANSITION` (PLANNED→DISPATCHED→DELIVERED only). DISPATCHED sets its orders `CONFIRMED→IN_TRANSIT`; DELIVERED sets `IN_TRANSIT→DELIVERED`. **Manual — no tracking.** | shipments, orders, order_events |

**Plan object:**
```json
{
  "plan_id": "uuid", "status": "PROPOSED", "method": "ORTOOLS",       // ORTOOLS | GREEDY_FALLBACK
  "solver_status": "…", "solve_time_ms": 0, "distance_source": "ESTIMATED_HAVERSINE",  // | OSRM_ROAD
  "totals": { "optimized_km":0, "optimized_cost":0, "baseline_km":0, "baseline_cost":0,
              "savings_km":0, "savings_cost":0, "savings_pct_cost":0, "vehicles_used":0, "avg_utilization_pct":0 },
  "baseline_note": "Baseline = each order shipped on its own dedicated round trip (modelled, not measured).",
  "shipments": [ {
      "temp_id": "s1", "shipment_id": null,                           // set after approval
      "vehicle": {"id":1,"name":"MT-01","vehicle_type":"MINI_TRUCK","capacity_kg":750},
      "total_distance_km":0, "total_cost":0, "peak_load_kg":0, "utilization_pct":0, "est_duration_min":0,
      "stops": [ {"sequence":0,"stop_type":"DEPOT_START","order_id":null,"label":"…","lat":0,"lng":0,"load_after_kg":0,"cum_distance_km":0,"eta_min_from_start":0} ],
      "geometry": [[0,0]]                                              // schematic polyline (or road geometry if OSRM)
  } ],
  "unassigned": [ {"order_id": 0, "quantity_kg": 0, "reason": "CAPACITY"} ],   // CAPACITY | DURATION | NO_FEASIBLE_INSERTION
  "skipped_order_ids": [], "warnings": []
}
```
Only `APPROVED` plans count in analytics.

## 12. Pricing (price transparency)

| M/S | Method & path | Auth | Purpose | Request | Response | Errors | Tables |
|---|---|---|---|---|---|---|---|
| M | `GET /pricing/breakdown` | party / ADMIN | Waterfall for one order | Query `order_id` | `{order_id, crop, quantity_kg, per_kg:{farmgate, transport, platform_fee, landed}, transport_basis:"ALLOCATED_ROUTE"\|"ESTIMATE", benchmark:{hub, market_name, price_date, modal_price_per_kg, min_price_per_kg, max_price_per_kg, source:"SYNTHETIC_DEMO"\|"AGMARKNET_SNAPSHOT", is_synthetic}\|null, scenario:{farmer_mandi_net_per_kg, buyer_traditional_per_kg, delta_farmer_pct, delta_buyer_pct, assumptions:{platform_fee_pct, commission_agent_pct, trader_margin_pct, retail_margin_pct, last_mile_cost_per_kg}}\|null, fair_band:{low,high}\|null, basis:"MODELLED_SCENARIO", disclaimer}` | 404/403; benchmark missing → `benchmark:null, scenario:null` (not an error) | orders, market_prices, route_plans |
| M | `GET /pricing/benchmark` | Any | Benchmark + fair band for the listing form | Query `crop_id` and (`hub_id` **or** `lat,lng`), optional `quantity_kg` (default 1000) | `{hub, benchmark:{…as above}\|null, trend:[{date, modal_price_per_kg}] (30 d), fair_band\|null, assumptions:{…}, basis:"MODELLED_SCENARIO"}` | 404 crop/hub | market_prices, demand_hubs |

## 13. Analytics (read-only, any authenticated role; aggregates are platform-wide)

| M/S | Method & path | Purpose | Response | Tables |
|---|---|---|---|---|
| M | `GET /analytics/overview` | KPIs + series | `{as_of, data_note:"All figures computed from synthetic demo records", kpis:{committed_orders, committed_volume_kg, committed_value_inr, requirement_fill_rate_pct, avg_logistics_cost_per_kg, route_savings_km, route_savings_inr, avg_utilization_pct}, price_gap:{avg_farmer_delta_pct, avg_buyer_delta_pct, orders_considered, basis:"MODELLED_SCENARIO"}, daily:[{date,orders,volume_kg}] (14 d), model:{deployed_method, data_source:"SYNTHETIC"}}` — metrics with no data are `null` (never fabricated), counts are `0` | orders, requirements, route_plans, shipments, market_prices |
| M | `GET /analytics/supply-demand` | Hub × crop gap table (optional `crop_id`) | `{rows:[{hub, crop, forecast_7d_kg, supply_kg, ratio, status}], method, data_source:"SYNTHETIC"}` | listings, demand_history |

KPI definitions: Data.md §7 and Phases.md §12. `committed` = status in {CONFIRMED, IN_TRANSIT, DELIVERED}. `requirement_fill_rate_pct` = Σ fulfilled / Σ requested over non-cancelled requirements. `avg_logistics_cost_per_kg` uses allocated route cost where available else estimate (flagged in a `basis_mix` field). Route metrics count APPROVED plans only.

## 14. Authorization summary (must equal Architecture.md §11)

| Group | PRODUCER | BUYER | ADMIN |
|---|---|---|---|
| auth/reference/health | ✔ | ✔ | ✔ |
| listings write | own | ✘ | ✘ |
| listings read | ✔ | ✔ | ✔ |
| requirements write | ✘ | own | ✘ |
| requirements read | ✘ | own | all |
| orders | own | own | all + override |
| forecasts / pricing / analytics / logistics read | ✔ | ✔ | ✔ |
| matching candidates / accept | ✘ / ✘ | own / own | any / ✘ |
| matching opportunities | own listing | ✘ | any |
| routes write | ✘ | ✘ | ✔ |
| routes read | limited | limited | ✔ |
| system reset | ✘ | ✘ | ✔ (demo) |
