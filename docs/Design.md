# Design — KrishiSetu UI/UX specification

Status: PLANNED. Screens map to API.md endpoints and Architecture.md routes. Mobile-first (360 px baseline), then 768 px and 1280 px.

## 1. Design philosophy

| Principle | Meaning in this product |
|---|---|
| Trustworthy | Every number shows where it came from (badge: Computed · Modelled · Synthetic). Assumptions are one tap away. |
| Farmer-friendly | Short words, big touch targets (≥44 px), one primary action per screen, icons with text, numbers with units (₹/kg, kg). Hindi labels for the listing flow are NICE. |
| Agriculture-focused | Earthy green/amber palette, crop icons, kg/quintal language, hub and district names — not a catalogue grid of product photos. |
| Not Amazon | No cart, no star ratings, no "deals", no promo banners, no product photography. Cards are data cards (crop, grade, qty, price band, distance, freshness). The centrepiece is the loop: Predict → Match → Move → Sell → Analyse. |
| Clear | One idea per card; progressive disclosure via "Why?" drawers. |
| Fast | Skeletons, no blocking spinners for lists, optimistic UI only for safe actions. |

## 2. Visual system (tokens in `styles/tokens.css`, mapped into `tailwind.config.ts`)

| Token | Value | Use |
|---|---|---|
| `--primary` | `#2E7D32` | primary buttons, active nav |
| `--primary-soft` | `#E8F5E9` | selected rows, info panels |
| `--accent` | `#F59E0B` | highlights, DEMO badge background (text dark) |
| `--ink` | `#1F2937` | body text |
| `--muted` | `#6B7280` | secondary text |
| `--surface` | `#FFFFFF` · `--bg` `#F7F8F5` | cards · page |
| `--success` `#2E7D32` · `--warning` `#B45309` · `--danger` `#B91C1C` · `--info` `#1D4ED8` | status colours |
| Radius | 12 px cards, 8 px inputs | |
| Font | `Noto Sans` (+ `Noto Sans Devanagari` when Hindi is on), base 16 px, numbers tabular | |
| Spacing | 4-px scale; card padding 16 (mobile) / 20 (desktop) | |

Contrast must be verified with a checker in Phase 12 (no contrast ratios are claimed here). Colour is never the only status carrier — chips include an icon and text.

## 3. Information architecture and navigation

Routes (authoritative; matches Architecture.md):

```
/login
/market                       /market/:listingId (S)
/forecast
/analytics
/orders                       /orders/:orderId
/producer/listings            /producer/listings/new     /producer/listings/:id (S)
/buyer/requirements           /buyer/requirements/new    /buyer/requirements/:id/match
/ops/logistics                /ops/routes/:planId
```

| Role | Bottom nav (mobile) / sidebar (desktop) |
|---|---|
| PRODUCER | My Listings · Demand · Market · Orders · Analytics |
| BUYER | Requirements · Market · Demand · Orders · Analytics |
| ADMIN (Operator) | Logistics · Orders · Market · Demand · Analytics |

Top bar: logo · page title · **DEMO DATA** badge (always when `VITE_DEMO_MODE`) · persona switcher (demo only) · user menu. Bottom nav shows max 5 items (mobile); sidebar on ≥1024 px.

## 4. User flows

| Flow | Screens |
|---|---|
| F1 Producer lists | My Listings → New Listing (form + Demand panel) → success toast → listing in list (ACTIVE) |
| F2 Buyer matches | Requirements → New Requirement → Match screen → Accept → Orders (PLACED) |
| F3 Confirm | Orders → Order detail → Confirm |
| F4 Plan movement | Logistics → select orders → Optimize → Plan page → Approve → Dispatch → Deliver |
| F5 Inspect price | Order detail → price waterfall → "Assumptions" drawer |
| F6 Analyse | Analytics → supply-demand row → Forecast page (deep link) |

## 5. Shared components

