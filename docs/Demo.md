# Demo — KrishiSetu (SIH26033)

Status: PLANNED. Inputs below are exact and come from Data.md §12. **Outputs are described as expected properties, not pre-claimed numbers** — the system is not built yet. After the first full run, record real values in §11 and use only those on stage (Rules D-3).

## 1. Narrative (one sentence)

*"Intermediaries bundle price information, buyer discovery and transport; KrishiSetu unbundles them into one loop — Predict demand, Match buyers, Move cargo in consolidated routes, Sell with a transparent price breakdown, Analyse the chain."*

Mapping to the screen path: Listing + forecast (PREDICT) → Match screen (MATCH) → Logistics + route plan (MOVE) → Order price waterfall (SELL) → Analytics (ANALYSE).

## 2. Pre-demo checklist (T−60 min)

1. `git status` clean, tag `demo-ready` checked out.
2. From `backend/`: `python -m scripts.setup_demo --no-retrain` (fresh deterministic seed dated today), then start API; `GET /api/v1/health` shows `db:"ok"`, `model.loaded:true`.
3. Start frontend (or built SPA). Open in a desktop browser **and** a 360 px phone/emulator tab.
4. Log in once per persona to confirm; keep the Persona switcher visible.
5. Confirm map tiles load (otherwise rely on the schematic list — §8).
6. Open Memory.md "Known bugs" and avoid those paths.
7. Have the screen recording and screenshots ready (§8).
8. Run `POST /system/reset-demo` (Operator menu → Reset demo data) immediately before going on stage.

## 3. Demo data (exact)

Seed dated "today" (IST). Personas (password shown on the Login page, demo only): `fpo_sonipat`, `buyer_gurugram`, `operator`.

| Item | Value |
|---|---|
| Live listing (typed on stage) | Producer P1 *Sonipat Kisan Collective [DEMO]* · Tomato · Grade A · **2,000 kg** · ask **₹23.00/kg** · min order **200 kg** · harvest **today** · available **today → today+3** |
| Buyer requirement (already seeded) | R1 — *Gurugram Restaurant Group [DEMO]* · Tomato · min Grade B · **1,500 kg** · max landed **₹29.00/kg** · needed by today+1 |
| Routing pool (seeded, CONFIRMED) | O1 Tomato 600 kg P2→B5 · O2 Onion 1,200 kg P4→B4 · O3 Potato 900 kg P4→B3 · O4 Tomato 500 kg P6→B3 · O5 Cauliflower 400 kg P1→B2 · O6 Green Chilli 150 kg P5→B1 (+ the new live order) |
| Fleet | MT-01 750 kg, PK-01 1,500 kg, MD-01 4,000 kg (Sonipat depot); PK-02 1,500 kg, MT-02 750 kg (Ghaziabad depot) |
| Extra seeded cases for the 5-min demo | R3 (partial fill), R8 (no match), R2 (multi-source) |

## 4. Three-minute demo (exact clicks)

| Time | Action (clicks) | What to say | Expected on screen (verify) |
|---|---|---|---|
| 0:00–0:20 | Login page, no clicks | "SIH26033: farmers earn less, consumers pay more, several intermediaries in between. They also do real work — information, discovery, transport. We unbundle those functions." | Login with DEMO notice |
| 0:20–0:55 | Click **FPO Sonipat** persona → bottom nav **My Listings** → **+ New listing** → Crop *Tomato*, Grade *A*, Quantity *2000*, Price *23.00*, Min order *200*, Harvest *today*, Available *today → +3* | "**PREDICT.** Before I publish, the FPO sees where demand is." Point at Demand panel: hub ranking, forecast band, price band. Say "synthetic" badge aloud | Demand panel populated: ranked hubs with Shortage/Balanced/Surplus chips, 7-day forecast with 80% band, benchmark and fair band with source badges |
| 0:55 | Click **Publish listing** | — | Toast; listing ACTIVE |
| 0:55–1:30 | Persona switcher → **Buyer Gurugram** → **Requirements** → R1 **Find matches** | "**MATCH.** Not a catalogue: ranked, explained, with landed price." Open **Why this rank?** on rank 1 | Rank-1 candidate is expected to be the new Sonipat listing (nearest eligible Grade A, freshest); fill FULL; factor bars; landed = ask + transport + fee |
| 1:30 | Click **Accept allocation** | — | Order created, status PLACED |
| 1:30–1:45 | Persona switcher → **Operator** → **Orders** → open the new order → **Confirm** (operator override) | "Producer confirmation — operator can act on behalf for the demo." | Status CONFIRMED |
| 1:45–2:25 | **Logistics** → pool shows seeded orders + new → **Select all** → **Optimize routes** | "**MOVE.** OR-Tools consolidates pickups and drops under capacity and duration limits." | Plan page: map, per-vehicle stops, km/₹, utilisation, savings vs baseline with the "modelled baseline" note; unassigned section (empty or with reasons) |
| 2:25 | Click **Approve plan** | — | Plan APPROVED, shipments PLANNED |
| 2:25–2:45 | **Orders** → the new order → price waterfall → **Assumptions** | "**SELL.** Every rupee is visible: farmgate, transport, fee, landed — against a benchmark and a *modelled* traditional-chain scenario. Assumptions are editable config." | Waterfall with source badges; two delta chips labelled Modelled |
| 2:45–3:00 | **Analytics** | "**ANALYSE.** KPIs just moved: orders, fill rate, route savings. All on synthetic demo data — we do not claim measured farmer income." | KPI cards updated; supply-demand table; DEMO banner |

