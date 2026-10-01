# PRD — KrishiSetu (working title)

| Field | Value |
|---|---|
| Document | Product Requirements Document |
| Version | 1.0 (documentation session, 2026-10-01) |
| Owner / sole developer | Shubham Kumar |
| Hackathon | Smart India Hackathon 2026 |
| Problem Statement ID | **SIH26033** |
| Title | Multiple intermediaries reduce farmers earnings and increase consumer prices |
| Problem creator | Sarim Moin — Ministry of Consumer Affairs, Food & Public Distribution |
| Department | Ministry of Education's Innovation Cell (MIC) |
| Technology bucket / category | Agriculture, FoodTech & Rural Development / Software |
| Working title | KrishiSetu (placeholder — check for name clashes before any public use) |

**Status vocabulary used in every doc:** `MUST / SHOULD / NICE / FUTURE` (priority) and `PLANNED / MVP / FUTURE` (implementation state). As of this document **nothing is implemented**; every feature is PLANNED.

**SIH26033 link codes** (used to tie each requirement back to the problem statement):

| Code | Meaning (from the official expected solution / benefits) |
|---|---|
| SIH-1 | Digital marketplace connecting farmers/FPOs directly with consumers and bulk buyers |
| SIH-2 | Logistics support |
| SIH-3 | AI for demand forecasting |
| SIH-4 | AI for route optimization |
| SIH-5 | Better prices for farmers |
| SIH-6 | Lower prices for consumers |
| SIH-7 | Reduced supply-chain inefficiencies |

---

## 1. Product overview

KrishiSetu is an **AI-assisted direct agricultural supply-chain coordination platform** — not a generic e-commerce store. It runs one loop:

| Step | Product capability | Module |
|---|---|---|
| **PREDICT** | 7-day demand forecast per demand hub × crop, plus supply-vs-demand signal shown when a producer lists produce | M5 Demand Intelligence |
| **MATCH** | Explainable ranking of listings against a buyer requirement; partial and multi-source allocation | M6 Matching Engine |
| **MOVE** | Transport cost/time estimate per order, then consolidated multi-stop route optimization across orders and vehicles | M7 Logistics, M8 Route Optimization |
| **SELL** | Producer listings, marketplace browse, direct orders, order lifecycle, price transparency waterfall | M2–M4, M9 |
| **ANALYSE** | Supply-chain analytics: fill rate, logistics cost/kg, route savings, modelled price gap vs traditional chain | M10 Analytics |

**Honest framing.** The product does not "eliminate intermediaries". It *unbundles* what intermediaries bundle together — price information, demand discovery, buyer matching, and consolidated transport — into transparent services available directly to farmers/FPOs and buyers (see Research §2 for why this framing is the defensible one).

## 2. Problem statement

As provided by the project owner (verbatim intent): *"Multiple intermediaries reduce farmers earnings and increase consumer prices."* Official expected solution: a digital marketplace that connects farmers/FPOs directly with consumers and bulk buyers, provides logistics support, and uses AI for demand forecasting and route optimization. Expected benefits: better prices for farmers, lower prices for consumers, reduced supply-chain inefficiencies.

> Verification note: a web search in the documentation session did not return the official SIH portal entry for SIH26033. The text above is taken from the owner's brief and is treated as the authoritative scope lock. Re-check against the SIH portal before the final submission (Risk R-12).

## 3. Problem analysis