| Component | Spec |
|---|---|
| `StatusChip` | icon + label; colours per table in §14 |
| `DataSourceBadge` | `Synthetic` (amber outline), `Modelled` (blue outline), `Computed` (green outline), `Agmarknet snapshot · <dates>` (green) |
| `MetricCard` | label, value, unit, optional delta, source badge |
| `Field` | label above input, helper text, inline error text (red + icon), required mark |
| `QuantityInput` | numeric, kg suffix, stepper buttons optional, blocks non-numeric |
| `PriceInput` | ₹ prefix, /kg suffix |
| `Drawer` | bottom sheet on mobile, right panel on desktop; used for "Why this score?", "Assumptions", "Model card" |
| `EmptyState` | icon, one sentence, primary action |
| `ErrorState` | message from envelope, Retry button, request id if available |
| `Skeleton` | card/table/chart variants |
| `Toast` | success/error, auto-dismiss 5 s, `aria-live=polite` |
| `Table` | sticky header, horizontal scroll container on mobile; below 640 px rows collapse into stacked cards |

## 6. Screen specifications (exact UI hierarchy)

### 6.1 Login `/login`
```
Page
├─ Brand header (logo, tagline "Predict · Match · Move · Sell · Analyse")
├─ DEMO notice (when demo mode): "Demo data only. All records are synthetic."
├─ LoginForm: Email · Password · [Sign in]
└─ DemoPersonas (demo mode): 6 persona buttons (FPO Sonipat, FPO Meerut, Farmer Karnal, Buyer Gurugram, Buyer Noida, Operator) → POST /auth/demo-login
```

### 6.2 My Listings `/producer/listings`
```
Page
├─ Header: title · [+ New listing] (primary)
├─ Filters: status chips (Active · Sold out · Expired · Withdrawn)
├─ ListingCard × n  (crop icon, crop+grade, qty available / total, ask ₹/kg, PriceBand marker, expires in N days, StatusChip, [Edit] [Withdraw])
└─ States: loading skeleton ×3 · empty ("No listings yet" + New listing) · error
```

### 6.3 New Listing `/producer/listings/new`  ← PREDICT lives here
```
Page (mobile: single column, Demand panel collapses under form as accordion "Demand intelligence"; desktop: 2 columns 60/40)
├─ ListingForm
│  ├─ Crop select (icons) → Grade (A/B/C segmented) → Variety (optional)
│  ├─ QuantityInput · PriceInput (ask) with live PriceBand hint "Fair band ₹L–₹U (Modelled)"
│  ├─ Min order (kg) · Harvest date · Available from · Available until
│  ├─ Inline validation (mirrors Data.md §8) · warning banner if ask ≫ benchmark
│  └─ [Publish listing] (disabled until valid)
└─ DemandPanel  (updates on crop/quantity change, debounced 400 ms)
   ├─ Banner: DataSourceBadge Synthetic + "Forecast trained on synthetic data" (link → model card drawer)
   ├─ HubRanking: top 3 hubs: name, 7-day forecast kg, supply/demand StatusChip (Shortage/Balanced/Surplus), est. net ₹/kg (Indicative), distance
   ├─ ForecastChart for selected hub (history 28 d, forecast 7 d, 80% band; fallback label if method≠LIGHTGBM)
   └─ PriceBand: benchmark modal ₹/kg (source badge) and fair band
```

### 6.4 Requirements `/buyer/requirements` and New `/buyer/requirements/new`
```
List: RequirementCard (crop, min grade, qty, fulfilled progress bar, max landed ₹/kg, needed by, StatusChip, [Find matches])
Form: Crop · Min grade · Quantity · Max LANDED price ₹/kg (helper: "price delivered to you, including transport and fee") · Needed by · [Post requirement]
```

### 6.5 Match screen `/buyer/requirements/:id/match`  ← MATCH
```
Page
├─ RequirementSummary (crop, grade, qty, budget, needed by)
├─ AllocationSummary: fill bar (fulfilled / requested), StatusChip FULL|PARTIAL|NONE, shortfall banner (amber) "Short by 700 kg — no more eligible supply"
├─ CandidateList (ranked)
│  └─ CandidateCard: rank · producer (FPO/Farmer icon) · allocated qty · ask ₹ · transport ₹ · fee ₹ · LANDED ₹ (bold) · distance (Estimated) · freshness days
│     ├─ ScoreBreakdown: 4 bars (Price, Distance, Freshness, Fill) + total
│     ├─ Reasons list (from API)
│     └─ [Why this rank?] → Drawer with weights
├─ NearMisses (collapsed): excluded listings with reason chip (Budget · Grade · Distance · Freshness · Min order)
├─ Empty (NONE): EmptyState "No listing fits your budget" + best near-miss gaps ("₹3.2/kg over budget")
└─ Sticky footer: Delivery date · total landed ₹ · [Accept allocation] (primary)
```

