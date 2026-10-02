import { describe, it, expect } from 'vitest';
import {
  OrderPriceBreakdownResponse,
  PricingBenchmarkResponse,
} from '../api/types';

describe('Phase 10 Price Transparency Frontend Models and Calculations', () => {
  it('verifies price waterfall components and total reconciliation (AC-PRC-01)', () => {
    const mockBreakdown: OrderPriceBreakdownResponse = {
      order_id: 1,
      crop: { id: 1, name: 'Tomato' },
      quantity_kg: 600,
      per_kg: {
        farmgate: 22.50,
        transport: 3.47,
        platform_fee: 0.45,
        landed: 26.42,
      },
      totals: {
        farmgate_total: 13500.00,
        transport_total: 2082.00,
        platform_fee_total: 270.00,
        landed_total: 15852.00,
      },
      transport_basis: 'ESTIMATE',
      benchmark: {
        hub: { id: 2, name: 'Gurugram' },
        market_name: 'Gurugram Reference Market (SYNTHETIC)',
        price_date: '2026-10-01',
        modal_price_per_kg: 25.00,
        min_price_per_kg: 21.00,
        max_price_per_kg: 29.00,
        source: 'SYNTHETIC_DEMO',
        is_synthetic: true,
      },
      scenario: {
        farmer_mandi_net_per_kg: 21.25,
        buyer_traditional_per_kg: 31.24,
        delta_farmer_pct: 5.88,
        delta_buyer_pct: -15.43,
        assumptions: {
          platform_fee_pct: 2.0,
          commission_agent_pct: 5.0,
          trader_margin_pct: 8.0,
          retail_margin_pct: 12.0,
          last_mile_cost_per_kg: 1.0,
        },
      },
      fair_band: {
        low: 21.25,
        high: 27.23,
      },
      basis: 'MODELLED_SCENARIO',
      disclaimer: 'Modelled scenario based on published research parameters.',
    };

    // Math reconciliation
    const perKg = mockBreakdown.per_kg;
    const computedLanded = Number((perKg.farmgate + perKg.transport + perKg.platform_fee).toFixed(2));
    expect(computedLanded).toBe(perKg.landed);

    // Totals reconciliation
    const totals = mockBreakdown.totals;
    const computedTotal = Number((totals.farmgate_total + totals.transport_total + totals.platform_fee_total).toFixed(2));
    expect(computedTotal).toBe(totals.landed_total);

    // Provenance
    expect(mockBreakdown.basis).toBe('MODELLED_SCENARIO');
    expect(mockBreakdown.benchmark?.source).toBe('SYNTHETIC_DEMO');
    expect(mockBreakdown.benchmark?.is_synthetic).toBe(true);

    // Scenario deltas
    expect(mockBreakdown.scenario?.delta_farmer_pct).toBe(5.88);
    expect(mockBreakdown.scenario?.delta_buyer_pct).toBe(-15.43);
  });

  it('correctly maps benchmark response with 30-day trend and fair price band', () => {
    const mockBenchmark: PricingBenchmarkResponse = {
      hub: { id: 1, name: 'Delhi North', city: 'Delhi', state: 'Delhi' },
      benchmark: {
        hub: { id: 1, name: 'Delhi North' },
        market_name: 'Delhi North Reference Market (SYNTHETIC)',
        price_date: '2026-10-01',
        modal_price_per_kg: 24.50,
        min_price_per_kg: 20.00,
        max_price_per_kg: 28.00,
        source: 'AGMARKNET_SNAPSHOT',
        is_synthetic: false,
      },
      trend: [
        { date: '2026-09-20', modal_price_per_kg: 25.00 },
        { date: '2026-09-25', modal_price_per_kg: 24.00 },
        { date: '2026-10-01', modal_price_per_kg: 24.50 },
      ],
      fair_band: {
        low: 20.50,
        high: 26.80,
      },
      assumptions: {
        platform_fee_pct: 2.0,
        commission_agent_pct: 5.0,
        trader_margin_pct: 8.0,
        retail_margin_pct: 12.0,
        last_mile_cost_per_kg: 1.0,
      },
      basis: 'MODELLED_SCENARIO',
      disclaimer: 'Official Agmarknet snapshot data used where available.',
    };

    expect(mockBenchmark.hub.id).toBe(1);
    expect(mockBenchmark.benchmark?.source).toBe('AGMARKNET_SNAPSHOT');
    expect(mockBenchmark.benchmark?.is_synthetic).toBe(false);
    expect(mockBenchmark.trend).toHaveLength(3);
    expect(mockBenchmark.fair_band?.high).toBeGreaterThan(mockBenchmark.fair_band?.low || 0);
  });
});