| # | Root cause | Consequence | Can software help? | Product lever |
|---|---|---|---|---|
| RC-1 | Information asymmetry on prices and demand | Farmers accept whatever price the local trader/agent offers | Yes | Demand forecast + price benchmark + fair price band |
| RC-2 | Small, scattered lots; weak aggregation | High per-kg transport and handling cost; low bargaining power | Partly (FPO aggregation is organizational) | FPO-first listings; consolidated routing |
| RC-3 | Fragmented logistics, empty return trips, small vehicles | High transport cost/kg | Yes | Logistics estimate + OR-Tools consolidation |
| RC-4 | Perishability and time pressure | Forced sales at poor prices | Partly | Freshness-aware matching, shelf-life filters |
| RC-5 | Thin buyer discovery (who needs what, when) | Produce goes to nearest trader, not best buyer | Yes | Requirements board + matching |
| RC-6 | Multi-layer margins invisible to both ends | Neither side can see where the price went | Yes | Price transparency waterfall (modelled) |
| RC-7 | Credit dependence, trust, cold storage, quality grading | Farmers tied to agents for credit | **No** (out of scope) | Explicitly excluded (see §11) |

RC-7 matters: intermediaries also provide credit and risk absorption (Research §2). The PRD therefore does not promise that the platform removes every intermediary function.

## 4. Target users

| ID | User | Description | Primary needs |
|---|---|---|---|
| U-FPO | FPO / producer collective (primary) | Aggregates produce from member farmers; has a coordinator with a smartphone | List produce in bulk, know where demand is, get a fair price, arrange transport |
| U-FARM | Individual farmer (secondary) | Small lot seller | Simple listing, price guidance |
| U-BULK | Bulk buyer | Restaurant group, retailer, processor, institutional kitchen | Reliable supply, known landed price, delivery date |
| U-GROUP | Consumer group buyer | RWA / community / consumer-cooperative group-buy | Lower price through aggregated demand |
| U-OPS | Logistics coordinator / platform operator | Plans consolidated dispatch | Fewer trips, capacity checks, cost view |
| U-OBS | Observer (policy / judge) | Wants evidence of system impact | Analytics and transparency |

Decision D-005: **individual single-household consumers are not a direct user type in the MVP.** SIH26033 says "consumers", which the MVP serves through aggregated `CONSUMER_GROUP` buyers. Individual D2C is FUTURE.

## 5. Farmer / FPO pain points

| ID | Pain point | Root cause | Addressed by |
|---|---|---|---|
| FP-1 | Does not know which city/market needs their crop this week | RC-1, RC-5 | FR-50, FR-51 |
| FP-2 | Does not know what a fair price is | RC-1 | FR-91 |
| FP-3 | Cannot find bulk buyers except through a known trader | RC-5 | FR-60, FR-63 |
| FP-4 | Transport is expensive for partial loads | RC-2, RC-3 | FR-70, FR-80 |
| FP-5 | Cannot see how the final price was split | RC-6 | FR-90 |
| FP-6 | Produce spoils while waiting for a buyer | RC-4 | FR-10 (expiry), matching freshness score |

## 6. Buyer pain points

| ID | Pain point | Addressed by |
|---|---|---|
| BP-1 | Sourcing through several layers; price opaque | FR-90, FR-102 |
| BP-2 | Inconsistent quantity/grade from ad-hoc sources | FR-20 (grade/qty spec), FR-60 |
| BP-3 | Unknown delivery cost until negotiation | FR-30, FR-70 |
| BP-4 | Cannot compare sources on price, distance and freshness together | FR-60 (scored, explained) |
| BP-5 | Large requirement cannot be met by one seller | FR-61 (multi-source allocation) |

## 7. Supply-chain pain points

| ID | Pain point | Addressed by |
|---|---|---|
| SC-1 | Supply and demand not coordinated in time | FR-50, FR-51 |
| SC-2 | Many half-empty vehicles on overlapping corridors | FR-80, FR-81 |
| SC-3 | No shared view of landed-price components | FR-90 |
| SC-4 | No feedback loop for planners | FR-100–FR-102 |

## 8. Existing workflow (as understood — Research §2; ASSUMPTION for step details)

```
Farmer → village trader / commission agent → APMC mandi (auction, wholesaler)
       → retailer / bulk-breaker → consumer or bulk buyer
Transport: arranged per hop; information: verbal, local; price: discovered at mandi.
```
Reported number of intermediaries in Indian produce channels is 6–8 (Lok Sabha reply, Research §2 F-1). Academic work shows intermediaries also perform real functions, so the "wedge" is not all waste (Research §2 F-2).

