# Research — SIH26033 (KrishiSetu)

**Tagging rule.** Every substantive statement is tagged:

- `[FACT-V]` — verified in the documentation session from a source listed in §12 (URL given).
- `[FACT-U]` — believed true from background knowledge but **not re-verified**; verify before citing in any submission.
- `[ASSUMPTION]` — needed to proceed; not sourced.
- `[PROPOSAL]` — a design decision this project makes.
- `[FUTURE]` — deliberately not built.

Nothing here is claimed "unique" without evidence. Where a capability already exists elsewhere, that is stated.

---

## 1. SIH26033 interpretation

| Item | Reading | Tag |
|---|---|---|
| Official text | Taken from the owner's brief (title, creator, expected solution, benefits). A web search in the session did not surface the portal entry. | `[ASSUMPTION]` matches the portal (A-10) |
| Four solution pillars | Direct marketplace; logistics support; AI demand forecasting; AI route optimization | from brief |
| Three benefits | Better farmer prices; lower consumer prices; fewer supply-chain inefficiencies | from brief |
| "Consumers" | Served through aggregated consumer-group buyers in MVP; individual D2C deferred | `[PROPOSAL]` D-005 |
| "AI" | Demand forecasting = ML (gradient boosting). Route optimization = combinatorial optimization (OR-Tools), which is "AI" in the operations-research sense. Matching = deterministic scoring, not ML. | `[PROPOSAL]` — stated openly to avoid inflating "AI" claims |
| Judging lens | Problem understanding, working solution, technical depth, demo quality, realistic implementation | from brief |

**Product decision PD-1:** build the four pillars as a connected loop (PREDICT→MATCH→MOVE→SELL→ANALYSE), with the loop — not the catalogue — as the demo centrepiece.

## 2. Agricultural supply chains and intermediaries

### Findings

| ID | Finding | Tag | Source |
|---|---|---|---|
| F-1 | A Government of India reply to Parliament states intermediaries in agricultural produce channels (commission agents, traders, wholesalers, distributors) number roughly 6–8, reduce the farmer's share of the consumer's rupee, and raise consumer prices. It cites a 2004 Ministry of Agriculture "Millennium study" putting the producer's share of consumer spending at 32%–68% for fruits, vegetables and flowers. | `[FACT-V]` (old study — order-of-magnitude context only) | eparlib.nic.in (S-1) |
| F-2 | Academic evidence is mixed: intermediaries are often blamed for the farm-to-retail wedge, but theory and field observation also show they supply time, transport, storage and credit that farmers lack; under some conditions multiple intermediaries *increase* consumer welfare via competition. | `[FACT-V]` | CASI, Univ. of Pennsylvania (S-2) |
| F-3 | A study-based report on Pakistani onion/potato/tomato chains found bulk-breaker (last-stage) margins of 20–42% after quality controls, highest for tomatoes. | `[FACT-V]` but **Pakistan, not India** — indicative only | IGC (S-3) |
| F-4 | Commentary on intermediary-heavy chains notes you can reduce the number of hands but not the underlying value-creating activities (grading, sorting, packaging, transport). | `[FACT-V]` (opinion piece) | Financial Express BD (S-4) |
| F-5 | Mandi (APMC) wholesale prices are published as min / max / modal per day per market through Agmarknet. | `[FACT-V]` | data.gov.in (S-5) |

### Implications

- **PD-2 (framing):** position the platform as *unbundling* intermediary functions (information, matching, consolidated transport) into transparent services, not as "removing middlemen". This is defensible against F-2 and F-4. `[PROPOSAL]`
- **PD-3 (honest numbers):** do not assert a measured % saving. Show a **modelled scenario** with editable assumptions and cite F-1/F-3 only as motivation. `[PROPOSAL]`
- **PD-4:** credit/trust/cold-storage functions of intermediaries are explicitly out of scope (PRD RC-7). `[PROPOSAL]`

## 3. Existing platforms and competitors

