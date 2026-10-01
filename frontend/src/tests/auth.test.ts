import { describe, it, expect } from 'vitest';
import { DEMO_PERSONAS } from '../api/types';

describe('Demo Personas Specification', () => {
  it('contains exactly the 6 canonical demo personas', () => {
    expect(DEMO_PERSONAS).toHaveLength(6);
    const keys = DEMO_PERSONAS.map((p) => p.key);
    expect(keys).toEqual([
      'fpo_sonipat',
      'fpo_meerut',
      'farmer_karnal',
      'buyer_gurugram',
      'buyer_noida',
      'operator',
    ]);
  });

  it('has valid email and non-empty metadata for every persona', () => {
    for (const persona of DEMO_PERSONAS) {
      expect(persona.email).toContain('@fasalsetu.internal');
      expect(persona.label.length).toBeGreaterThan(0);
      expect(persona.sublabel.length).toBeGreaterThan(0);
      expect(persona.location.length).toBeGreaterThan(0);
      expect(['farmer', 'fpo', 'buyer_retail', 'buyer_trader', 'operator']).toContain(persona.role);
    }
  });
});
