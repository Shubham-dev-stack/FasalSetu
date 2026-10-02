export type UserRole =
  | 'farmer'
  | 'fpo'
  | 'buyer_trader'
  | 'buyer_retail'
  | 'buyer_fmcg'
  | 'transporter'
  | 'operator'
  | 'PRODUCER'
  | 'BUYER'
  | 'ADMIN';

export interface UserProfile {
  id: string;
  user_id: string;
  state: string;
  district: string;
  pincode: string;
  lat: number;
  lon: number;
  primary_hub_id?: string | null;
  storage_capacity_mt?: number | null;
  cold_storage_flag?: boolean | null;
  scale_acres?: number | null;
  daily_demand_kg?: number | null;
  vehicle_count?: number | null;
  rating_avg: number;
  rating_count: number;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  role: UserRole;
  name: string;
  phone?: string | null;
  is_active: boolean;
  created_at: string;
  profile?: UserProfile | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Crop {
  code: string;
  name: string;
  perishability_class: 'LOW' | 'MEDIUM' | 'HIGH' | 'VERY_HIGH';
  shelf_life_days: number;
  target_temp_c?: number | null;
  msp_inr_per_quintal?: number | null;
  is_active: boolean;
}

export interface Hub {
  code: string;
  name: string;
  type: 'COLLECTION_CENTER' | 'DISTRIBUTION_HUB' | 'CONSUMPTION_MARKET';
  state: string;
  district: string;
  lat: number;
  lon: number;
  capacity_mt: number;
  cold_storage_mt: number;
  dry_storage_mt: number;
  is_active: boolean;
}

export interface Vehicle {
  code: string;
  name: string;
  vehicle_type: string;
  capacity_payload_kg: number;
  capacity_volume_m3: number;
  cold_storage_flag: boolean;
  cost_per_km_empty: number;
  cost_per_km_loaded: number;
  driver_bata_per_day: number;
  is_active: boolean;
}

export interface ReferenceDataResponse {
  crops: Crop[];
  hubs: Hub[];
  vehicles: Vehicle[];
}

export interface DemoPersona {
  key: string;
  label: string;
  sublabel: string;
  role: UserRole;
  email: string;
  location: string;
}

export const DEMO_PERSONAS: DemoPersona[] = [
  {
    key: 'fpo_sonipat',
    label: 'Sonipat Kisan FPO',
    sublabel: 'Aggregator / Producer',
    role: 'fpo',
    email: 'fpo.sonipat@fasalsetu.internal',
    location: 'Sonipat, Haryana',
  },
  {
    key: 'fpo_meerut',
    label: 'Meerut Kisan Sahkari FPO',
    sublabel: 'Aggregator / Producer',
    role: 'fpo',
    email: 'fpo.meerut@fasalsetu.internal',
    location: 'Meerut, Uttar Pradesh',
  },
  {
    key: 'farmer_karnal',
    label: 'Ramesh Singh',
    sublabel: 'Individual Smallholder',
    role: 'farmer',
    email: 'farmer.karnal@fasalsetu.internal',
    location: 'Karnal, Haryana',
  },
  {
    key: 'buyer_gurugram',
    label: 'FreshMart Supermarkets',
    sublabel: 'Retail Chain Buyer',
    role: 'buyer_retail',
    email: 'buyer.gurugram@fasalsetu.internal',
    location: 'Gurugram, Haryana',
  },
  {
    key: 'buyer_noida',
    label: 'AgroProcure Wholesale',
    sublabel: 'B2B Trader / Aggregator',
    role: 'buyer_trader',
    email: 'buyer.noida@fasalsetu.internal',
    location: 'Noida, Uttar Pradesh',
  },
  {
    key: 'operator',
    label: 'FasalSetu Desk Admin',
    sublabel: 'Platform Ops / Logistics Manager',
    role: 'operator',
    email: 'operator@fasalsetu.internal',
    location: 'Central Control Hub',
  },
];

export interface ProducerProfileOut {
  id: number;
  user_id: number;
  producer_type: 'FARMER' | 'FPO';
  org_name: string;
  state: string;
  district: string;
  locality?: string | null;
  lat: number;
  lng: number;
  member_farmers?: number | null;
  is_demo: boolean;
  created_at: string;
}

export interface ProducerProfileUpdate {
  org_name?: string;
  state?: string;
  district?: string;
  locality?: string | null;
  lat?: number;
  lng?: number;
  member_farmers?: number | null;
}

export interface ProducerSummary {
  id: number;
  org_name: string;
  producer_type: string;
  district: string;
  state: string;
  lat: number;
  lng: number;
}

export interface CropSummary {
  id: number;
  name: string;
  category: string;
  shelf_life_days: number;
  perishability: string;
}

export interface BenchmarkContext {
  nearest_hub_name?: string | null;
  benchmark_modal_per_kg?: number | null;
  benchmark_source?: string | null;
}

export interface LandedEstimate {
  distance_km: number;
  distance_source: string;
  transport_cost_per_kg: number;
  platform_fee_per_kg: number;
  landed_price_per_kg: number;
  basis: string;
}

export interface Listing {
  id: number;
  producer: ProducerSummary;
  crop: CropSummary;
  variety?: string | null;
  grade: 'A' | 'B' | 'C';
  quantity_kg: number;
  quantity_available_kg: number;
  ask_price_per_kg: number;
  min_order_kg: number;
  harvest_date: string;
  available_from: string;
  available_until: string;
  status: 'ACTIVE' | 'SOLD_OUT' | 'EXPIRED' | 'WITHDRAWN';
  is_demo: boolean;
  harvest_age_days: number;
  landed_estimate?: LandedEstimate | null;
  demand_status?: string | null;
  created_at: string;
}

export interface ListingCreateRequest {
  crop_id: number;
  variety?: string | null;
  grade: 'A' | 'B' | 'C';
  quantity_kg: number;
  ask_price_per_kg: number;
  min_order_kg: number;
  harvest_date: string;
  available_from: string;
  available_until: string;
}

export interface ListingUpdateRequest {
  ask_price_per_kg?: number;
  quantity_kg?: number;
  min_order_kg?: number;
  available_until?: string;
  status?: 'WITHDRAWN';
}

export interface ListingCreateResponse {
  listing: Listing;
  warnings: string[];
  benchmark_context?: BenchmarkContext | null;
}

export interface ListingDetailResponse {
  listing: Listing;
  benchmark_context?: BenchmarkContext | null;
}

export interface ListingListResponse {
  items: Listing[];
  total: number;
}

export interface HubSummary {
  id: number;
  name: string;
  state: string;
  lat: number;
  lng: number;
}

export interface BuyerProfileOut {
  id: number;
  user_id: number;
  buyer_type: string;
  org_name: string;
  hub_id: number;
  hub?: HubSummary | null;
  city: string;
  state: string;
  lat: number;
  lng: number;
  is_demo: boolean;
  created_at: string;
}

export interface BuyerProfileUpdate {
  org_name?: string;
  city?: string;
  state?: string;
  hub_id?: number;
  lat?: number;
  lng?: number;
}

export interface BuyerSummary {
  id: number;
  org_name: string;
  buyer_type: string;
  city: string;
  state: string;
  hub_id: number;
  lat: number;
  lng: number;
}

export interface LandedPriceGuidance {
  formula: string;
  note: string;
}

export interface Requirement {
  id: number;
  buyer: BuyerSummary;
  crop: CropSummary;
  grade_min: 'A' | 'B' | 'C';
  quantity_kg: number;
  quantity_fulfilled_kg: number;
  max_landed_price_per_kg: number;
  needed_by: string;
  status: 'OPEN' | 'PARTIALLY_FULFILLED' | 'FULFILLED' | 'CANCELLED' | 'EXPIRED';
  notes?: string | null;
  is_demo: boolean;
  created_at: string;
  landed_guidance?: LandedPriceGuidance | null;
}

export interface RequirementCreateRequest {
  crop_id: number;
  grade_min: 'A' | 'B' | 'C';
  quantity_kg: number;
  max_landed_price_per_kg: number;
  needed_by: string;
  notes?: string | null;
}

export interface RequirementUpdateRequest {
  quantity_kg?: number;
  max_landed_price_per_kg?: number;
  needed_by?: string;
  notes?: string | null;
  status?: 'CANCELLED';
}

export interface RequirementDetailResponse {
  requirement: Requirement;
  landed_guidance?: LandedPriceGuidance | null;
}

export interface RequirementListResponse {
  items: Requirement[];
  total: number;
}

export interface BuyerOrderSummary {
  id: number;
  org_name: string;
  hub_id?: number | null;
}

export interface ProducerOrderSummary {
  id: number;
  org_name: string;
  district: string;
  state: string;
}

export interface CropOrderSummary {
  id: number;
  name: string;
}

export interface OrderEvent {
  id: number;
  order_id: number;
  from_status?: string | null;
  to_status: string;
  actor_user_id: number;
  actor_role: string;
  note?: string | null;
  at: string;
}

export interface Order {
  id: number;
  listing_id: number;
  requirement_id?: number | null;
  buyer: BuyerOrderSummary;
  producer: ProducerOrderSummary;
  crop: CropOrderSummary;
  quantity_kg: number;
  agreed_price_per_kg: number;
  transport_cost_estimate_per_kg: number;
  platform_fee_per_kg: number;
  landed_price_per_kg_estimate: number;
  total_amount_estimate: number;
  delivery_date: string;
  status: 'PLACED' | 'CONFIRMED' | 'REJECTED' | 'CANCELLED' | 'IN_TRANSIT' | 'DELIVERED';
  origin: 'MARKETPLACE' | 'MATCHING';
  shipment_id?: number | null;
  allocated_transport_cost_total?: number | null;
  events: OrderEvent[];
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrderCreateRequest {
  listing_id: number;
  quantity_kg: number;
  delivery_date: string;
  requirement_id?: number | null;
}

export interface OrderTransitionRequest {
  to_status: 'CONFIRMED' | 'REJECTED' | 'CANCELLED';
  note?: string | null;
}

export interface OrderListResponse {
  items: Order[];
  total: number;
}

export interface ForecastHistoryItem {
  date: string;
  demand_kg: number;
  is_synthetic: boolean;
}

export interface ForecastDailyItem {
  date: string;
  day_of_week: string;
  point_forecast_kg: number;
  interval_lo_kg?: number | null;
  interval_hi_kg?: number | null;
}

export interface ForecastDemandResponse {
  hub_id: number;
  hub_name: string;
  crop_id: number;
  crop_name: string;
  cutoff_date: string;
  horizon_days: number;
  method: string;
  model_version: string;
  demand_data_source: string;
  price_feature_sources: string[];
  reproducibility: string;
  disclaimer: string;
  history: ForecastHistoryItem[];
  forecast: ForecastDailyItem[];
}

export interface HubOpportunityItem {
  hub_id: number;
  hub_name: string;
  state: string;
  lat: number;
  lng: number;
  total_forecast_kg: number;
  avg_daily_forecast_kg: number;
  active_supply_kg: number;
  supply_demand_ratio: number;
  opportunity_label: 'HIGH_DEFICIT' | 'BALANCED' | 'OVERSUPPLIED' | string;
  method: string;
}

export interface ForecastHubsResponse {
  crop_id: number;
  crop_name: string;
  cutoff_date: string;
  horizon_days: number;
  demand_data_source: string;
  disclaimer: string;
  hubs: HubOpportunityItem[];
}

export interface ModelInfoResponse {
  model_id: string;
  model_version: string;
  trained_at: string;
  git_commit: string;
  dataset_hash_sha256: string;
  generator_version: string;
  demand_data_source: string;
  price_feature_sources: string[];
  reproducibility: string;
  deployed_method: string;
  deployment_gate: {
    passed: boolean;
    deployed_method: string;
    reason: string;
    val_mae_lgbm?: number;
    min_val_baseline?: number;
    test_mae_lgbm?: number;
    min_test_baseline?: number;
  };
  metrics: {
    validation: Record<string, any>;
    test: Record<string, any>;
  };
  split_spec: Record<string, any>;
  disclaimer: string;
}

export interface MatchingScores {
  price: number;
  distance: number;
  freshness: number;
  fill: number;
  total: number;
}

export interface MatchingWeights {
  price: number;
  distance: number;
  freshness: number;
  fill: number;
}

export interface CandidateProducerSummary {
  id: number;
  org_name: string;
  producer_type?: string | null;
  district?: string | null;
  state?: string | null;
}

export interface CandidateListingSummary {
  id: number;
  producer: CandidateProducerSummary;
  grade: string;
  ask_price_per_kg: number;
  harvest_date: string;
  available_from: string;
  available_until: string;
  min_order_kg: number;
}

export interface Candidate {
  rank: number;
  listing: CandidateListingSummary;
  available_kg: number;
  allocated_kg: number;
  distance_km: number;
  distance_source: string;
  transit_hours: number;
  age_at_delivery_days: number;
  ask_price_per_kg: number;
  transport_cost_per_kg: number;
  platform_fee_per_kg: number;
  landed_price_per_kg: number;
  scores: MatchingScores;
  weights: MatchingWeights;
  reasons: string[];
}

export interface AllocationItem {
  listing_id: number;
  quantity_kg: number;
}

export interface NearMiss {
  listing_id: number;
  excluded_reason: 'BUDGET' | 'GRADE' | 'DISTANCE' | 'FRESHNESS' | 'AVAILABILITY' | 'BELOW_MIN_ORDER';
  detail: string;
  landed_price_per_kg?: number | null;
  distance_km?: number | null;
}

export interface MatchingCandidatesResponse {
  requirement: {
    id: number;
    crop: { id: number; name: string };
    grade_min: string;
    quantity_kg: number;
    quantity_fulfilled_kg: number;
    max_landed_price_per_kg: number;
    needed_by: string;
    status: string;
  };
  fill_status: 'FULL' | 'PARTIAL' | 'NONE';
  requested_kg: number;
  fulfilled_kg: number;
  shortfall_kg: number;
  earliest_delivery_date: string | null;
  allocations: AllocationItem[];
  candidates: Candidate[];
  near_misses: NearMiss[];
}

export interface MatchingAcceptRequest {
  requirement_id: number;
  allocations: AllocationItem[];
  delivery_date: string;
}

export interface MatchingAcceptResponse {
  orders: Order[];
  requirement: {
    id: number;
    status: string;
    quantity_fulfilled_kg: number;
  };
}

export interface ProducerOpportunity {
  requirement: {
    id: number;
    crop: { id: number; name: string };
    grade_min: string;
    quantity_kg: number;
    quantity_fulfilled_kg: number;
    max_landed_price_per_kg: number;
    needed_by: string;
  };
  buyer: {
    id: number;
    org_name: string;
    buyer_type: string;
    city?: string | null;
    state?: string | null;
  };
  distance_km: number;
  landed_price_per_kg: number;
  scores: MatchingScores;
  reasons: string[];
}

export interface ProducerOpportunitiesResponse {
  listing: {
    id: number;
    crop: { id: number; name: string };
    grade: string;
    quantity_available_kg: number;
    ask_price_per_kg: number;
  };
  opportunities: ProducerOpportunity[];
  hub_context?: {
    hub: { id: number; name: string };
    forecast_7d_kg: number;
    status: 'SHORTAGE' | 'BALANCED' | 'SURPLUS';
  } | null;
}

export interface VehiclePlanLeg {
  vehicle_type: string;
  capacity_kg: number;
  load_kg: number;
  trips: number;
  trip_cost: number;
  total_cost: number;
}

export interface LogisticsEstimateRequest {
  listing_id: number;
  quantity_kg: number;
  buyer_id?: number | null;
  dest_lat?: number | null;
  dest_lng?: number | null;
}

export interface LogisticsEstimateResponse {
  distance_km: number;
  distance_source: string;
  vehicle_plan: VehiclePlanLeg[];
  trips: number;
  cost_total: number;
  cost_per_kg: number;
  transit_hours: number;
  basis: string;
}

export interface FleetVehicle {
  id: number;
  name: string;
  vehicle_type: string;
  capacity_kg: number;
  cost_per_km: number;
  fixed_cost_per_trip: number;
  avg_speed_kmph: number;
  depot_name: string;
  depot_lat: number;
  depot_lng: number;
  is_available: boolean;
  is_demo: boolean;
}

export interface VehicleListResponse {
  items: FleetVehicle[];
}

export interface StopOut {
  sequence: number;
  stop_type: 'DEPOT_START' | 'PICKUP' | 'DROP' | 'DEPOT_END';
  order_id?: number | null;
  label: string;
  lat: number;
  lng: number;
  load_after_kg: number;
  cum_distance_km: number;
  eta_min_from_start: number;
}

export interface PlanVehicleOut {
  id: number;
  name: string;
  vehicle_type: string;
  capacity_kg: number;
}

export interface PlanShipmentOut {
  temp_id: string;
  shipment_id?: number | null;
  vehicle: PlanVehicleOut;
  total_distance_km: number;
  total_cost: number;
  peak_load_kg: number;
  utilization_pct: number;
  est_duration_min: number;
  stops: StopOut[];
  geometry: [number, number][];
}

export interface PlanTotals {
  optimized_km: number;
  optimized_cost: number;
  baseline_km: number;
  baseline_cost: number;
  savings_km: number;
  savings_cost: number;
  savings_pct_cost: number;
  vehicles_used: number;
  avg_utilization_pct: number;
}

export interface UnassignedOrder {
  order_id: number;
  quantity_kg: number;
  reason: string;
}

export interface RoutePlanResponse {
  plan_id: string;
  status: 'PROPOSED' | 'APPROVED' | 'DISCARDED';
  method: string;
  solver_status?: string | null;
  solve_time_ms: number;
  distance_source: string;
  totals: PlanTotals;
  baseline_note: string;
  shipments: PlanShipmentOut[];
  unassigned: UnassignedOrder[];
  skipped_order_ids: number[];
  warnings: string[];
}

export interface RoutePlanSummaryItem {
  id: string;
  status: 'PROPOSED' | 'APPROVED' | 'DISCARDED';
  method: string;
  orders_count: number;
  vehicles_used: number;
  optimized_km: number;
  optimized_cost: number;
  savings_pct: number;
  created_at: string;
  approved_at?: string | null;
}

export interface RoutePlanListResponse {
  items: RoutePlanSummaryItem[];
  total: number;
}

export interface ShipmentDetailResponse {
  id: number;
  plan_id: string;
  vehicle_id: number;
  vehicle_name: string;
  vehicle_type: string;
  status: 'PLANNED' | 'DISPATCHED' | 'DELIVERED';
  total_distance_km: number;
  total_cost: number;
  peak_load_kg: number;
  utilization_pct: number;
  est_duration_min: number;
  stops: StopOut[];
  order_ids: number[];
}

export interface RoutePlanApproveResponse {
  plan: RoutePlanResponse;
  shipments: ShipmentDetailResponse[];
}

export interface OptimizeRoutesRequest {
  order_ids?: number[];
  time_limit_s?: number;
  distance_mode?: 'HAVERSINE' | 'OSRM';
}

export interface WaterfallPerKg {
  farmgate: number;
  transport: number;
  platform_fee: number;
  landed: number;
}

export interface WaterfallTotals {
  farmgate_total: number;
  transport_total: number;
  platform_fee_total: number;
  landed_total: number;
}

export interface PricingCropInfo {
  id: number;
  name: string;
}

export interface PricingHubInfo {
  id: number;
  name: string;
  city?: string | null;
  state?: string | null;
}

export interface BenchmarkInfo {
  hub: PricingHubInfo;
  market_name: string;
  price_date: string;
  modal_price_per_kg: number;
  min_price_per_kg: number;
  max_price_per_kg: number;
  source: 'SYNTHETIC_DEMO' | 'AGMARKNET_SNAPSHOT' | string;
  is_synthetic: boolean;
}

export interface ScenarioAssumptions {
  platform_fee_pct: number;
  commission_agent_pct: number;
  trader_margin_pct: number;
  retail_margin_pct: number;
  last_mile_cost_per_kg: number;
}

export interface TraditionalScenario {
  farmer_mandi_net_per_kg: number;
  buyer_traditional_per_kg: number;
  delta_farmer_pct: number;
  delta_buyer_pct: number;
  assumptions: ScenarioAssumptions;
}

export interface FairBand {
  low: number;
  high: number;
}

export interface TrendPoint {
  date: string;
  modal_price_per_kg: number;
}

export interface OrderPriceBreakdownResponse {
  order_id: number;
  crop: PricingCropInfo;
  quantity_kg: number;
  per_kg: WaterfallPerKg;
  totals: WaterfallTotals;
  transport_basis: 'ALLOCATED_ROUTE' | 'ESTIMATE' | string;
  benchmark?: BenchmarkInfo | null;
  scenario?: TraditionalScenario | null;
  fair_band?: FairBand | null;
  basis: string;
  disclaimer: string;
}

export interface PricingBenchmarkResponse {
  hub: PricingHubInfo;
  benchmark?: BenchmarkInfo | null;
  trend: TrendPoint[];
  fair_band?: FairBand | null;
  assumptions: ScenarioAssumptions;
  basis: string;
  disclaimer: string;
}