### 6.6 Marketplace `/market`
```
Page
├─ Filters (mobile: sheet; desktop: left rail): Crop · Grade · State · Price max · Freshness (harvested ≤ N days) · Sort (Landed price, Distance, Freshness)
├─ MarketCard grid (1 col mobile, 2 tablet, 3 desktop): crop+grade · producer · available kg · ask ₹/kg · landed est. ₹/kg (buyers, "Estimated") · distance · harvest age · demand StatusChip
└─ States: skeleton · empty ("No listings match filters" + Clear filters) · error
```

### 6.7 Demand dashboard `/forecast`
```
Page
├─ Banner (always): "Synthetic demand data. Metrics validate the pipeline, not real-world accuracy."
├─ Selectors: Hub · Crop · Horizon (3/5/7 d)
├─ ForecastChart (history, forecast, band; tooltip with values)
├─ StatGrid: 7-day total · vs last 7 days % · method · model version
├─ SupplyDemandTable (all hubs for selected crop): forecast 7d, supply, ratio, StatusChip
└─ ModelCard drawer: metrics (val/test, baselines, coverage), splits, data range, gate result
```

### 6.8 Orders `/orders` and Order detail `/orders/:orderId`  ← SELL
```
List: OrderRow/Card (id, crop, qty, parties, total farmgate ₹, StatusChip, delivery date) · filters by status
Detail
├─ Header: order id, StatusChip, action buttons by role/state (Confirm · Reject · Cancel · override badge for Operator)
├─ Parties & quantities card
├─ OrderTimeline (Placed → Confirmed → In transit → Delivered, with timestamps; manual-status note)
├─ PriceWaterfall (chart): Farmgate → + Transport → + Platform fee → = Landed
│  ├─ Benchmark markers: Mandi modal (source badge), Farmer mandi-net (Modelled), Buyer traditional (Modelled)
│  ├─ Two delta chips: "Farmer: +x% vs mandi-net scenario" · "Buyer: −y% vs traditional scenario" (label: Modelled scenario)
│  └─ [Assumptions] drawer listing every pricing.yaml value
└─ ShipmentCard (if planned): vehicle, stops, link to plan
```

### 6.9 Ops Logistics `/ops/logistics`  ← MOVE
```
Page
├─ Header: [Optimize routes] (primary, disabled until ≥1 order selected)
├─ OrdersPool table (CONFIRMED & unrouted): checkbox · order · pickup→drop · qty · crop · needed date; "Select all"
├─ Fleet table: vehicle, type, capacity, rate, depot
├─ Options (collapsed): solver time limit (default 5 s), distance mode (Estimated · Road via OSRM if enabled)
├─ RecentPlans list: status chip (Proposed/Approved/Discarded), savings, link
└─ States: empty pool ("No confirmed orders to route") · solving (progress text "Optimizing… up to 5 s") · error
```

### 6.10 Route plan `/ops/routes/:planId`
```
Page
├─ PlanHeader: StatusChip (Proposed/Approved/Discarded), method (OR-Tools / Greedy fallback), distance source badge (Estimated / Road), solve time
├─ KPI row: Total km · Total ₹ · Vehicles used · Avg utilisation · Savings vs baseline (km, ₹, %) with note "baseline = modelled unconsolidated trips"
├─ RouteMap (Leaflet, OSM attribution): colour+number per vehicle, numbered stops, depot markers, polyline; fallback: schematic list if tiles fail
├─ VehicleRouteList (accordion per vehicle): stop table (seq, type Pickup/Drop, place, order, load after, cum km, ETA min)
├─ Unassigned (amber): order chunk, qty, reason chip (Capacity · Duration · No feasible insertion)
└─ Footer actions (Proposed): [Discard] [Approve plan]; (Approved): per-shipment [Dispatch] → [Mark delivered] (manual; labelled "Status is updated manually")
```

