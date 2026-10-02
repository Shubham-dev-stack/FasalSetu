import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import {
  fetchAnalyticsOverviewApi,
  fetchAnalyticsSupplyDemandApi,
} from '../../api/analytics';
import {
  AnalyticsOverviewResponse,
  AnalyticsSupplyDemandResponse,
} from '../../api/types';
import {
  Package,
  Layers,
  Truck,
  IndianRupee,
  ShieldCheck,
  Info,
  Calendar,
  AlertTriangle,
  ExternalLink,
} from 'lucide-react';

const CROPS = [
  { id: 1, name: 'Tomato' },
  { id: 2, name: 'Onion' },
  { id: 3, name: 'Potato' },
  { id: 4, name: 'Cauliflower' },
  { id: 5, name: 'Green Chilli' },
];

export const AnalyticsPage: React.FC = () => {
  const { token } = useAuth();
  const [overview, setOverview] = useState<AnalyticsOverviewResponse | null>(null);
  const [supplyDemand, setSupplyDemand] = useState<AnalyticsSupplyDemandResponse | null>(null);
  const [selectedCropId, setSelectedCropId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [ovRes, sdRes] = await Promise.all([
          fetchAnalyticsOverviewApi(token),
          fetchAnalyticsSupplyDemandApi(selectedCropId, token),
        ]);
        setOverview(ovRes);
        setSupplyDemand(sdRes);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics data');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [token, selectedCropId]);

  const kpis = overview?.kpis;
  const priceGap = overview?.price_gap;

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 py-6 text-ink">
      {/* Page Header & Demo Disclaimer Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-ink">Platform Impact Analytics</h1>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              Traceable Metrics
            </span>
          </div>
          <p className="text-sm text-muted mt-1">
            Real-time aggregate platform performance, logistics consolidation, and supply-demand reconciliation.
          </p>
        </div>

        {/* Provenance and Data Note Badge */}
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs font-medium">
          <Info className="w-4 h-4 text-amber-600 shrink-0" />
          <span>{overview?.data_note || 'All figures computed from synthetic demo records'}</span>
        </div>
      </div>

      {loading && (
        <div className="p-12 text-center text-sm text-muted bg-surface rounded-xl border border-gray-200">
          <span className="animate-spin inline-block w-6 h-6 border-2 border-primary border-t-transparent rounded-full mr-2 align-middle" />
          Aggregating platform intelligence & reconciliation metrics...
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-danger text-sm flex items-center space-x-3">
          <AlertTriangle className="w-5 h-5 text-danger shrink-0" />
          <div>
            <strong className="block font-semibold">Error Loading Analytics</strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      {!loading && !error && overview && (
        <>
          {/* SECTION 1: CORE PLATFORM KPIS */}
          <div>
            <h2 className="text-base font-semibold text-ink mb-3 flex items-center space-x-2">
              <Package className="w-4 h-4 text-primary" />
              <span>Platform Activity & Fulfillment</span>
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Committed Orders */}
              <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
                <span className="text-xs text-muted block uppercase font-semibold">Committed Orders</span>
                <div className="mt-2 flex items-baseline space-x-2">
                  <span className="text-2xl font-bold text-ink">{kpis?.committed_orders ?? 0}</span>
                  <span className="text-xs text-muted">orders</span>
                </div>
                <span className="text-xs text-muted mt-1 block">Confirmed, In-Transit & Delivered</span>
              </div>

              {/* Committed Volume */}
              <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
                <span className="text-xs text-muted block uppercase font-semibold">Committed Volume</span>
                <div className="mt-2 flex items-baseline space-x-2">
                  <span className="text-2xl font-bold text-ink">
                    {kpis?.committed_volume_kg?.toLocaleString() ?? 0}
                  </span>
                  <span className="text-xs text-muted">kg</span>
                </div>
                <span className="text-xs text-muted mt-1 block">Total transacted produce mass</span>
              </div>

              {/* Farmgate Value */}
              <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
                <span className="text-xs text-muted block uppercase font-semibold">Committed Value</span>
                <div className="mt-2 flex items-baseline space-x-1">
                  <span className="text-xl font-bold text-ink">₹</span>
                  <span className="text-2xl font-bold text-ink">
                    {kpis?.committed_value_inr?.toLocaleString() ?? 0}
                  </span>
                </div>
                <span className="text-xs text-muted mt-1 block">Gross farmgate produce value</span>
              </div>

              {/* Requirement Fill Rate */}
              <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
                <span className="text-xs text-muted block uppercase font-semibold">Requirement Fill Rate</span>
                <div className="mt-2 flex items-baseline space-x-1">
                  <span className="text-2xl font-bold text-emerald-600">
                    {kpis?.requirement_fill_rate_pct !== null && kpis?.requirement_fill_rate_pct !== undefined
                      ? `${kpis.requirement_fill_rate_pct}%`
                      : 'N/A'}
                  </span>
                </div>
                <span className="text-xs text-muted mt-1 block">Fulfilled vs requested demand</span>
              </div>
            </div>
          </div>

          {/* SECTION 2: LOGISTICS CONSOLIDATION & ROUTE SAVINGS */}
          <div>
            <h2 className="text-base font-semibold text-ink mb-3 flex items-center space-x-2">
              <Truck className="w-4 h-4 text-primary" />
              <span>Logistics Impact & Multi-Stop Consolidation</span>
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Avg Logistics Cost */}
              <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
                <span className="text-xs text-muted block uppercase font-semibold">Avg Transport Rate</span>
                <div className="mt-2 flex items-baseline space-x-1">
                  <span className="text-2xl font-bold text-ink">
                    {kpis?.avg_logistics_cost_per_kg !== null && kpis?.avg_logistics_cost_per_kg !== undefined
                      ? `₹${kpis.avg_logistics_cost_per_kg}`
                      : 'N/A'}
                  </span>
                  <span className="text-xs text-muted">/ kg</span>
                </div>
                <span className="text-xs text-muted mt-1 block">Allocated route cost & estimate basis</span>
              </div>

              {/* Route Distance Savings */}
              <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
                <span className="text-xs text-muted block uppercase font-semibold">Route Distance Savings</span>
                <div className="mt-2 flex items-baseline space-x-1">
                  <span className="text-2xl font-bold text-emerald-600">
                    {kpis?.route_savings_km?.toLocaleString() ?? 0}
                  </span>
                  <span className="text-xs text-muted">km</span>
                </div>
                <span className="text-xs text-muted mt-1 block">Saved vs unconsolidated trips</span>
              </div>

              {/* Route Cost Savings */}
              <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
                <span className="text-xs text-muted block uppercase font-semibold">Logistics Cost Savings</span>
                <div className="mt-2 flex items-baseline space-x-1">
                  <span className="text-xl font-bold text-emerald-600">₹</span>
                  <span className="text-2xl font-bold text-emerald-600">
                    {kpis?.route_savings_inr?.toLocaleString() ?? 0}
                  </span>
                </div>
                <span className="text-xs text-muted mt-1 block">Across APPROVED route plans</span>
              </div>

              {/* Average Fleet Utilization */}
              <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
                <span className="text-xs text-muted block uppercase font-semibold">Avg Fleet Utilization</span>
                <div className="mt-2 flex items-baseline space-x-1">
                  <span className="text-2xl font-bold text-primary">
                    {kpis?.avg_utilization_pct !== null && kpis?.avg_utilization_pct !== undefined
                      ? `${kpis.avg_utilization_pct}%`
                      : 'N/A'}
                  </span>
                </div>
                <span className="text-xs text-muted mt-1 block">Peak load capacity ratio</span>
              </div>
            </div>
          </div>

          {/* SECTION 3: MODELLED TRADITIONAL CHAIN GAP & 14-DAY ACTIVITY */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Modelled Scenario Comparison Card */}
            <div className="bg-surface rounded-xl border border-gray-200 p-6 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <IndianRupee className="w-5 h-5 text-primary" />
                    <h3 className="text-base font-bold text-ink">Modelled Price Scenario vs APMC Chain</h3>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-gray-100 text-muted uppercase font-semibold">
                    {priceGap?.basis}
                  </span>
                </div>

                <p className="text-xs text-muted mb-4">
                  Comparative scenario evaluation against traditional multi-tier APMC mandi supply chains
                  evaluated across {priceGap?.orders_considered ?? 0} platform orders.
                </p>

                <div className="grid grid-cols-2 gap-4 my-4">
                  <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200">
                    <span className="text-xs text-emerald-800 font-semibold block uppercase">Farmer Net Realisation</span>
                    <div className="text-2xl font-bold text-emerald-700 mt-1">
                      {priceGap?.avg_farmer_delta_pct !== null && priceGap?.avg_farmer_delta_pct !== undefined
                        ? `+${priceGap.avg_farmer_delta_pct}%`
                        : 'N/A'}
                    </div>
                    <span className="text-xs text-emerald-600 mt-1 block">Above local mandi net return</span>
                  </div>

                  <div className="p-4 rounded-xl bg-blue-50 border border-blue-200">
                    <span className="text-xs text-blue-800 font-semibold block uppercase">Buyer Landed Cost</span>
                    <div className="text-2xl font-bold text-blue-700 mt-1">
                      {priceGap?.avg_buyer_delta_pct !== null && priceGap?.avg_buyer_delta_pct !== undefined
                        ? `${priceGap.avg_buyer_delta_pct > 0 ? '+' : ''}${priceGap.avg_buyer_delta_pct}%`
                        : 'N/A'}
                    </div>
                    <span className="text-xs text-blue-600 mt-1 block">vs traditional retail baseline</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-100 text-[11px] text-muted flex items-start space-x-2">
                <Info className="w-4 h-4 text-muted shrink-0 mt-0.5" />
                <span>
                  Evaluated using research parameters: 5% commission agent fee, 8% trader margin, 12% retail margin,
                  and ₹1.00/kg last-mile logistics. Not a guarantee of historical savings.
                </span>
              </div>
            </div>

            {/* 14-Day Activity Spark / Daily Table */}
            <div className="bg-surface rounded-xl border border-gray-200 p-6 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <Calendar className="w-5 h-5 text-primary" />
                    <h3 className="text-base font-bold text-ink">14-Day Committed Orders Timeline</h3>
                  </div>
                  <span className="text-xs text-muted">Daily volume in kg</span>
                </div>

                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {overview.daily.map((d) => (
                    <div
                      key={d.date}
                      className="flex items-center justify-between text-xs py-1.5 px-3 rounded-lg bg-bg border border-gray-100"
                    >
                      <span className="font-mono text-ink font-medium">{d.date}</span>
                      <div className="flex items-center space-x-4">
                        <span className="text-muted">{d.orders} orders</span>
                        <span className="font-semibold text-ink w-20 text-right">
                          {d.volume_kg.toLocaleString()} kg
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-gray-100 text-xs text-muted flex items-center justify-between">
                <span>Model Pipeline: <strong className="text-ink">{overview.model.deployed_method}</strong></span>
                <span>Source: <strong className="text-ink font-mono">{overview.model.data_source}</strong></span>
                {overview.model.model_version && (
                  <span>Version: <strong className="text-ink font-mono">{overview.model.model_version}</strong></span>
                )}
              </div>
            </div>
          </div>

          {/* SECTION 4: HUB × CROP SUPPLY-DEMAND MATRIX */}
          <div className="bg-surface rounded-xl border border-gray-200 p-6 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <Layers className="w-5 h-5 text-primary" />
                  <h3 className="text-base font-bold text-ink">Hub × Crop Supply vs Demand Matrix</h3>
                </div>
                <p className="text-xs text-muted mt-1">
                  Compares 7-day predicted demand against active produce supply attributed to the nearest hub (Rule D-026).
                </p>
              </div>

              {/* Crop Filter Dropdown */}
              <div className="flex items-center space-x-2">
                <label className="text-xs font-semibold text-muted">Filter Crop:</label>
                <select
                  value={selectedCropId || ''}
                  onChange={(e) => setSelectedCropId(e.target.value ? Number(e.target.value) : null)}
                  className="text-xs bg-bg border border-gray-200 rounded-lg px-3 py-1.5 text-ink focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="">All 5 Crops (Full Matrix)</option>
                  {CROPS.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Matrix Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-gray-200 bg-bg text-muted font-semibold uppercase tracking-wider">
                    <th className="py-2.5 px-3">Demand Hub</th>
                    <th className="py-2.5 px-3">Crop</th>
                    <th className="py-2.5 px-3 text-right">7-Day Forecast Demand</th>
                    <th className="py-2.5 px-3 text-right">Attributed Supply</th>
                    <th className="py-2.5 px-3 text-right">Supply / Demand Ratio</th>
                    <th className="py-2.5 px-3 text-center">Market Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {supplyDemand?.rows.map((row) => (
                    <tr key={`${row.hub_id}-${row.crop_id}`} className="hover:bg-bg/60 transition-colors">
                      <td className="py-2.5 px-3 font-semibold text-ink">{row.hub}</td>
                      <td className="py-2.5 px-3 text-ink">{row.crop}</td>
                      <td className="py-2.5 px-3 text-right font-mono">
                        {row.forecast_7d_kg.toLocaleString()} kg
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-medium">
                        {row.supply_kg.toLocaleString()} kg
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono">{row.ratio.toFixed(2)}</td>
                      <td className="py-2.5 px-3 text-center">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase ${
                            row.status === 'SHORTAGE'
                              ? 'bg-amber-100 text-amber-800'
                              : row.status === 'SURPLUS'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {supplyDemand?.rows.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-muted">
                        No supply-demand records found for the selected criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between text-xs text-muted pt-3 border-t border-gray-100 gap-2">
              <span className="flex items-center space-x-1">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Forecasting Engine: <strong className="text-ink">{supplyDemand?.method}</strong> (80% Quantile Intervals)</span>
              </span>
              <Link
                to="/forecast"
                className="text-primary hover:underline font-semibold inline-flex items-center space-x-1"
              >
                <span>View Full Demand Intelligence & Model Card</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