## 5. Five-minute demo (adds depth)

Same as §4 plus, inserted:

1. **Before publishing the listing (0:50):** Persona → Buyer Gurugram → R1 **Find matches** first. Expected (verify): little or no economical supply (remaining tomato lots are small and far), illustrating the aggregation problem. Then go back to the FPO persona and publish; re-run Match and show the change from the weak/partial result to a full single-source fill.
2. **Edge cases (after Accept):** R3 (Cauliflower, Grade A, 1,000 kg) → PARTIAL with shortfall banner; R8 (Tomato A, 2,500 kg, ₹22) → NONE with near-miss "over budget"; R2 (Onion 6,500 kg) → multi-source allocation.
3. **Forecast page:** Demand dashboard → open **Model card** drawer → state measured metrics only from the card; point out baselines and the 80% interval coverage as *measured*, plus the synthetic disclaimer.
4. **After Approve:** open one shipment → **Dispatch** → **Mark delivered** (manual, labelled) → show order statuses move to In transit/Delivered → Analytics "committed" and route KPIs.
5. **Mobile:** switch to the 360 px tab and show Match and Order detail.

## 6. Illustrative worked arithmetic (formula check, **not system output**)

Hand-calculated from approximate coordinates and config defaults (circuity 1.35, return factor 2.0, PICKUP ₹16/km + ₹600, fee 2%). The app's own numbers are authoritative; expect them to be close but not identical.

- Sonipat (28.99, 77.02) → Gurugram buyer (28.47, 77.05): straight line ≈ 58 km → road estimate ≈ 78 km.
- 1,500 kg fits one PICKUP (1,500 kg): trip cost ≈ 600 + 16 × 78 × 2 ≈ ₹3,100 → ≈ ₹2.07/kg.
- Fee ≈ 2% × 23.00 = ₹0.46/kg → landed ≈ 23.00 + 2.07 + 0.46 ≈ **₹25.5/kg** vs budget ₹29.00 (headroom ≈ 12%).
- If benchmark modal ≈ ₹24/kg: farmer mandi-net ≈ 24 × 0.95 − ≈2.1 ≈ ₹20.7; buyer traditional ≈ 24 × 1.08 × 1.12 + 1.0 ≈ ₹30.0 → farmer scenario delta ≈ +11%, buyer scenario delta ≈ −15%. **These are outcomes of assumptions, not measured savings.**

## 7. Judge explanation (30 seconds)

"Our system does five things in one loop. It predicts where demand will be, matches farmer lots to buyer requirements with explainable scores, plans consolidated transport, shows a transparent price breakdown, and tracks supply-chain KPIs. It is deliberately honest: demand data is synthetic because no public buyer-level data exists, and price savings are shown as a modelled scenario with every assumption visible."

## 8. Fallback scenarios

| Failure | Response |
|---|---|
| Forecast model fails/missing | UI shows "Using a simple fallback estimate" — narrate it as designed behaviour (AC-FC-02) |
| OR-Tools slow/fails | Plan returned with method "Greedy fallback"; say so |
| Map tiles don't load | Use the stop list / schematic view |
| OSRM unreachable | Already default to estimated distances; no impact |
| Backend crashed | Restart; Operator → Reset demo data; reload |
| Data looks off | Reset demo data, rerun |
| Laptop fails | Open the deployed backup URL (may need ~1 min cold start) |
| Everything fails | Play the screen recording; walk through screenshots |

## 9. Technical explanation (60–90 seconds)

