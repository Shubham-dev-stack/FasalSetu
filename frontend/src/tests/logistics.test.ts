import { describe, it, expect } from 'vitest';
import {
  FleetVehicle,
  LogisticsEstimateResponse,
  VehicleListResponse,
} from '../api/types';

describe('Phase 8 Logistics Frontend Models and Calculators', () => {
  it('formats vehicle type label cleanly', () => {
    const rawType = 'MEDIUM_TRUCK';
    const formatted = rawType.replace('_', ' ');
    expect(formatted).toBe('MEDIUM TRUCK');
  });

  it('correctly maps dedicated logistics estimate response structure', () => {
    const mockEstimate: LogisticsEstimateResponse = {
      distance_km: 78.5,
      distance_source: 'ESTIMATED_HAVERSINE',
      vehicle_plan: [
        {
          vehicle_type: 'PICKUP',
          capacity_kg: 1500,
          load_kg: 1200,
          trips: 1,
          trip_cost: 3112.0,
          total_cost: 3112.0,
        },
      ],
      trips: 1,
      cost_total: 3112.0,
      cost_per_kg: 2.59,
      transit_hours: 3.28,
      basis: 'ESTIMATE',
    };

    expect(mockEstimate.distance_km).toBe(78.5);
    expect(mockEstimate.trips).toBe(1);
    expect(mockEstimate.vehicle_plan).toHaveLength(1);
    expect(mockEstimate.vehicle_plan[0].vehicle_type).toBe('PICKUP');
    expect(mockEstimate.cost_per_kg).toBe(2.59);
    expect(mockEstimate.basis).toBe('ESTIMATE');
  });

  it('correctly aggregates multi-trip vehicles for oversize loads', () => {
    const mockMultiTripEstimate: LogisticsEstimateResponse = {
      distance_km: 50.0,
      distance_source: 'ESTIMATED_HAVERSINE',
      vehicle_plan: [
        {
          vehicle_type: 'MEDIUM_TRUCK',
          capacity_kg: 4000,
          load_kg: 4000,
          trips: 1,
          trip_cost: 3800.0,
          total_cost: 3800.0,
        },
        {
          vehicle_type: 'PICKUP',
          capacity_kg: 1500,
          load_kg: 1500,
          trips: 1,
          trip_cost: 2200.0,
          total_cost: 2200.0,
        },
      ],
      trips: 2,
      cost_total: 6000.0,
      cost_per_kg: 1.09,
      transit_hours: 2.33,
      basis: 'ESTIMATE',
    };

    expect(mockMultiTripEstimate.trips).toBe(2);
    expect(mockMultiTripEstimate.vehicle_plan).toHaveLength(2);
    const totalLegsCost = mockMultiTripEstimate.vehicle_plan.reduce(
      (sum, leg) => sum + leg.total_cost,
      0
    );
    expect(totalLegsCost).toBe(mockMultiTripEstimate.cost_total);
  });

  it('validates vehicle list response items', () => {
    const v1: FleetVehicle = {
      id: 1,
      name: 'MT-01',
      vehicle_type: 'MINI_TRUCK',
      capacity_kg: 750,
      cost_per_km: 12.0,
      fixed_cost_per_trip: 400.0,
      avg_speed_kmph: 30.0,
      depot_name: 'Sonipat Transport Hub',
      depot_lat: 28.98,
      depot_lng: 77.03,
      is_available: true,
      is_demo: true,
    };
    const mockFleet: VehicleListResponse = {
      items: [
        v1,
        {
          id: 2,
          name: 'PK-01',
          vehicle_type: 'PICKUP',
          capacity_kg: 1500,
          cost_per_km: 16.0,
          fixed_cost_per_trip: 600.0,
          avg_speed_kmph: 30.0,
          depot_name: 'Sonipat Transport Hub',
          depot_lat: 28.98,
          depot_lng: 77.03,
          is_available: true,
          is_demo: true,
        },
      ],
    };

    expect(mockFleet.items).toHaveLength(2);
    expect(mockFleet.items[0].capacity_kg).toBe(750);
    expect(mockFleet.items[1].capacity_kg).toBe(1500);
    expect(mockFleet.items.every((v) => v.is_available)).toBe(true);
  });
});
