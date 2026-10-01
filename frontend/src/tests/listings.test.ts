import { describe, it, expect } from 'vitest';

describe('Produce Listing Validation Rules (Data.md §8)', () => {
  it('validates quantity bounds (0 < quantity <= 100,000)', () => {
    const isValidQuantity = (q: number) => q > 0 && q <= 100000;
    expect(isValidQuantity(0)).toBe(false);
    expect(isValidQuantity(-50)).toBe(false);
    expect(isValidQuantity(100)).toBe(true);
    expect(isValidQuantity(100000)).toBe(true);
    expect(isValidQuantity(100001)).toBe(false);
  });

  it('validates min_order_kg is positive and does not exceed quantity_kg', () => {
    const isValidMinOrder = (minOrder: number, quantity: number) =>
      minOrder > 0 && minOrder <= quantity;

    expect(isValidMinOrder(0, 500)).toBe(false);
    expect(isValidMinOrder(100, 500)).toBe(true);
    expect(isValidMinOrder(500, 500)).toBe(true);
    expect(isValidMinOrder(600, 500)).toBe(false);
  });

  it('validates ask price is strictly positive', () => {
    const isValidPrice = (p: number) => p > 0 && p <= 100000;
    expect(isValidPrice(0)).toBe(false);
    expect(isValidPrice(-10)).toBe(false);
    expect(isValidPrice(24.5)).toBe(true);
    expect(isValidPrice(150)).toBe(true);
  });

  it('triggers price sanity warning when ask price > 3x benchmark', () => {
    const isPriceFarAboveBenchmark = (ask: number, benchmark: number) => ask > 3 * benchmark;
    expect(isPriceFarAboveBenchmark(25, 22.5)).toBe(false);
    expect(isPriceFarAboveBenchmark(65, 22.5)).toBe(false);
    expect(isPriceFarAboveBenchmark(70, 22.5)).toBe(true); // 70 > 67.5
  });

  it('validates harvest date is within [today - 30 days, today]', () => {
    const today = new Date('2026-10-01');
    const isValidHarvestDate = (harvestDateStr: string) => {
      const d = new Date(harvestDateStr);
      const minDate = new Date(today);
      minDate.setDate(minDate.getDate() - 30);
      return d <= today && d >= minDate;
    };

    expect(isValidHarvestDate('2026-10-01')).toBe(true);
    expect(isValidHarvestDate('2026-09-25')).toBe(true);
    expect(isValidHarvestDate('2026-09-01')).toBe(true);
    expect(isValidHarvestDate('2026-08-30')).toBe(false); // > 30 days old
    expect(isValidHarvestDate('2026-10-02')).toBe(false); // future date
  });

  it('validates availability window: available_until >= available_from and >= today', () => {
    const today = new Date('2026-10-01');
    const isValidAvailability = (fromStr: string, untilStr: string) => {
      const from = new Date(fromStr);
      const until = new Date(untilStr);
      return until >= from && until >= today;
    };

    expect(isValidAvailability('2026-10-01', '2026-10-05')).toBe(true);
    expect(isValidAvailability('2026-10-03', '2026-10-02')).toBe(false); // inverted
    expect(isValidAvailability('2026-09-20', '2026-09-25')).toBe(false); // past until
  });
});
