import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  ShieldCheck,
  AlertCircle,
  Info,
} from 'lucide-react';
import { getDemandForecast, getHubsForecast, getModelInfo } from '../../api/forecasts';
import {
  ForecastDemandResponse,
  ForecastHubsResponse,
  ModelInfoResponse,
} from '../../api/types';
import { ForecastChart } from '../../components/charts/ForecastChart';
import { ModelInfoModal } from '../../components/domain/ModelInfoModal';

const CROPS = [
  { id: 1, name: 'Tomato' },
  { id: 2, name: 'Onion' },
  { id: 3, name: 'Potato' },
  { id: 4, name: 'Cauliflower' },
  { id: 5, name: 'Green Chilli' },
];

const HUBS = [
  { id: 1, name: 'Delhi North', state: 'Delhi' },
  { id: 2, name: 'Delhi South', state: 'Delhi' },
  { id: 3, name: 'Gurugram', state: 'Haryana' },
  { id: 4, name: 'Noida', state: 'Uttar Pradesh' },
  { id: 5, name: 'Sonipat', state: 'Haryana' },
];

export const ForecastPage: React.FC = () => {
  const [selectedCropId, setSelectedCropId] = useState<number>(1);
  const [selectedHubId, setSelectedHubId] = useState<number>(1);
  const [horizonDays, setHorizonDays] = useState<number>(7);

  const [demandData, setDemandData] = useState<ForecastDemandResponse | null>(null);
  const [hubsData, setHubsData] = useState<ForecastHubsResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showModelModal, setShowModelModal] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    Promise.all([
      getDemandForecast(selectedHubId, selectedCropId, horizonDays),
      getHubsForecast(selectedCropId, horizonDays),
    ])
      .then(([demandRes, hubsRes]) => {
        if (!isMounted) return;
        setDemandData(demandRes);
        setHubsData(hubsRes);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Error fetching demand forecast:', err);
        setError(err.message || 'Failed to fetch demand forecasts.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedCropId, selectedHubId, horizonDays]);

  const handleOpenModelCard = async () => {
    setShowModelModal(true);
    if (!modelInfo) {
      try {
        const info = await getModelInfo();
        setModelInfo(info);
      } catch (err) {
        console.error('Failed to load model card:', err);
      }
    }
  };

  const selectedCrop = CROPS.find((c) => c.id === selectedCropId) || CROPS[0];
  const selectedHub = HUBS.find((h) => h.id === selectedHubId) || HUBS[0];

  const totalDemand = demandData
    ? demandData.forecast.reduce((sum, item) => sum + item.point_forecast_kg, 0)
    : 0;
  const avgDailyDemand = horizonDays > 0 ? totalDemand / horizonDays : 0;
  const isLgbm = demandData?.method === 'LIGHTGBM';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-200">
        <div>
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-emerald-100 text-emerald-800 rounded-lg">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-gray-900">Regional Demand Intelligence</h1>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Machine learning demand forecasts and multi-hub opportunity rankings across Northern India.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleOpenModelCard}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-emerald-300 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-semibold shadow-sm transition-colors"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-700" />
            <span>Model Card &amp; Integrity (MOD-01)</span>
          </button>
        </div>
      </div>

      {/* Control Bar: Crop, Hub, Horizon */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Crop Selector */}
        <div>
          <label className="block text-xs font-bold text-gray-700 mb-1.5">Select Commodity Crop</label>
          <select
            value={selectedCropId}
            onChange={(e) => setSelectedCropId(Number(e.target.value))}
            className="w-full text-xs font-semibold px-3 py-2 bg-slate-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            {CROPS.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Hub Selector */}
        <div>
          <label className="block text-xs font-bold text-gray-700 mb-1.5">Primary Demand Hub</label>
          <select
            value={selectedHubId}
            onChange={(e) => setSelectedHubId(Number(e.target.value))}
            className="w-full text-xs font-semibold px-3 py-2 bg-slate-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            {HUBS.map((h) => (
              <option key={h.id} value={h.id}>
                {h.name} ({h.state})
              </option>
            ))}
          </select>
        </div>

        {/* Horizon Selector */}
        <div>
          <label className="block text-xs font-bold text-gray-700 mb-1.5">Forecast Horizon</label>
          <select
            value={horizonDays}
            onChange={(e) => setHorizonDays(Number(e.target.value))}
            className="w-full text-xs font-semibold px-3 py-2 bg-slate-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            <option value={1}>1 Day Ahead</option>
            <option value={3}>3 Days Ahead</option>
            <option value={5}>5 Days Ahead</option>
            <option value={7}>7 Days Ahead (Standard)</option>
          </select>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="py-20 text-center text-gray-500 space-y-2">
          <span className="animate-spin inline-block w-8 h-8 border-3 border-emerald-600 border-t-transparent rounded-full" />
          <p className="text-sm font-medium">Executing LightGBM quantile inference pipeline...</p>
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-sm flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 shrink-0 text-amber-600 mt-0.5" />
          <div>
            <h4 className="font-bold">Unable to load forecast data</h4>
            <p className="text-xs text-amber-800 mt-0.5">{error}</p>
          </div>
        </div>
      ) : demandData ? (
        <div className="space-y-6">
          {/* Key Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <span className="text-xs font-semibold text-gray-500 block">
                Total {horizonDays}-Day Projected Demand
              </span>
              <div className="text-2xl font-extrabold text-emerald-950 font-mono mt-1">
                {totalDemand.toLocaleString('en-IN', { maximumFractionDigits: 0 })}{' '}
                <span className="text-xs font-normal text-emerald-700">kg</span>
              </div>
              <span className="text-[11px] text-gray-400 mt-1 block">
                Across {selectedHub.name} bulk buyers
              </span>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <span className="text-xs font-semibold text-gray-500 block">Average Daily Demand</span>
              <div className="text-2xl font-extrabold text-gray-900 font-mono mt-1">
                {avgDailyDemand.toLocaleString('en-IN', { maximumFractionDigits: 0 })}{' '}
                <span className="text-xs font-normal text-gray-500">kg / day</span>
              </div>
              <span className="text-[11px] text-emerald-700 font-medium mt-1 block">
                Normalized daily requirement
              </span>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <span className="text-xs font-semibold text-gray-500 block">Day 1 Uncertainty (80% CI)</span>
              <div className="text-lg font-bold text-gray-900 font-mono mt-1.5">
                {isLgbm && demandData.forecast[0].interval_lo_kg !== null ? (
                  <span>
                    {demandData.forecast[0].interval_lo_kg?.toFixed(0)} –{' '}
                    {demandData.forecast[0].interval_hi_kg?.toFixed(0)}{' '}
                    <span className="text-xs font-normal text-gray-500">kg</span>
                  </span>
                ) : (
                  <span className="text-gray-400 text-sm font-normal">N/A (Naive Point)</span>
                )}
              </div>
              <span className="text-[11px] text-gray-400 mt-1 block">
                LightGBM q10 .. q90 interval
              </span>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <span className="text-xs font-semibold text-gray-500 block">Active Model Method</span>
              <div className="mt-1.5">
                <span
                  className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold border ${
                    isLgbm
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                      : 'bg-amber-50 text-amber-800 border-amber-300'
                  }`}
                >
                  {isLgbm ? 'LightGBM Direct' : 'Seasonal Naive'}
                </span>
              </div>
              <span className="text-[11px] text-gray-400 mt-1.5 block">
                Model version {demandData.model_version}
              </span>
            </div>
          </div>

          {/* Forecast Visual Chart */}
          <ForecastChart
            history={demandData.history}
            forecast={demandData.forecast}
            method={demandData.method}
            cropName={selectedCrop.name}
            hubName={selectedHub.name}
          />

          {/* Daily Breakdown Table */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-gray-900">
                  Daily Demand Projections &amp; Uncertainty Range
                </h3>
                <p className="text-xs text-gray-500">
                  Forward horizon from cutoff date {demandData.cutoff_date}
                </p>
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-gray-200 text-gray-700 font-semibold">
                  <tr>
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Day of Week</th>
                    <th className="py-2.5 px-3">Point Forecast (ŷ)</th>
                    <th className="py-2.5 px-3">80% Lower (q10)</th>
                    <th className="py-2.5 px-3">80% Upper (q90)</th>
                    <th className="py-2.5 px-3">Interval Spread</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {demandData.forecast.map((item, idx) => {
                    const hasInterval = item.interval_lo_kg !== null && item.interval_hi_kg !== null;
                    const spread = hasInterval ? item.interval_hi_kg! - item.interval_lo_kg! : null;
                    return (
                      <tr key={item.date} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/40'}>
                        <td className="py-2 px-3 font-semibold text-gray-900">{item.date}</td>
                        <td className="py-2 px-3 text-gray-600">{item.day_of_week}</td>
                        <td className="py-2 px-3 font-bold font-mono text-emerald-800">
                          {item.point_forecast_kg.toFixed(1)} kg
                        </td>
                        <td className="py-2 px-3 font-mono text-gray-600">
                          {hasInterval ? `${item.interval_lo_kg!.toFixed(1)} kg` : '—'}
                        </td>
                        <td className="py-2 px-3 font-mono text-gray-600">
                          {hasInterval ? `${item.interval_hi_kg!.toFixed(1)} kg` : '—'}
                        </td>
                        <td className="py-2 px-3 font-mono text-gray-500">
                          {spread !== null ? `±${(spread / 2).toFixed(1)} kg` : 'Point only'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Regional Hub Opportunities (Rule D-026 Supply Attribution) */}
          {hubsData && hubsData.hubs.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-bold text-gray-900">
                    Regional Hub Shortage &amp; Supply-Demand Ratios (Rule D-026)
                  </h3>
                  <p className="text-xs text-gray-500">
                    Each active produce lot is strictly attributed to the producer's nearest hub center (zero double-counting).
                  </p>
                </div>
                <span className="text-xs text-gray-400">Ranked by lowest supply-demand ratio</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {hubsData.hubs.map((hub) => {
                  const isShortage = hub.opportunity_label === 'HIGH_DEFICIT';
                  const isBalanced = hub.opportunity_label === 'BALANCED';
                  const isSelected = hub.hub_id === selectedHubId;

                  return (
                    <div
                      key={hub.hub_id}
                      onClick={() => setSelectedHubId(hub.hub_id)}
                      className={`cursor-pointer rounded-xl border p-4 transition-all ${
                        isSelected
                          ? 'border-emerald-500 bg-emerald-50/30 ring-2 ring-emerald-500/20'
                          : 'border-gray-200 bg-white hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <h4 className="text-sm font-bold text-gray-900">{hub.hub_name}</h4>
                          <span className="text-[11px] text-gray-500">{hub.state}</span>
                        </div>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${
                            isShortage
                              ? 'bg-rose-50 text-rose-800 border-rose-200'
                              : isBalanced
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                              : 'bg-slate-50 text-slate-700 border-slate-200'
                          }`}
                        >
                          {isShortage ? 'High Deficit' : isBalanced ? 'Balanced' : 'Oversupplied'}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-xs border-t border-gray-100 pt-2 font-mono">
                        <div>
                          <span className="text-[10px] text-gray-400 font-sans block">Demand Forecast</span>
                          <span className="font-semibold text-gray-800">{hub.total_forecast_kg.toFixed(0)} kg</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-gray-400 font-sans block">Active Local Supply</span>
                          <span className="font-semibold text-gray-800">{hub.active_supply_kg.toFixed(0)} kg</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-xs border-t border-gray-100 pt-2 mt-2">
                        <span className="text-gray-500">Supply / Demand:</span>
                        <strong className="font-mono text-gray-900">{hub.supply_demand_ratio}x</strong>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Research Transparency Footnote */}
          <div className="bg-slate-50 border border-gray-200 rounded-xl p-4 flex items-start space-x-3 text-xs text-gray-600">
            <Info className="w-5 h-5 text-gray-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <strong className="text-gray-900">Academic &amp; Operational Disclosure:</strong>
              <p className="leading-relaxed">
                {demandData.disclaimer} Demand history is synthetic (Dataset DS-01). Benchmarks anchor against Agmarknet snapshot data. Projections validate the coordination pipeline and honesty gate logic.
              </p>
            </div>
          </div>
        </div>
      ) : null}

      {/* Model Info Modal */}
      <ModelInfoModal
        isOpen={showModelModal}
        onClose={() => setShowModelModal(false)}
        modelInfo={modelInfo}
        loading={!modelInfo}
      />
    </div>
  );
};
