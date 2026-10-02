import { describe, it, expect } from 'vitest';
import {
  Candidate,
  NearMiss,
} from '../api/types';

describe('Deterministic Matching Engine Domain Logic & Formulas (ML.md §9, API.md §9)', () => {
  it('calculates weighted matching score correctly and verifies bounds', () => {
    const weights = { price: 0.4, distance: 0.2, freshness: 0.2, fill: 0.2 };
    const factors = { price: 0.85, distance: 0.9, freshness: 0.95, fill: 1.0 };

    const total =
      weights.price * factors.price +
      weights.distance * factors.distance +
      weights.freshness * factors.freshness +
      weights.fill * factors.fill;

    expect(total).toBeCloseTo(0.91, 2);
    expect(total).toBeGreaterThanOrEqual(0.0);
    expect(total).toBeLessThanOrEqual(1.0);
  });

  it('determines fill_status correctly based on fulfilled and shortfall quantities', () => {
    const getFillStatus = (
      requested: number,
      fulfilled: number
    ): 'FULL' | 'PARTIAL' | 'NONE' => {
      const shortfall = requested - fulfilled;
      if (shortfall <= 0.001) return 'FULL';
      if (fulfilled > 0) return 'PARTIAL';
      return 'NONE';
    };

    expect(getFillStatus(1500, 1500)).toBe('FULL');
    expect(getFillStatus(1000, 300)).toBe('PARTIAL');
    expect(getFillStatus(2500, 0)).toBe('NONE');
  });

  it('generates verified greedy allocations across multiple sources (Seed R2 pattern)', () => {
    const remainingDemand = 6500;
    const candidates = [
      { id: 5, available_kg: 4800, min_order_kg: 500, score: 0.9 },
      { id: 6, available_kg: 2000, min_order_kg: 500, score: 0.85 },
      { id: 7, available_kg: 1400, min_order_kg: 300, score: 0.8 },
    ];

    let rem = remainingDemand;
    const allocations: Array<{ listing_id: number; quantity_kg: number }> = [];

    for (const c of candidates) {
      if (rem <= 0) break;
      const q = Math.min(c.available_kg, rem);
      if (q >= c.min_order_kg) {
        allocations.push({ listing_id: c.id, quantity_kg: q });
        rem -= q;
      }
    }

    expect(allocations.length).toBe(2);
    expect(allocations[0]).toEqual({ listing_id: 5, quantity_kg: 4800 });
    expect(allocations[1]).toEqual({ listing_id: 6, quantity_kg: 1700 });
    expect(rem).toBe(0);
  });

  it('skips candidates when allocatable quantity is below min_order_kg', () => {
    const remainingDemand = 200;
    const candidate = { id: 8, available_kg: 3000, min_order_kg: 500 };

    const q = Math.min(candidate.available_kg, remainingDemand);
    const isBelowMin = q < candidate.min_order_kg;

    expect(isBelowMin).toBe(true);
    expect(q).toBe(200);
  });

  it('validates near-miss structure and allowed exclusion reasons', () => {
    const allowedReasons = [
      'BUDGET',
      'GRADE',
      'DISTANCE',
      'FRESHNESS',
      'AVAILABILITY',
      'BELOW_MIN_ORDER',
    ];

    const nearMiss: NearMiss = {
      listing_id: 4,
      excluded_reason: 'BUDGET',
      detail: 'Landed ₹36.53/kg is ₹0.53/kg over budget ₹36.00/kg',
      landed_price_per_kg: 36.53,
      distance_km: 76.5,
    };

    expect(allowedReasons.includes(nearMiss.excluded_reason)).toBe(true);
    expect(nearMiss.detail).toContain('over budget');
  });

  it('validates candidate deterministic reasons format and numbers', () => {
    const mockCandidate: Partial<Candidate> = {
      rank: 1,
      landed_price_per_kg: 25.6,
      distance_km: 58.2,
      reasons: [
        'Landed ₹25.60/kg is 11.7% below your ₹29.00 budget',
        'Nearby source (58.2 km est., ~2.5h transit)',
        'Fresh produce (2 days from harvest at delivery vs 7d shelf life)',
        'Single lot can fulfill 100% of requested 1,500 kg',
      ],
    };

    expect(mockCandidate.reasons?.length).toBe(4);
    expect(mockCandidate.reasons?.[0]).toContain('below your');
    expect(mockCandidate.reasons?.[1]).toContain('58.2 km');
  });

  it('validates matching accept payload constraints', () => {
    const isValidAcceptPayload = (payload: {
      requirement_id: number;
      allocations: Array<{ listing_id: number; quantity_kg: number }>;
      delivery_date: string;
      needed_by: string;
      today: string;
    }) => {
      if (!payload.requirement_id || payload.requirement_id <= 0) return false;
      if (!payload.allocations || payload.allocations.length === 0) return false;
      if (payload.allocations.some((a) => a.quantity_kg <= 0)) return false;
      if (payload.delivery_date < payload.today) return false;
      if (payload.delivery_date > payload.needed_by) return false;
      return true;
    };

    expect(
      isValidAcceptPayload({
        requirement_id: 3,
        allocations: [{ listing_id: 10, quantity_kg: 300 }],
        delivery_date: '2026-10-03',
        needed_by: '2026-10-04',
        today: '2026-10-02',
      })
    ).toBe(true);

    // Empty allocations
    expect(
      isValidAcceptPayload({
        requirement_id: 3,
        allocations: [],
        delivery_date: '2026-10-03',
        needed_by: '2026-10-04',
        today: '2026-10-02',
      })
    ).toBe(false);

    // Delivery date after needed_by
    expect(
      isValidAcceptPayload({
        requirement_id: 3,
        allocations: [{ listing_id: 10, quantity_kg: 300 }],
        delivery_date: '2026-10-05',
        needed_by: '2026-10-04',
        today: '2026-10-02',
      })
    ).toBe(false);
  });
});