## 9. Proposed workflow

```
FPO/Farmer ── lists produce ──────────────────────────────┐
     ▲ PREDICT: demand forecast + hub ranking + price band │
                                                           ▼
Buyer ── posts requirement ──▶ MATCH (scored, explained, partial/multi-source)
                                                           │ accept
                                                           ▼
                                            ORDER (PLACED → CONFIRMED by producer)
                                                           │
Operator ── selects confirmed orders ──▶ MOVE: OR-Tools consolidated routes
                                                           │ approve
                                                           ▼
                              SHIPMENT (manual status) → DELIVERED
                                                           │
            SELL: price waterfall per order  ──▶  ANALYSE: dashboards
```
Payment is **out of scope** (settled outside the platform; D-006).

## 10. Product goals

| ID | Goal | SIH link | Verification |
|---|---|---|---|
| G-1 | A producer can list produce and immediately see demand intelligence for it | SIH-1, SIH-3 | Demo step 2; AC-FC-01, AC-FC-07 |
| G-2 | A buyer requirement is matched to producers with a ranked, explained result, including partial fills | SIH-1, SIH-7 | AC-MAT-01…08 |
| G-3 | Transport cost/kg is estimated for every candidate and every order | SIH-2 | AC-LOG-01…05 |
| G-4 | Multiple orders are consolidated into optimized routes with a disclosed baseline comparison | SIH-2, SIH-4, SIH-7 | AC-RTE-01…10 |
| G-5 | Every order shows a transparent price waterfall against a disclosed benchmark and a disclosed traditional-chain scenario | SIH-5, SIH-6 | AC-PRC-01…04 |
| G-6 | Analytics update when orders/routes change | SIH-7 | AC-ANL-01…03 |
| G-7 | All demo data is visibly labelled synthetic; no fabricated accuracy | (credibility) | AC-DATA-01…04 |

## 11. Non-goals

- Payments, escrow, invoicing, GST, e-way bill (D-006).
- Chat, social feed, ratings/reviews, notifications infrastructure.
- Live GPS tracking or any claim of real-time vehicle location (shipment status is manual).
- Real farmer-income claims or measured price savings (only **modelled scenario** differences).
- Credit, insurance, input sales, advisory content.
- Cold-chain/warehouse management, quality assaying, image-based grading.
- Individual household consumers (D-005), delivery-slot scheduling to households.
- Multi-tenant administration, KYC, Aadhaar/e-KYC, AgriStack integration.
- Deep learning forecasting (LSTM/Transformer), recommender systems, blockchain, LLM agents.
- Native mobile apps (responsive web only).

## 12. Core value proposition

| For | Value | Evidence type |
|---|---|---|
| FPO / farmer | See where demand is before harvest-selling; know a fair price band; share transport through consolidation; see exactly where the buyer's rupee goes | Modelled + forecast (synthetic-trained) |
| Bulk / group buyer | Direct, scored sourcing with a known landed price and freshness | Computed per order |
| Operator | One-click consolidated routes with capacity checks and a baseline comparison | Computed |
| Observer | Traceable metrics with every assumption disclosed | Computed + disclosed config |

## 13. Core user journeys

| ID | Journey | Steps |
|---|---|---|
| J-1 | FPO lists produce | Login → New listing → choose crop, grade, qty, price, dates → see demand forecast, hub ranking and price band beside the form → submit → listing ACTIVE |
| J-2 | Buyer sources | Login → New requirement → Match screen → inspect ranked candidates with explanations → accept allocation → orders PLACED |
| J-3 | Producer confirms | Orders → Confirm (or Reject) → CONFIRMED |
| J-4 | Operator plans movement | Logistics → confirmed orders pool → Optimize → review map, stops, savings, unassigned → Approve → shipments PLANNED → Dispatch → Deliver |
| J-5 | Anyone inspects price | Order detail → price waterfall (farmgate, transport, fee, landed) vs benchmark vs traditional-chain scenario |
| J-6 | Observer analyses | Analytics → KPIs, supply-vs-demand table, model card |
| J-7 | Marketplace direct buy (SHOULD) | Market → filter → listing detail with landed estimate → direct order |