| Platform | What it does | Overlap with this project | Tag / source |
|---|---|---|---|
| **eNAM** (National Agriculture Market) | Government electronic trading platform integrating regulated mandis; by March 2026: 1,656 mandis in 23 States + 4 UTs; >1.80 crore farmers, ~2.73 lakh traders, 4,724 FPOs registered; cumulative trade ₹4.84 lakh crore. SFAC is the implementing agency. | Direct overlap on "digital marketplace" and FPO trade; price discovery is mandi-auction-centred | `[FACT-V]` PIB (S-6) |
| eNAM "Platform of Platforms" | Reported to add logistics, fintech, warehousing and FPO modules | Overlap on logistics/FPO integration | `[FACT-U]` — only a secondary UPSC-prep site (S-7) reported it; verify on enam.gov.in |
| **Ninjacart** | B2B fresh-produce supply chain: sources directly from farmers via collection centres, sells to retailers/restaurants; company statements describe demand forecasting to plan purchases and route planning to minimise delivery cost | **Direct overlap with all four SIH pillars** (self-reported, inventory-led model) | `[FACT-V]` company/press statements (S-8, S-9); accuracy/wastage figures are **self-reported — do not reuse** |
| **DeHaat** | Agri services marketplace (inputs, advisory, produce) serving farmers, micro-entrepreneurs, institutional buyers | Overlap on farmer↔buyer linkage | `[FACT-V]` description (S-10) |
| YourKrishi | Connects farmers with businesses for fresh-produce supply; inventory planning and delivery | Overlap | `[FACT-V]` description (S-10) |
| Agmarknet / mandi-price apps | Free price information, min/max/modal | Overlap on price transparency | `[FACT-V]` (S-5) |
| ONDC (agri/FPO onboarding), WayCool, Jumbotail, Kisan Suvidha app, Central scheme for 10,000 FPOs | Exist per background knowledge | Partial overlaps | `[FACT-U]` — not verified in session |

### What existing platforms already solve (do not claim as novel)

1. Direct farmer/FPO-to-business produce sourcing (Ninjacart, YourKrishi, DeHaat).
2. Mandi price information (Agmarknet, eNAM).
3. Internal demand forecasting and delivery route planning inside private supply chains (Ninjacart self-reports both).
4. Digital mandi trading with FPO participation (eNAM).

### What is NOT unique

A marketplace, demand forecasting, route optimization, direct sourcing, FPO focus — **each exists**. The project must not claim any of these as a first.

## 4. Differentiation opportunity (honest)

