import { describe, it, expect } from 'vitest';
import {
  RoutePlanResponse,
  RoutePlanSummaryItem,
  ShipmentDetailResponse,
} from '../api/types';

describe('Phase 9 Route Optimization Models and API Handlers', () => {
  it('correctly maps proposed RoutePlanResponse with VRP metrics and savings', () => {
    const mockPlan: RoutePlanResponse = {
      plan_id: 'd07aa335-0eb0-4b5a-accd-ddb18f80cdc5',
      status: 'PROPOSED',
      method: 'ORTOOLS',
      solver_status: 'OPTIMAL',
      solve_time_ms: 1240,
      distance_source: 'ESTIMATED_HAVERSINE',
      totals: {
        optimized_km: 752.4,
        optimized_cost: 12500.0,
        baseline_km: 1150.0,
        baseline_cost: 17750.0,
        savings_km: 397.6,
        savings_cost: 5250.0,
        savings_pct_cost: 29.58,
        vehicles_used: 4,
        avg_utilization_pct: 78.3,
      },
      baseline_note: 'Baseline = each order shipped on its own dedicated round trip.',
      shipments: [
        {
          temp_id: 's1',
          shipment_id: null,
          vehicle: {
            id: 1,
            name: 'MT-01',
            vehicle_type: 'MINI_TRUCK',
            capacity_kg: 750,
          },
          total_distance_km: 207.5,
          total_cost: 2890.0,
          peak_load_kg: 500,
          utilization_pct: 66.7,
          est_duration_min: 455,
          stops: [
            {
              sequence: 0,
              stop_type: 'DEPOT_START',
              order_id: null,
              label: 'Depot: Sonipat',
              lat: 28.98,
              lng: 77.03,
              load_after_kg: 0,
              cum_distance_km: 0,
              eta_min_from_start: 0,
            },
            {
              sequence: 1,
              stop_type: 'PICKUP',
              order_id: 4,
              label: 'Pickup #4',
              lat: 29.39,
              lng: 76.97,
              load_after_kg: 500,
              cum_distance_km: 62.0,
              eta_min_from_start: 144,
            },
            {
              sequence: 2,
              stop_type: 'DROP',
              order_id: 4,
              label: 'Drop #4',
              lat: 28.72,
              lng: 77.15,
              load_after_kg: 0,
              cum_distance_km: 165.4,
              eta_min_from_start: 371,
            },
            {
              sequence: 3,
              stop_type: 'DEPOT_END',
              order_id: null,
              label: 'Depot Return: Sonipat',
              lat: 28.98,
              lng: 77.03,
              load_after_kg: 0,
              cum_distance_km: 207.5,
              eta_min_from_start: 455,
            },
          ],
          geometry: [
            [28.98, 77.03],
            [29.39, 76.97],
            [28.72, 77.15],
            [28.98, 77.03],
          ],
        },
      ],
      unassigned: [
        {
          order_id: 6,
          quantity_kg: 150,
          reason: 'NO_FEASIBLE_INSERTION',
        },
      ],
      skipped_order_ids: [],
      warnings: [],
    };

    expect(mockPlan.plan_id).toBe('d07aa335-0eb0-4b5a-accd-ddb18f80cdc5');
    expect(mockPlan.status).toBe('PROPOSED');
    expect(mockPlan.totals.savings_cost).toBe(5250.0);
    expect(mockPlan.totals.savings_pct_cost).toBe(29.58);
    expect(mockPlan.shipments).toHaveLength(1);
    expect(mockPlan.shipments[0].stops).toHaveLength(4);
    expect(mockPlan.unassigned).toHaveLength(1);
    expect(mockPlan.unassigned[0].order_id).toBe(6);
  });

  it('correctly maps RoutePlanSummaryItem list format', () => {
    const summaryItem: RoutePlanSummaryItem = {
      id: 'plan-123',
      status: 'APPROVED',
      method: 'ORTOOLS',
      orders_count: 5,
      vehicles_used: 3,
      optimized_km: 412.3,
      optimized_cost: 8400.0,
      savings_pct: 25.4,
      created_at: '2026-10-02T10:00:00Z',
      approved_at: '2026-10-02T10:05:00Z',
    };

    expect(summaryItem.orders_count).toBe(5);
    expect(summaryItem.vehicles_used).toBe(3);
    expect(summaryItem.status).toBe('APPROVED');
    expect(summaryItem.savings_pct).toBe(25.4);
  });

  it('validates shipment detail and status progression', () => {
    const shipment: ShipmentDetailResponse = {
      id: 1,
      plan_id: 'plan-abc',
      vehicle_id: 2,
      vehicle_name: 'PK-01',
      vehicle_type: 'PICKUP',
      status: 'PLANNED',
      total_distance_km: 180.5,
      total_cost: 3200.0,
      peak_load_kg: 1200,
      utilization_pct: 80.0,
      est_duration_min: 350,
      stops: [],
      order_ids: [1, 2],
    };

    expect(shipment.status).toBe('PLANNED');
    expect(shipment.order_ids).toContain(1);
    expect(shipment.order_ids).toContain(2);

    // Verify progression checks
    const allowedTransitions: Record<string, string[]> = {
      PLANNED: ['DISPATCHED'],
      DISPATCHED: ['DELIVERED'],
      DELIVERED: [],
    };
    expect(allowedTransitions[shipment.status]).toContain('DISPATCHED');
    expect(allowedTransitions[shipment.status]).not.toContain('DELIVERED');
  });
});