## 14. Functional requirements

Priority: **M**=MUST, **S**=SHOULD, **N**=NICE, **F**=FUTURE. All state PLANNED.

| ID | Requirement | Pri | SIH link |
|---|---|---|---|
| FR-01 | Email+password login with JWT; roles `PRODUCER`, `BUYER`, `ADMIN` | M | SIH-1 |
| FR-02 | Self-registration for producer and buyer with location capture | S | SIH-1 |
| FR-03 | Demo persona quick-login when `DEMO_MODE=true` | M | (demo) |
| FR-04 | Profile with lat/lng (used by logistics, matching) | M | SIH-2 |
| FR-10 | Create listing: crop, grade, qty, ask price, min order, harvest/available dates; strict validation | M | SIH-1, SIH-5 |
| FR-11 | Edit price/quantity, withdraw listing; expired listings auto-hidden | M | SIH-1 |
| FR-20 | Create buyer requirement: crop, min grade, qty, max landed price, needed-by | M | SIH-1, SIH-6 |
| FR-21 | Cancel/update requirement | S | SIH-1 |
| FR-30 | Marketplace browse with filters (crop, grade, state, price, freshness) and landed-price estimate for buyers | M | SIH-1, SIH-6 |
| FR-31 | Listing detail (producer summary, demand badge, landed estimate) | S | SIH-1 |
| FR-32 | Direct order from a listing | S | SIH-1 |
| FR-40 | Order lifecycle with guarded transitions and event log | M | SIH-7 |
| FR-41 | Atomic quantity reservation; restore on cancel/reject | M | SIH-7 |
| FR-50 | 7-day demand forecast with 80% interval for hub × crop | M | SIH-3 |
| FR-51 | Hub ranking for a crop from producer location (demand pressure + net realisation) | M | SIH-3, SIH-5 |
| FR-52 | Model card endpoint with metrics and **synthetic-data disclosure** | M | SIH-3 |
| FR-53 | Forecast fallback (seasonal-naive) when model unavailable, flagged in response | M | SIH-3 |
| FR-60 | Ranked candidates for a requirement with hard filters, weighted score and per-factor explanation | M | SIH-1, SIH-7 |
| FR-61 | Partial and multi-source allocation; shortfall reported | M | SIH-1 |
| FR-62 | Accept allocation → orders created atomically with server-side revalidation | M | SIH-1 |
| FR-63 | Producer-side opportunities: compatible open requirements for a listing (read-only) | S | SIH-1, SIH-3 |
| FR-70 | Logistics estimate: distance, vehicle plan, cost, cost/kg, transit hours | M | SIH-2 |
| FR-71 | Vehicle reference list | M | SIH-2 |
| FR-80 | Consolidated multi-stop pickup-and-delivery optimization (OR-Tools) with capacity and route-duration constraints | M | SIH-4 |
| FR-81 | Baseline comparison (unconsolidated dedicated trips) for km and cost | M | SIH-4, SIH-7 |
| FR-82 | Plan lifecycle PROPOSED → APPROVED/DISCARDED; approval creates shipments | M | SIH-2 |
| FR-83 | Shipment manual lifecycle PLANNED → DISPATCHED → DELIVERED (no live tracking) | S | SIH-2 |
| FR-84 | Unassigned orders reported with reason (capacity, duration, infeasible) | M | SIH-4 |
| FR-85 | Route map with ordered stops (schematic or road geometry) | M | SIH-4 |
| FR-86 | Optional road-network distances via OSRM with automatic haversine fallback | N | SIH-4 |
| FR-90 | Per-order price waterfall: farmgate, transport, platform fee, landed | M | SIH-5, SIH-6 |
| FR-91 | Price benchmark (latest reference modal price, source-labelled) and fair price band | M | SIH-5 |
| FR-92 | Traditional-chain **scenario** comparison with visible assumptions | M | SIH-5, SIH-6 |
| FR-93 | Ingest real Agmarknet snapshot into `market_prices` | N | SIH-5 |
| FR-100 | KPI overview (volume, value, fill rate, logistics cost/kg, route savings, utilisation) | M | SIH-7 |
| FR-101 | Supply-vs-demand table per hub × crop | M | SIH-3, SIH-7 |
| FR-102 | Modelled price gap vs traditional chain (avg %) | M | SIH-5, SIH-6 |
| FR-110 | Deterministic demo seed + one-click reset (DEMO_MODE, ADMIN) | M | (demo) |
| FR-111 | Every seeded/synthetic record flagged `is_demo`/`is_synthetic`, badge in UI | M | (credibility) |
| FR-112 | Health endpoint | M | (ops) |
| FR-120 | Hindi UI labels for the producer listing flow | N | (usability) |

