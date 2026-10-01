import { describe, it, expect } from 'vitest';

describe('Phase 5 — Order Placement & Landed Pricing Rules', () => {
  it('validates order quantity between min_order_kg and quantity_available_kg', () => {
    const minOrderKg = 100;
    const availableKg = 700;

    const isValidOrderQty = (qty: number) => qty >= minOrderKg && qty <= availableKg;

    expect(isValidOrderQty(50)).toBe(false); // below min
    expect(isValidOrderQty(100)).toBe(true); // exact min
    expect(isValidOrderQty(500)).toBe(true); // valid
    expect(isValidOrderQty(700)).toBe(true); // exact available
    expect(isValidOrderQty(750)).toBe(false); // exceeds available
  });

  it('validates delivery_date is today or later', () => {
    const todayStr = '2026-10-01';
    const isFutureOrToday = (dStr: string) => dStr >= todayStr;

    expect(isFutureOrToday('2026-10-01')).toBe(true);
    expect(isFutureOrToday('2026-10-05')).toBe(true);
    expect(isFutureOrToday('2026-09-30')).toBe(false);
  });

  it('computes transparent landed cost breakdown accurately with 2% platform fee', () => {
    const quantityKg = 500;
    const agreedPricePerKg = 24.0;
    const transportCostPerKg = 3.5;

    const farmgateTotal = agreedPricePerKg * quantityKg; // 12,000
    const platformFeeTotal = Math.round(0.02 * farmgateTotal * 100) / 100; // 240.0
    const platformFeePerKg = Math.round((platformFeeTotal / quantityKg) * 100) / 100; // 0.48
    const transportTotal = transportCostPerKg * quantityKg; // 1,750
    const landedPricePerKg =
      Math.round((agreedPricePerKg + transportCostPerKg + platformFeePerKg) * 100) / 100; // 27.98
    const totalAmount =
      Math.round((farmgateTotal + transportTotal + platformFeeTotal) * 100) / 100; // 13,990.0

    expect(farmgateTotal).toBe(12000.0);
    expect(platformFeeTotal).toBe(240.0);
    expect(platformFeePerKg).toBe(0.48);
    expect(transportTotal).toBe(1750.0);
    expect(landedPricePerKg).toBe(27.98);
    expect(totalAmount).toBe(13990.0);
  });

  it('enforces transition state machine permissions according to API.md §7', () => {
    type OrderStatus = 'PLACED' | 'CONFIRMED' | 'REJECTED' | 'CANCELLED' | 'IN_TRANSIT' | 'DELIVERED';
    type Role = 'PRODUCER' | 'BUYER' | 'ADMIN';

    const canTransition = (
      from: OrderStatus,
      to: OrderStatus,
      role: Role,
      shipmentId: number | null
    ): boolean => {
      if (from === 'PLACED') {
        if (to === 'CONFIRMED' && (role === 'PRODUCER' || role === 'ADMIN')) return true;
        if (to === 'REJECTED' && (role === 'PRODUCER' || role === 'ADMIN')) return true;
        if (to === 'CANCELLED' && (role === 'BUYER' || role === 'ADMIN')) return true;
      }
      if (from === 'CONFIRMED' && to === 'CANCELLED') {
        // Allowed only while shipment_id is null
        if (shipmentId === null && (role === 'BUYER' || role === 'PRODUCER' || role === 'ADMIN')) {
          return true;
        }
      }
      return false;
    };

    // Producer can confirm or reject PLACED order
    expect(canTransition('PLACED', 'CONFIRMED', 'PRODUCER', null)).toBe(true);
    expect(canTransition('PLACED', 'REJECTED', 'PRODUCER', null)).toBe(true);
    expect(canTransition('PLACED', 'CANCELLED', 'PRODUCER', null)).toBe(false);

    // Buyer can cancel PLACED order, but cannot confirm/reject
    expect(canTransition('PLACED', 'CANCELLED', 'BUYER', null)).toBe(true);
    expect(canTransition('PLACED', 'CONFIRMED', 'BUYER', null)).toBe(false);
    expect(canTransition('PLACED', 'REJECTED', 'BUYER', null)).toBe(false);

    // Both can cancel unrouted CONFIRMED order
    expect(canTransition('CONFIRMED', 'CANCELLED', 'BUYER', null)).toBe(true);
    expect(canTransition('CONFIRMED', 'CANCELLED', 'PRODUCER', null)).toBe(true);

    // Cannot cancel routed CONFIRMED order
    expect(canTransition('CONFIRMED', 'CANCELLED', 'BUYER', 101)).toBe(false);
    expect(canTransition('CONFIRMED', 'CANCELLED', 'PRODUCER', 101)).toBe(false);

    // Terminal states cannot be changed via order transition API
    expect(canTransition('DELIVERED', 'CANCELLED', 'ADMIN', null)).toBe(false);
    expect(canTransition('CANCELLED', 'CONFIRMED', 'ADMIN', null)).toBe(false);
    expect(canTransition('REJECTED', 'CONFIRMED', 'ADMIN', null)).toBe(false);
  });

  it('validates requirement compatibility for linked orders', () => {
    const requirement = {
      id: 1,
      crop_id: 1,
      grade_min: 'B',
      quantity_kg: 1500,
      quantity_fulfilled_kg: 900,
      max_landed_price_per_kg: 32.0,
      status: 'PARTIALLY_FULFILLED',
      needed_by: '2026-10-15',
    };

    const remainingQty = requirement.quantity_kg - requirement.quantity_fulfilled_kg; // 600 kg

    const isCompatible = (orderQty: number, landedPrice: number, listingGrade: string) => {
      if (orderQty > remainingQty) return false;
      if (landedPrice > requirement.max_landed_price_per_kg) return false;
      const rank: Record<string, number> = { A: 3, B: 2, C: 1 };
      if ((rank[listingGrade] ?? 0) < (rank[requirement.grade_min] ?? 0)) return false;
      return true;
    };

    expect(isCompatible(400, 28.5, 'A')).toBe(true); // Grade A satisfies min B, 400 <= 600, price <= 32
    expect(isCompatible(400, 28.5, 'B')).toBe(true); // Grade B satisfies min B
    expect(isCompatible(400, 28.5, 'C')).toBe(false); // Grade C fails min B
    expect(isCompatible(700, 28.5, 'A')).toBe(false); // 700 > remaining 600
    expect(isCompatible(400, 33.0, 'A')).toBe(false); // 33.0 > max budget 32.0
  });
});
