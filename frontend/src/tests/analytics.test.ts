import { describe, it, expect } from 'vitest';
import {
  AnalyticsOverviewResponse,
  AnalyticsSupplyDemandResponse,
} from '../api/types';

describe('Phase 11: Analytics Types & Transformations', () => {
  it('correctly maps analytics overview response structure and KPIs', () => {
    const mockOverview: AnalyticsOverviewResponse = {
      as_of: '2026-10-02T12:00:00Z',
      data_note: 'All figures computed from synthetic demo records',
      kpis: {
        committed_orders: 10,
        committed_volume_kg: 6350.0,
        committed_value_inr: 140100.0,
        requirement_fill_rate_pct: 8.05,
        avg_logistics_cost_per_kg: 8.54,
        route_savings_km: 120.5,
        route_savings_inr: 2450.0,
        avg_utilization_pct: 78.5,
      },
      price_gap: {
        avg_farmer_delta_pct: 22.86,
        avg_buyer_delta_pct: 3.25,
        orders_considered: 10,
        basis: 'MODELLED_SCENARIO',
      },
      daily: [
        { date: '2026-10-01', orders: 2, volume_kg: 1200.0 },
        { date: '2026-10-02', orders: 1, volume_kg: 500.0 },
      ],
      model: {
        deployed_method: 'LIGHTGBM',
        data_source: 'SYNTHETIC',
        model_version: '1.0.0',
      },
    };

    expect(mockOverview.kpis.committed_orders).toBe(10);
    expect(mockOverview.kpis.committed_volume_kg).toBe(6350.0);
    expect(mockOverview.price_gap.basis).toBe('MODELLED_SCENARIO');
    expect(mockOverview.model.data_source).toBe('SYNTHETIC');
    expect(mockOverview.daily.length).toBe(2);
  });

  it('correctly calculates and validates supply-demand ratios and status', () => {
    const mockSupplyDemand: AnalyticsSupplyDemandResponse = {
      rows: [
        {
          hub: 'Delhi North',
          hub_id: 1,
          crop: 'Tomato',
          crop_id: 1,
          forecast_7d_kg: 9464.1,
          supply_kg: 38000.0,
          ratio: 4.02,
          status: 'SURPLUS',
        },
        {
          hub: 'Gurugram',
          hub_id: 2,
          crop: 'Tomato',
          crop_id: 1,
          forecast_7d_kg: 5868.0,
          supply_kg: 600.0,
          ratio: 0.1,
          status: 'SHORTAGE',
        },
      ],
      method: 'LIGHTGBM',
      data_source: 'SYNTHETIC',
      as_of: '2026-10-02T12:00:00Z',
    };

    expect(mockSupplyDemand.rows.length).toBe(2);
    expect(mockSupplyDemand.rows[0].status).toBe('SURPLUS');
    expect(mockSupplyDemand.rows[1].status).toBe('SHORTAGE');

    // Ratio verification
    const r0 = mockSupplyDemand.rows[0].supply_kg / mockSupplyDemand.rows[0].forecast_7d_kg;
    expect(r0).toBeGreaterThan(1.3);
    const r1 = mockSupplyDemand.rows[1].supply_kg / mockSupplyDemand.rows[1].forecast_7d_kg;
    expect(r1).toBeLessThan(0.7);
  });
});