## 15. Non-functional requirements

Targets are **design targets, not measured results**; Testing.md defines how each is measured later.

| ID | Requirement | Target |
|---|---|---|
| NFR-1 | API latency, non-optimizer endpoints, local machine | p95 < 500 ms |
| NFR-2 | Route optimization | ≤ 10 s wall time for ≤ 30 orders and ≤ 5 vehicles (default time limit 5 s) |
| NFR-3 | Forecast inference | < 300 ms per hub × crop |
| NFR-4 | Mobile-first UI | fully usable at 360 px width; no horizontal page scroll |
| NFR-5 | Accessibility | WCAG 2.1 AA intent: contrast, focus, labels, ≥44 px touch targets |
| NFR-6 | Core demo works offline of third-party APIs | No external call required for the main demo path |
| NFR-7 | Reproducibility | `setup_demo` yields identical entity counts with the fixed seed |
| NFR-8 | Security baseline | Hashed passwords, JWT expiry, object-level authorization, validated input |
| NFR-9 | Errors | Uniform JSON error envelope; no stack traces to client |
| NFR-10 | Maintainability | Modular monolith; one module per domain; no cross-module DB writes except via service functions |

## 16. Core modules

| ID | Module | Responsibility | Pri |
|---|---|---|---|
| M1 | Identity & Profiles | auth, roles, profiles, locations | M |
| M2 | Producer Listings | listing CRUD, validation, expiry | M |
| M3 | Buyer Requirements | requirement CRUD | M |
| M4 | Marketplace & Orders | browse, direct order, order lifecycle, reservation | M |
| M5 | Demand Intelligence | forecast, hub ranking, model card | M |
| M6 | Matching Engine | filters, scoring, allocation, accept | M |
| M7 | Logistics | distance, vehicle selection, cost | M |
| M8 | Route Optimization | OR-Tools VRP, plans, shipments | M |
| M9 | Price Transparency | waterfall, benchmark, fair band | M |
| M10 | Analytics | KPIs, supply-demand, comparisons | M |
| M11 | Reference & Demo Data | crops, hubs, seed/reset | M |

## 17. MVP scope

MVP = every `M` requirement in §14 plus the `S` items that fit the 3-day plan. The authoritative classification (MUST / SHOULD / NICE / FUTURE per feature) is the **3-Day Feasibility Audit in Phases.md §15**; if this PRD and that audit disagree, the audit wins and the PRD must be corrected (recorded in Memory.md).

Explicit MVP boundaries: one geographic demo region (Delhi-NCR belt), 5 crops, 5 demand hubs, 6 demo producers, 5 demo buyers, 5 vehicles; SQLite; synthetic demand data; synthetic price benchmark unless an Agmarknet snapshot is ingested.

## 18. Future scope (FUTURE — not built)

