export type UserRole =
  | 'farmer'
  | 'fpo'
  | 'buyer_trader'
  | 'buyer_retail'
  | 'buyer_fmcg'
  | 'transporter'
  | 'operator';

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