| ID | Opportunity | Why defensible | Tag |
|---|---|---|---|
| DF-1 | **Open, FPO-first coordination layer** rather than an inventory-owning trader: producers keep the sale; the platform provides information and coordination | Inventory-led models (Ninjacart's described approach) take title/margin; an FPO-first coordination layer is a different structure | `[PROPOSAL]` |
| DF-2 | **Explainable matching**: every ranked candidate shows per-factor scores and reasons | Most platforms show listings, not scored explanations; *not verified across all competitors* | `[PROPOSAL]`, uniqueness **not claimed** |
| DF-3 | **One connected loop in one product** (forecast → match → consolidated route → price waterfall → analytics) with all assumptions inspectable | Judged as integration depth; not a claim of market novelty | `[PROPOSAL]` |
| DF-4 | **Transparent price waterfall with a disclosed traditional-chain scenario** | Directly targets the SIH problem ("where did the price go") | `[PROPOSAL]` |
| DF-5 | Honest data labelling (synthetic vs real) as a product feature | Builds judge trust | `[PROPOSAL]` |

**Product decision PD-5:** the pitch says "we integrate and make transparent" — never "no one does this".

## 5. Demand forecasting research

| Topic | Finding / position | Tag |
|---|---|---|
| Available signals | Public mandi data gives prices (and in some datasets arrivals), not buyer-level purchase demand | `[ASSUMPTION]` A-04 (no exhaustive dataset search) |
| Real buyer demand data | Not available to this project | `[FACT]` of our situation |
| Consequence | Demand training data must be **synthetic**, generated from a documented process; any accuracy figure validates the *pipeline*, not real-world performance | `[PROPOSAL]` D-010 |
| Model choice | Tabular time-series with calendar + lag + price features → gradient boosting (LightGBM) is a sound, fast, explainable choice; seasonal-naive and moving-average baselines are mandatory | `[PROPOSAL]` |
| Uncertainty | Quantile regression (q10/q90) → 80% interval; report empirical coverage honestly | `[PROPOSAL]` |
| Deep learning | Unjustified at this data size and time budget | `[PROPOSAL]` |
| Horizon | 7 days, direct strategy using lags ≥ 7 (no recursive forecasting, no leakage) | `[PROPOSAL]` |

## 6. Agricultural logistics and route optimization

| Topic | Finding / position | Tag | Source |
|---|---|---|---|
| Problem class | Consolidating pickups and deliveries with vehicle capacity and route duration = capacitated pickup-and-delivery VRP | `[FACT-U]` standard OR | — |
| Solver | Google OR-Tools routing library supports pickup-delivery pairs, capacity dimensions, fixed vehicle costs, disjunction penalties | `[FACT-U]` — verify API names in Phase 8 against the installed version's docs | — |
| OSRM `trip` service | A greedy TSP heuristic only — not a capacitated VRP; so OR-Tools is needed for the optimization claim | `[FACT-V]` | OSRM README (S-11) |
| OSRM public demo server | Non-commercial, reasonable use, ≤ 1 request/second, no uptime/latency guarantee, ODbL + OSRM attribution required, may be withdrawn anytime | `[FACT-V]` | OSRM wiki (S-12, S-13) |
| Consequence | Default distance = haversine × circuity factor (offline, deterministic, labelled *estimated*). OSRM is an optional enhancement with cache, ≤ 25 nodes and automatic fallback. | `[PROPOSAL]` D-014 |
| Circuity factor 1.35, speed 30 km/h, costs/km, fixed costs | Illustrative config values | `[ASSUMPTION]` A-06 |
| Baseline for savings | "Each order ships on its own dedicated round trip from the pickup point" — models today's uncoordinated transport. Savings are modelled vs this baseline, **not** vs measured reality | `[PROPOSAL]` |
| Live tracking | Out of scope; status is manual | `[PROPOSAL]` |

## 7. Datasets, APIs and public data sources

| Source | Content | Access | Limits | Decision | Tag |
|---|---|---|---|---|---|
| data.gov.in — "Current Daily Price of Various Commodities from Various Markets (Mandi)" (from Agmarknet) | Daily wholesale min/max/modal per commodity × market | OGD platform; an API key from a free account is reported to be required; the resource page for one listing said "API for this resource does not exist — request API" | Schema inconsistencies and pagination quirks reported by developers; availability of a usable API **must be verified on the day** | Optional ingestion (FR-93, NICE); synthetic default | `[FACT-V]` (S-5, S-14 secondary); availability `[ASSUMPTION]` |
| Variety-wise Daily Market Prices (data.gov.in / AIKosh listing) | Same family of data | Listing exists | Format/access unverified | Same | `[FACT-V]` listing (S-15) |
| Community wrappers of Agmarknet (e.g., a free 5-state API) | Re-served government data | Public | Third-party, licence CC BY-NC-SA 4.0 on that one, uptime unknown | **Do not depend on**; mention only | `[FACT-V]` (S-14) |
| eNAM live price dashboard | Mandi prices | Public website | No documented public API verified | Not used | `[FACT-V]` existence (S-6) |
| OpenStreetMap tiles | Base map | Public | Tile usage policy: fair use; attribution required | Leaflet + OSM tiles for demo with attribution; schematic fallback | `[FACT-U]` policy details — re-read before deploy |
| OSRM | Road distances | Public demo server | see §6 | Optional | `[FACT-V]` |
| Buyer-level produce demand | — | None available | — | **Synthetic** | `[ASSUMPTION]` A-04 |
| Vehicle rates, freight costs | — | No public reliable source used | — | Config constants flagged ASSUMPTION | `[ASSUMPTION]` A-06 |
| District/coordinates | Approximate district-centre lat/lng for NCR-belt towns | Typed from general knowledge | Approximate only | Used for demo entities; flagged approximate | `[ASSUMPTION]` |

### Data limitations that shape the product

1. No real demand → demand forecast is a *pipeline demonstration* (D-010).
2. Agmarknet gives wholesale prices, not farm-gate or retail; farm-gate and retail are modelled (D-012).
3. Mandi names need manual mapping to demand hubs (`market_hub_map.csv`).
4. Market-price units are per quintal; convert ÷100 to ₹/kg `[ASSUMPTION]` A-05.

## 8. Feasibility

| Component | Feasible in ~3 days solo with AI agents? | Notes |
|---|---|---|
| CRUD + auth + roles | Yes | Well-trodden |
| Marketplace/orders with reservation | Yes | Watch atomic update |
| LightGBM pipeline on synthetic panel | Yes | Generator + train + inference ≈ 4 h |
| Deterministic matching with explanations | Yes | Pure functions, easy tests |
| OR-Tools pickup-delivery with capacity | Yes, risky | Most likely overrun → timebox + fallback heuristic |
| Price waterfall + scenario | Yes | Pure arithmetic over config |
| Analytics | Yes | SQL aggregates |
| Real Agmarknet ingestion | Uncertain | API access risk → NICE |
| OSRM | Yes but optional | Rate-limited demo server |
| Hindi UI | Only labels | NICE |

## 9. Risk register (research-derived)

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-02 | Synthetic-trained model mistaken for real accuracy | High | High | Disclosure banner, model card, Rules.md |
| R-03 | data.gov.in/Agmarknet API unavailable | Medium | Low | Synthetic default |
| R-07 | OSRM demo server throttles/blocks | Medium | Low | Default haversine, cache, fallback |
| R-08 | Competitor comparison challenged by judges | Medium | Medium | Honest Research §3–4; Demo Q&A |
| R-09 | OR-Tools model infeasible/slow on edge cases | Medium | High | Disjunction penalties, chunking, time limit, greedy fallback |
| R-10 | Modelled savings read as real | Medium | High | Label "modelled", show assumptions, Rules.md claim table |
| R-11 | Cold start of free hosting during demo | Medium | Medium | Local laptop primary; screenshots/video fallback |
| R-12 | SIH26033 text differs from portal | Low | Medium | Re-verify before submission |

## 10. Assumptions register

See PRD §22 (A-01…A-10). Research adds: A-11 — OSM tile usage for a low-traffic demo is acceptable `[ASSUMPTION]`; A-12 — approximate NCR-belt coordinates are adequate for distance estimation `[ASSUMPTION]`.

## 11. Research → product decisions (traceability)

| Decision | Driven by |
|---|---|
| Unbundling framing, not "remove middlemen" (PD-2) | F-2, F-4 |
| Modelled, labelled price scenario (PD-3) | F-1, F-3, data limitation 2 |
| Synthetic demand with disclosure (D-010) | §5 |
| OR-Tools rather than OSRM `trip` (D-013) | §6 |
| Haversine default, OSRM optional (D-014) | §6, R-07 |
| FPO-first, coordination-not-inventory (DF-1) | §3 |
| Matching is deterministic, not ML (D-011) | No training signal for matching; explainability |
| Price benchmark synthetic by default (D-012) | §7 |

## 12. Sources consulted in the documentation session

| ID | Source | URL |
|---|---|---|
| S-1 | Lok Sabha reply on intermediaries (eparlib) | https://eparlib.nic.in/bitstream/123456789/611033/1/113092.pdf |
| S-2 | CASI, Penn — "Are intermediaries bad?" | https://casi.sas.upenn.edu/node/4969 |
| S-3 | IGC — fresh produce price wedges, Pakistan | https://www.theigc.org/publications/understanding-fresh-produce-supply-chain-dynamics-and-price-wedges-evidence-pakistan |
| S-4 | Financial Express BD — middleman conundrum | https://thefinancialexpress.com.bd/views/price-rises-middleman-conundrum |
| S-5 | data.gov.in — Mandi daily price resource | https://data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi |
| S-6 | PIB — e-NAM 10 years (Apr 2026) | https://static.pib.gov.in/WriteReadData/specificdocs/documents/2026/apr/doc2026413845801.pdf |
| S-7 | Secondary summary of e-NAM Platform of Platforms | https://anantamias.com/e-nam-platform-of-platforms/ |
| S-8 | Outlook Business — Ninjacart | https://www.outlookbusiness.com/power-of-i-2019/ninja-power-5328 |
| S-9 | YourStory — Ninjacart (2016) | https://yourstory.com:443/2016/06/ninjacart |
| S-10 | CB Insights — DeHaat / YourKrishi descriptions | https://www.cbinsights.com/company/ninjacart/alternatives-competitors |
| S-11 | OSRM backend README | https://github.com/GradientDP/osrm-backend |
| S-12 | OSRM API usage policy | https://github.com/Project-OSRM/osrm-backend/wiki/Api-usage-policy |
| S-13 | OSRM demo server page | https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server |
| S-14 | DEV post on Agmarknet API friction and a community wrapper | https://dev.to/shrinivas-sn/agmarknet-api-alternative-a-free-keyless-way-to-get-mandi-prices-in-india-38pg |
| S-15 | AIKosh listing of variety-wise daily market prices | https://aikosh.indiaai.gov.in/home/datasets/details/variety_wise_daily_market_prices_of_commodity.html |

Before a final submission, open S-1, S-6 and S-12 directly and re-confirm the numbers and policy text quoted here.