Real demand signals from buyer order history; real Agmarknet/eNAM price feeds with scheduled refresh; eNAM "Platform of Platforms" / ONDC integration study; payments and escrow; individual consumer D2C; min-cost-flow global matching; cold-chain constraints; mixed-load compatibility rules; live vehicle tracking with driver app; multilingual UI beyond Hindi labels; Postgres + Alembic migrations; holiday/festival calendar features; price forecasting; FPO-level analytics and credit scoring.

## 19. Success criteria

| Level | Criterion |
|---|---|
| Functional | Demo path (Demo.md) runs end-to-end from a fresh `setup_demo` without manual DB edits |
| Technical | All `M` acceptance criteria in Testing.md executed and recorded in the execution log; forecast model beats the seasonal-naive baseline on validation and test, **or** the fallback is honestly shown |
| Honesty | No UI or doc claim exceeds what is implemented; all demo numbers carry a synthetic/modelled label |
| Judging | Clear link from each screen to SIH26033; ability to answer the Q&A in Demo.md without overclaiming |

## 20. Constraints

Single developer (Shubham Kumar); ~3 days (~31 planned working hours, Phases.md); AI coding agents as assistants only; no budget for paid APIs; no access to real buyer-order data; public demo server limits for routing (Research §6); SIH evaluation favours a working demo.

## 21. Risks (summary; full register in Research §9 and Testing.md)

| ID | Risk | Mitigation |
|---|---|---|
| R-01 | Scope creep beyond 3 days | Cut list in Phases.md §15; freeze at T-4h |
| R-02 | Forecast trained on synthetic data looks "too good" | Mandatory disclosure in UI/model card; Rules.md data rules |
| R-03 | Agmarknet/data.gov.in access unreliable | Synthetic benchmark default, ingestion optional |
| R-04 | OR-Tools formulation takes longer than planned | Timeboxed; greedy insertion fallback (FR-84 still honoured) |
| R-05 | Judges view it as "another marketplace" | Demo leads with PREDICT→MATCH→MOVE loop, not catalogue |
| R-06 | Overclaiming savings | Only modelled scenario language; assumptions visible |

## 22. Assumptions (register)

| ID | Assumption | Status |
|---|---|---|
| A-01 | The developer is comfortable with React and Python (or AI tools compensate) | ASSUMPTION |
| A-02 | Demo is shown from the developer's laptop; a deployed copy is backup | ASSUMPTION |
| A-03 | Demand hubs are city clusters; hub demand is bulk-buyer demand, not household demand | PROPOSAL |
| A-04 | No public dataset of buyer-level produce demand exists for this use; synthetic demand is required | ASSUMPTION (not exhaustively searched) |
| A-05 | Agmarknet prices are quoted per quintal (100 kg) and need conversion to ₹/kg | ASSUMPTION — verify on first download |
| A-06 | Vehicle rates, speeds, circuity factor, margins, shelf-life values are illustrative config values, not sourced | ASSUMPTION |
| A-07 | Mixed-crop loads in one vehicle are allowed in MVP | PROPOSAL |
| A-08 | Payment and invoicing happen outside the platform | PROPOSAL |
| A-09 | All dates use Asia/Kolkata | PROPOSAL |
| A-10 | The SIH26033 text in the owner's brief matches the official portal | ASSUMPTION |

## 23. Demo scenario (summary — full script in Demo.md)

1. FPO "Sonipat Kisan Collective [DEMO]" lists 2,000 kg Grade-A tomato at ₹19.00/kg → demand forecast, hub ranking and price band appear beside the form.
2. Buyer "Gurugram Restaurant Group [DEMO]" has an open requirement for 1,500 kg tomato → Match screen ranks candidates with explanations → accept → order PLACED.
3. Operator confirms and opens Logistics: seeded confirmed orders plus the new one → Optimize → consolidated routes, baseline comparison, utilisation → Approve.
4. Order detail shows the price waterfall against benchmark and traditional-chain scenario.
5. Analytics reflects the new order and approved plan.
