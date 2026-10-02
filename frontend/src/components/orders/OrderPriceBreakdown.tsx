import React, { useEffect, useState } from 'react';
import { fetchOrderPriceBreakdownApi } from '../../api/pricing';
import { OrderPriceBreakdownResponse } from '../../api/types';

interface OrderPriceBreakdownProps {
  orderId: number;
  token?: string | null;
  // Fallbacks if API is still loading or for initial render
  fallbackQuantityKg?: number;
  fallbackAgreedPricePerKg?: number;
  fallbackTransportCostPerKg?: number;
  fallbackPlatformFeePerKg?: number;
  fallbackLandedPricePerKg?: number;
  fallbackTotalAmount?: number;
}

export const OrderPriceBreakdown: React.FC<OrderPriceBreakdownProps> = ({
  orderId,
  token,
  fallbackQuantityKg = 0,
  fallbackAgreedPricePerKg = 0,
  fallbackTransportCostPerKg = 0,
  fallbackPlatformFeePerKg = 0,
  fallbackLandedPricePerKg = 0,
  fallbackTotalAmount = 0,
}) => {
  const [data, setData] = useState<OrderPriceBreakdownResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadBreakdown() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchOrderPriceBreakdownApi(orderId, token);
        if (isMounted) setData(res);
      } catch (err: unknown) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Unable to load live breakdown');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadBreakdown();
    return () => {
      isMounted = false;
    };
  }, [orderId, token]);

  const farmgate = data ? data.per_kg.farmgate : fallbackAgreedPricePerKg;
  const transport = data ? data.per_kg.transport : fallbackTransportCostPerKg;
  const platformFee = data ? data.per_kg.platform_fee : fallbackPlatformFeePerKg;
  const landed = data ? data.per_kg.landed : fallbackLandedPricePerKg;
  const transportBasis = data ? data.transport_basis : 'ESTIMATE';

  const farmgateTotal = data
    ? data.totals.farmgate_total
    : fallbackAgreedPricePerKg * fallbackQuantityKg;
  const transportTotal = data
    ? data.totals.transport_total
    : fallbackTransportCostPerKg * fallbackQuantityKg;
  const platformFeeTotal = data
    ? data.totals.platform_fee_total
    : fallbackPlatformFeePerKg * fallbackQuantityKg;
  const landedTotal = data
    ? data.totals.landed_total
    : fallbackTotalAmount || fallbackLandedPricePerKg * fallbackQuantityKg;

  const benchmark = data?.benchmark;
  const scenario = data?.scenario;
  const fairBand = data?.fair_band;

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-100 pb-3">
        <div>
          <h3 className="font-bold text-gray-900 text-sm">
            Per-Order Price Waterfall Breakdown
          </h3>
          <p className="text-[11px] text-gray-500">
            Authoritative cost breakdown reconciling direct farmgate, logistics, and platform fee.
          </p>
        </div>
        <span className="text-[10px] font-bold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
          Phase 10 Transparency
        </span>
      </div>

      {loading && (
        <div className="py-2 text-center text-xs text-gray-400 animate-pulse">
          Reconciling live price waterfall...
        </div>
      )}

      {error && (
        <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
          Note: Viewing preliminary calculation ({error}).
        </div>
      )}

      {/* Waterfall Table / Rows */}
      <div className="space-y-3 text-xs">
        <div className="flex justify-between items-center text-gray-700">
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
            <span className="font-semibold text-gray-900">Farmgate Producer Price</span>
          </span>
          <div className="text-right">
            <span className="font-bold text-gray-900">₹{farmgate.toFixed(2)}/kg</span>
            <span className="text-gray-400 ml-2">₹{farmgateTotal.toFixed(2)}</span>
          </div>
        </div>

        <div className="flex justify-between items-center text-gray-700">
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
            <span>
              Transport & Logistics{' '}
              <span className="text-[10px] font-semibold text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded ml-1">
                {transportBasis === 'ALLOCATED_ROUTE' ? 'Route Allocated' : 'Dedicated Trip Estimate'}
              </span>
            </span>
          </span>
          <div className="text-right">
            <span className="font-bold text-gray-900">₹{transport.toFixed(2)}/kg</span>
            <span className="text-gray-400 ml-2">₹{transportTotal.toFixed(2)}</span>
          </div>
        </div>

        <div className="flex justify-between items-center text-gray-700">
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
            <span>
              Platform Coordination Fee{' '}
              <span className="text-[10px] text-gray-400 font-normal">
                ({scenario ? `${scenario.assumptions.platform_fee_pct}%` : '2%'})
              </span>
            </span>
          </span>
          <div className="text-right">
            <span className="font-bold text-gray-900">₹{platformFee.toFixed(2)}/kg</span>
            <span className="text-gray-400 ml-2">₹{platformFeeTotal.toFixed(2)}</span>
          </div>
        </div>

        {/* Landed Summary */}
        <div className="pt-3 border-t border-gray-200 flex justify-between items-baseline">
          <div>
            <span className="font-black text-gray-900 text-sm">Final Landed Price</span>
            <p className="text-[10px] text-gray-400">Farmgate + Transport + Fee</p>
          </div>
          <div className="text-right">
            <span className="font-black text-emerald-700 text-base">
              ₹{landed.toFixed(2)}
              <span className="text-xs font-normal text-gray-500">/kg</span>
            </span>
            <p className="text-xs font-bold text-gray-800 mt-0.5">
              Total ₹{landedTotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      {/* Benchmark & Fair Price Band Card */}
      {benchmark && (
        <div className="bg-emerald-50/50 border border-emerald-200 rounded-xl p-3.5 space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-emerald-950 flex items-center gap-1.5">
              <span>🏛️</span>
              <span>Market Reference Benchmark ({benchmark.hub.name})</span>
            </span>
            <span
              className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase ${
                benchmark.is_synthetic
                  ? 'bg-amber-100 text-amber-800 border border-amber-200'
                  : 'bg-blue-100 text-blue-800 border border-blue-200'
              }`}
            >
              {benchmark.source}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-gray-700 pt-1">
            <div className="bg-white p-2 rounded-lg border border-emerald-100">
              <span className="text-[10px] text-gray-400 block">APMC Modal Reference</span>
              <strong className="text-gray-900 text-sm">₹{benchmark.modal_price_per_kg.toFixed(2)}/kg</strong>
              <span className="text-[10px] text-gray-500 block">
                Range: ₹{benchmark.min_price_per_kg} – ₹{benchmark.max_price_per_kg}
              </span>
            </div>

            <div className="bg-white p-2 rounded-lg border border-emerald-100">
              <span className="text-[10px] text-gray-400 block">Fair Price Band</span>
              {fairBand ? (
                <div>
                  <strong className="text-emerald-700 text-sm">
                    ₹{fairBand.low.toFixed(2)} – ₹{fairBand.high.toFixed(2)}/kg
                  </strong>
                  <span className="text-[10px] text-gray-500 block">Mutual economic win</span>
                </div>
              ) : (
                <span className="text-xs text-gray-400 italic">Band not feasible under current costs</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Traditional Chain Modelled Scenario (AC-PRC-02 & 03) */}
      {scenario && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-3.5 space-y-2.5 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-gray-900 flex items-center gap-1.5">
              <span>⚖️</span>
              <span>Traditional Supply Chain Comparison (Modelled Scenario)</span>
            </span>
            <span className="text-[9px] font-semibold text-gray-500 bg-white px-2 py-0.5 rounded border border-gray-200">
              {data?.basis || 'MODELLED_SCENARIO'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="bg-white p-2.5 rounded-lg border border-gray-200 space-y-1">
              <span className="text-[10px] text-gray-500 block">Traditional Mandi Net (Farmer)</span>
              <div className="font-bold text-gray-900">₹{scenario.farmer_mandi_net_per_kg.toFixed(2)}/kg</div>
              <div className={`text-[11px] font-bold ${scenario.delta_farmer_pct >= 0 ? 'text-emerald-700' : 'text-rose-600'}`}>
                {scenario.delta_farmer_pct >= 0 ? `+${scenario.delta_farmer_pct.toFixed(1)}%` : `${scenario.delta_farmer_pct.toFixed(1)}%`}{' '}
                farmer realization
              </div>
            </div>

            <div className="bg-white p-2.5 rounded-lg border border-gray-200 space-y-1">
              <span className="text-[10px] text-gray-500 block">Traditional Intermediary Cost (Buyer)</span>
              <div className="font-bold text-gray-900">₹{scenario.buyer_traditional_per_kg.toFixed(2)}/kg</div>
              <div className={`text-[11px] font-bold ${scenario.delta_buyer_pct <= 0 ? 'text-emerald-700' : 'text-amber-600'}`}>
                {scenario.delta_buyer_pct <= 0 ? `${scenario.delta_buyer_pct.toFixed(1)}%` : `+${scenario.delta_buyer_pct.toFixed(1)}%`}{' '}
                buyer cost
              </div>
            </div>
          </div>

          <p className="text-[10px] text-gray-500 leading-tight">
            * Assumptions: commission agent {scenario.assumptions.commission_agent_pct}%, trader margin {scenario.assumptions.trader_margin_pct}%, retail margin {scenario.assumptions.retail_margin_pct}%, last-mile handling ₹{scenario.assumptions.last_mile_cost_per_kg}/kg. {data?.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
};