React + TypeScript SPA; FastAPI modular monolith; SQLite via SQLAlchemy (Postgres-compatible); LightGBM quantile models with a seasonal-naive fallback and a deployment gate; deterministic scored matching; OR-Tools capacitated pickup-and-delivery routing with a disclosed baseline; formulas and assumptions in YAML; synthetic data labelled everywhere; single Docker image deployment.

## 10. Likely judge questions and honest answers

| Question | Answer |
|---|---|
| Isn't this just another marketplace? | The marketplace is the least important screen. The value is the loop: forecast, explained matching, consolidated routing and price transparency in one flow. |
| Ninjacart/DeHaat/eNAM already do this. | Yes — direct sourcing, forecasting, route planning and digital mandi trading exist (Research §3). We don't claim novelty in any single capability. Our angle is an open, FPO-first coordination layer with inspectable assumptions rather than an inventory-owning trader. |
| Is the forecast real? | It is trained on synthetic demand because no public buyer-level demand data exists. The metrics validate the pipeline, not real-world accuracy, and the UI says so. With real order history the same pipeline can be retrained. |
| How much do farmers save? | We don't claim a measured number. We show a modelled scenario using disclosed assumptions; real impact needs a pilot. |
| Why not ML for matching? | There's no training signal and explainability matters; deterministic scoring is better engineering. Not every problem needs ML. |
| Why OR-Tools? | Consolidation with capacities and pickup-delivery pairing is a vehicle-routing problem; OSRM's trip service is only a greedy TSP. |
| Are the distances real? | Default distances are estimated (straight-line × circuity factor) and labelled; road distances via OSRM are optional. |
| What about payments and trust? | Out of scope; settlement is outside the platform. Credit and trust functions of intermediaries are real and not solved here. |
| Is vehicle tracking live? | No. Status is manual. No GPS claims. |
| Why are intermediaries bad if they add value? | They aren't all bad; we target the information and coordination gaps, not logistics work itself. |
| How would it scale? | Postgres, queue for optimization, self-hosted OSRM, real data feeds — all FUTURE. |
| What did you build in 3 days? | Everything on the screens you saw; anything beyond is labelled PLANNED/FUTURE in the docs. |

## 11. Demo verification log (fill after the first successful full run; leave blank until then)

| Item | Observed value | Date |
|---|---|---|
| R1 candidates before live listing (fill status, count) | NONE (count: 0, fulfilled: 0.0 kg) | 2026-10-02 |
| R1 rank-1 listing after live listing; fill status | Listing ID 15 (Sonipat Kisan Collective); FULL (1,500 kg) | 2026-10-02 |
| Landed price rank 1 (₹/kg) | ₹25.53/kg (Farmgate ₹23.00 + Trans ₹2.07 + Fee ₹0.46) | 2026-10-02 |
| Plan: method, solve time, vehicles used | ORTOOLS, 5.08s wall time, 5 vehicles used | 2026-10-02 |
| Plan: optimized km / baseline km; ₹ / ₹ | 909.1 km / 1,307.3 km; ₹17,783.26 / ₹20,851.84 (savings: 398.2 km, ₹3,068.58 / 14.7%) | 2026-10-02 |
| Waterfall: farmgate / transport / fee / landed | ₹23.00 / ₹3.52 / ₹0.46 / ₹26.98 (reconciles ±0.01; O1 allocated consolidated route transport is ₹3.52/kg vs its dedicated charter baseline ₹4.07/kg, representing a 13.6% transport savings; distinct from R1 1,500kg dedicated estimate ₹2.07/kg) | 2026-10-02 |
| Model card: deployed_method, val & test MAE vs baseline | LIGHTGBM, Val MAE: 105.42, Test MAE: 104.66 vs B1 Seasonal Naive: 137.55 (passed gate) | 2026-10-02 |
| Analytics KPIs after demo path | Committed orders: 11, Volume: 7,850 kg, Value: ₹1,74,600, Fill rate: 9.26%, Route savings: 398.2 km (₹3,068.58) | 2026-10-02 |


## 12. Limitations to state if asked

Synthetic demand and prices by default; no payments; no live tracking; one demo region and five crops; distances estimated; greedy per-requirement matching (not globally optimal); mixed crops share vehicles; modelled baseline and scenario depend on assumptions; SQLite single-writer.

## 13. Future scope to mention

Real order-history training; Agmarknet/eNAM price feeds; ONDC/eNAM integration study; payments/escrow; individual consumer groups at scale; cold-chain and loading constraints; global min-cost-flow matching; live tracking; Postgres and migrations.