### 6.11 Analytics `/analytics`  ← ANALYSE
```
Page
├─ Banner: "All figures are computed from synthetic demo records."
├─ KPI grid (MetricCard ×8): committed orders · volume kg · value ₹ · requirement fill rate · avg logistics ₹/kg · route km saved · route ₹ saved · avg utilisation
├─ Modelled price gap: two cards (Farmer vs mandi-net scenario, Buyer vs traditional scenario) with [Assumptions] drawer
├─ OrdersChart (14 days: orders & kg)
├─ SupplyDemandTable (hub × crop) with filter
└─ Model card link
```

### 6.12 Operator/admin extras
Persona switcher and `Reset demo data` (confirm dialog) in the user menu, visible only in demo mode. No separate admin dashboard (analytics covers it).

## 7. Forms
Labels above inputs; helper text under; errors inline and summarised at top on submit; `inputmode="decimal"` for numeric fields; dates use native pickers; submit button shows "Saving…" and disables; server `details[]` mapped to fields.

## 8. Cards and tables
Cards: single-purpose, max 5 data rows visible, rest behind "Details". Tables: numeric columns right-aligned with units in header; ≥640 px real table, <640 px stacked rows.

## 9. Charts
Recharts. Forecast: history line (solid), forecast line (dashed), band area (10% opacity). Waterfall: stacked bars with labelled segments. Axis units always shown. Every chart has a text summary (`aria-label` + visible caption) and a data-table fallback via "View data".

## 10. Filters
Persist in URL query params; "Clear filters" always visible when any active; filter counts shown on mobile sheet button.

## 11. Status states (chips)

| Entity | Status → colour · icon |
|---|---|
| Listing | ACTIVE green · SOLD_OUT grey · EXPIRED grey · WITHDRAWN grey |
| Requirement | OPEN blue · PARTIALLY_FULFILLED amber · FULFILLED green · CANCELLED/EXPIRED grey |
| Order | PLACED blue · CONFIRMED green · REJECTED red · CANCELLED grey · IN_TRANSIT amber · DELIVERED green (check) |
| Plan | PROPOSED blue · APPROVED green · DISCARDED grey |
| Shipment | PLANNED blue · DISPATCHED amber · DELIVERED green |
| Supply/demand | SHORTAGE red (demand exceeds supply — good for producers) · BALANCED green · SURPLUS amber |

## 12. Loading, empty, error states

Every data screen implements all three (AC-UI-02). Loading: skeletons matching layout. Empty: sentence + next action. Error: envelope `message`, Retry, and for 401 redirect to login, 403 shows "Not allowed for your role". Forecast-specific: fallback banner "Using a simple fallback estimate". Routing-specific: banner "Road distances unavailable — using estimated distances".

## 13. Responsive behaviour

| Width | Layout |
|---|---|
| 360–639 | single column, bottom nav, filters in sheet, tables stacked, map 60 vh with list below |
| 640–1023 | 2-column grids, bottom nav |
| ≥1024 | sidebar nav, 2-column forms (form + Demand panel), map beside stop list |
No horizontal page scroll at any width (AC-UI-01); wide tables scroll inside their container.

## 14. Accessibility
Semantic landmarks; visible focus ring (2 px `--primary` offset); all inputs labelled; errors linked with `aria-describedby`; toasts `aria-live`; charts have text alternatives; map has a keyboard-reachable list alternative; touch targets ≥44 px; `prefers-reduced-motion` respected; language attribute set; status never colour-only.

## 15. Microinteractions
Button press feedback; score bars animate 300 ms on first render; fill bar animates on allocation change; skeleton shimmer; toast slide-in; route polyline draws once (skipped under reduced motion); accept button shows success check. No decorative animation elsewhere.

## 16. Copy rules
Use "Estimated", "Modelled", "Synthetic", "Indicative" wherever true. Never "Live", "Real-time", "Guaranteed", "Saves farmers ₹X". Microcopy for max landed price, baseline and scenario is fixed in `frontend/src/lib/copy.ts` so wording stays consistent with Rules.md §5.
