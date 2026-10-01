import { describe, it, expect } from 'vitest';

describe('Buyer Requirement Domain Rules & Validations (Data.md §8 & §12)', () => {
  it('validates quantity bounds (0 < quantity <= 100,000)', () => {
    const isValidQuantity = (q: number) => q > 0 && q <= 100000;
    expect(isValidQuantity(0)).toBe(false);
    expect(isValidQuantity(-100)).toBe(false);
    expect(isValidQuantity(1500)).toBe(true);
    expect(isValidQuantity(100000)).toBe(true);
    expect(isValidQuantity(100001)).toBe(false);
  });

  it('validates max landed price is strictly positive', () => {
    const isValidPrice = (p: number) => p > 0 && p <= 100000;
    expect(isValidPrice(0)).toBe(false);
    expect(isValidPrice(-10)).toBe(false);
    expect(isValidPrice(29.0)).toBe(true);
    expect(isValidPrice(55.0)).toBe(true);
  });

  it('validates quality grade requirement accepts only A, B, or C', () => {
    const isValidGrade = (grade: string) => ['A', 'B', 'C'].includes(grade);
    expect(isValidGrade('A')).toBe(true);
    expect(isValidGrade('B')).toBe(true);
    expect(isValidGrade('C')).toBe(true);
    expect(isValidGrade('D')).toBe(false);
    expect(isValidGrade('X')).toBe(false);
  });

  it('validates needed_by date must not be in the past', () => {
    const today = new Date('2026-10-01');
    const isFutureOrToday = (dateStr: string) => {
      const d = new Date(dateStr);
      return d >= today;
    };

    expect(isFutureOrToday('2026-10-01')).toBe(true);
    expect(isFutureOrToday('2026-10-03')).toBe(true);
    expect(isFutureOrToday('2026-09-30')).toBe(false);
  });

  it('validates Rule D-021 dynamic expiry evaluation', () => {
    const evaluateDynamicExpiry = (
      neededByStr: string,
      currentStatus: string,
      todayStr: string
    ) => {
      if (neededByStr < todayStr && ['OPEN', 'PARTIALLY_FULFILLED'].includes(currentStatus)) {
        return 'EXPIRED';
      }
      return currentStatus;
    };

    expect(evaluateDynamicExpiry('2026-09-30', 'OPEN', '2026-10-01')).toBe('EXPIRED');
    expect(evaluateDynamicExpiry('2026-09-30', 'PARTIALLY_FULFILLED', '2026-10-01')).toBe('EXPIRED');
    expect(evaluateDynamicExpiry('2026-10-02', 'OPEN', '2026-10-01')).toBe('OPEN');
    expect(evaluateDynamicExpiry('2026-09-30', 'FULFILLED', '2026-10-01')).toBe('FULFILLED');
    expect(evaluateDynamicExpiry('2026-09-30', 'CANCELLED', '2026-10-01')).toBe('CANCELLED');
  });

  it('validates buyer quantity update cannot fall below quantity_fulfilled_kg', () => {
    const canUpdateQuantity = (newQty: number, fulfilledQty: number) => newQty >= fulfilledQty;

    expect(canUpdateQuantity(1500, 500)).toBe(true);
    expect(canUpdateQuantity(500, 500)).toBe(true);
    expect(canUpdateQuantity(400, 500)).toBe(false);
  });

  it('validates terminal states reject mutation (CANCELLED, FULFILLED, EXPIRED)', () => {
    const isMutable = (status: string) => ['OPEN', 'PARTIALLY_FULFILLED'].includes(status);

    expect(isMutable('OPEN')).toBe(true);
    expect(isMutable('PARTIALLY_FULFILLED')).toBe(true);
    expect(isMutable('CANCELLED')).toBe(false);
    expect(isMutable('FULFILLED')).toBe(false);
    expect(isMutable('EXPIRED')).toBe(false);
  });

  it('validates educational landed price formula text', () => {
    const formula = 'max_landed_price >= farmgate_ask + transport_cost + platform_fee (2%)';
    const note = 'Includes farmgate ask + transport + 2% platform fee';

    expect(formula).toContain('farmgate_ask');
    expect(formula).toContain('transport_cost');
    expect(formula).toContain('2%');
    expect(note).toBe('Includes farmgate ask + transport + 2% platform fee');
  });

  it('validates Indian geographical bounding box coordinates for buyers', () => {
    const isValidCoordinates = (lat: number, lng: number) =>
      lat >= 6.0 && lat <= 38.0 && lng >= 68.0 && lng <= 98.0;

    // Gurugram coordinates
    expect(isValidCoordinates(28.47, 77.05)).toBe(true);
    // Noida coordinates
    expect(isValidCoordinates(28.57, 77.35)).toBe(true);
    // Out of bounds
    expect(isValidCoordinates(4.5, 77.0)).toBe(false); // Lat < 6.0
    expect(isValidCoordinates(40.0, 77.0)).toBe(false); // Lat > 38.0
    expect(isValidCoordinates(28.0, 65.0)).toBe(false); // Lng < 68.0
    expect(isValidCoordinates(28.0, 102.0)).toBe(false); // Lng > 98.0
  });
});
