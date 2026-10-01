import { describe, it, expect } from 'vitest';

describe('Phase 6 — Demand Forecasting Domain Logic & Rules', () => {
  it('enforces horizon_days bounds between 1 and 7', () => {
    const isValidHorizon = (h: number) => h >= 1 && h <= 7 && Number.isInteger(h);

    expect(isValidHorizon(1)).toBe(true);
    expect(isValidHorizon(7)).toBe(true);
    expect(isValidHorizon(4)).toBe(true);
    expect(isValidHorizon(0)).toBe(false);
    expect(isValidHorizon(8)).toBe(false);
    expect(isValidHorizon(-1)).toBe(false);
    expect(isValidHorizon(3.5)).toBe(false);
  });

  it('enforces non-negativity and quantile monotonicity 0 <= q10 <= y_hat <= q90', () => {
    const sanitizeQuantiles = (q10: number, point: number, q90: number) => {
      const clipped = [Math.max(0, q10), Math.max(0, point), Math.max(0, q90)];
      clipped.sort((a, b) => a - b);
      return {
        interval_lo_kg: clipped[0],
        point_forecast_kg: clipped[1],
        interval_hi_kg: clipped[2],
      };
    };

    // Case 1: Already monotonic
    const res1 = sanitizeQuantiles(1200, 1400, 1600);
    expect(res1.interval_lo_kg).toBe(1200);
    expect(res1.point_forecast_kg).toBe(1400);
    expect(res1.interval_hi_kg).toBe(1600);

    // Case 2: Inverted quantiles (crossing)
    const res2 = sanitizeQuantiles(1500, 1300, 1400);
    expect(res2.interval_lo_kg).toBe(1300);
    expect(res2.point_forecast_kg).toBe(1400);
    expect(res2.interval_hi_kg).toBe(1500);
    expect(res2.interval_lo_kg <= res2.point_forecast_kg).toBe(true);
    expect(res2.point_forecast_kg <= res2.interval_hi_kg).toBe(true);

    // Case 3: Negative predictions clipped to 0
    const res3 = sanitizeQuantiles(-50, 100, 200);
    expect(res3.interval_lo_kg).toBe(0);
    expect(res3.point_forecast_kg).toBe(100);
    expect(res3.interval_hi_kg).toBe(200);
  });

  it('classifies regional hub opportunity labels based on supply-demand ratio', () => {
    const getOpportunityLabel = (activeSupplyKg: number, totalDemandKg: number): string => {
      if (totalDemandKg <= 0) return 'OVERSUPPLIED';
      const ratio = activeSupplyKg / totalDemandKg;
      if (ratio < 0.5) return 'HIGH_DEFICIT';
      if (ratio <= 1.2) return 'BALANCED';
      return 'OVERSUPPLIED';
    };

    // Supply deficit (high opportunity)
    expect(getOpportunityLabel(200, 1000)).toBe('HIGH_DEFICIT'); // ratio 0.2
    expect(getOpportunityLabel(490, 1000)).toBe('HIGH_DEFICIT'); // ratio 0.49

    // Balanced market
    expect(getOpportunityLabel(500, 1000)).toBe('BALANCED'); // ratio 0.5
    expect(getOpportunityLabel(1000, 1000)).toBe('BALANCED'); // ratio 1.0
    expect(getOpportunityLabel(1200, 1000)).toBe('BALANCED'); // ratio 1.2

    // Oversupplied
    expect(getOpportunityLabel(1500, 1000)).toBe('OVERSUPPLIED'); // ratio 1.5
    expect(getOpportunityLabel(500, 0)).toBe('OVERSUPPLIED');
  });

  it('enforces Rule D-026: produce lots are attributed strictly to nearest hub without double counting', () => {
    interface Hub {
      id: number;
      name: string;
      lat: number;
      lng: number;
    }

    interface ListingLot {
      id: number;
      quantity_kg: number;
      producer_lat: number;
      producer_lng: number;
    }

    const hubs: Hub[] = [
      { id: 1, name: 'Delhi North', lat: 28.7041, lng: 77.1025 },
      { id: 2, name: 'Delhi South', lat: 28.5355, lng: 77.2410 },
      { id: 3, name: 'Gurugram', lat: 28.4595, lng: 77.0266 },
    ];

    // Dummy euclidean / approximate distance for test assertion
    const distSq = (lat1: number, lng1: number, lat2: number, lng2: number) =>
      Math.pow(lat1 - lat2, 2) + Math.pow(lng1 - lng2, 2);

    const listings: ListingLot[] = [
      { id: 1, quantity_kg: 500, producer_lat: 28.71, producer_lng: 77.11 }, // Nearest to Delhi North (1)
      { id: 2, quantity_kg: 800, producer_lat: 28.46, producer_lng: 77.03 }, // Nearest to Gurugram (3)
      { id: 3, quantity_kg: 300, producer_lat: 28.54, producer_lng: 77.25 }, // Nearest to Delhi South (2)
    ];

    const supplyByHub: Record<number, number> = { 1: 0, 2: 0, 3: 0 };

    listings.forEach((lot) => {
      let nearestHub = hubs[0];
      let minDist = distSq(lot.producer_lat, lot.producer_lng, nearestHub.lat, nearestHub.lng);

      for (let i = 1; i < hubs.length; i++) {
        const d = distSq(lot.producer_lat, lot.producer_lng, hubs[i].lat, hubs[i].lng);
        if (d < minDist) {
          minDist = d;
          nearestHub = hubs[i];
        }
      }

      supplyByHub[nearestHub.id] += lot.quantity_kg;
    });

    expect(supplyByHub[1]).toBe(500);
    expect(supplyByHub[2]).toBe(300);
    expect(supplyByHub[3]).toBe(800);

    // Sum of attributed supply strictly equals total available quantity (zero double counting)
    const totalListingsQty = listings.reduce((sum, l) => sum + l.quantity_kg, 0);
    const totalHubsSupply = Object.values(supplyByHub).reduce((sum, s) => sum + s, 0);
    expect(totalHubsSupply).toBe(totalListingsQty);
  });

  it('guarantees null confidence intervals when fallback method is returned', () => {
    const isFallback = (method: string) => method === 'SEASONAL_NAIVE_FALLBACK';

    const buildDailyForecast = (
      date: string,
      day: string,
      point: number,
      method: string,
      lo?: number,
      hi?: number
    ) => {
      const fallback = isFallback(method);
      return {
        date,
        day_of_week: day,
        point_forecast_kg: point,
        interval_lo_kg: fallback ? null : (lo ?? null),
        interval_hi_kg: fallback ? null : (hi ?? null),
      };
    };

    const lgbmItem = buildDailyForecast('2026-10-01', 'Thursday', 1250, 'LIGHTGBM', 1100, 1400);
    expect(lgbmItem.interval_lo_kg).toBe(1100);
    expect(lgbmItem.interval_hi_kg).toBe(1400);

    const fallbackItem = buildDailyForecast(
      '2026-10-01',
      'Thursday',
      1250,
      'SEASONAL_NAIVE_FALLBACK',
      1100,
      1400
    );
    expect(fallbackItem.interval_lo_kg).toBeNull();
    expect(fallbackItem.interval_hi_kg).toBeNull();
    expect(fallbackItem.point_forecast_kg).toBe(1250);
  });
});
