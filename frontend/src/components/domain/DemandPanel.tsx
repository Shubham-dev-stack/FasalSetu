import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  MapPin,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { getDemandForecast, getHubsForecast, getModelInfo } from '../../api/forecasts';
import { fetchPricingBenchmarkApi } from '../../api/pricing';
import {
  ForecastDemandResponse,
  ForecastHubsResponse,
  ModelInfoResponse,
  PricingBenchmarkResponse,
} from '../../api/types';
import { ForecastChart } from '../charts/ForecastChart';
import { ModelInfoModal } from './ModelInfoModal';

interface DemandPanelProps {
  cropId: number;
  cropName: string;
  approxBenchmarkModal?: number | null;
  nearestHubId?: number;
  nearestHubName?: string;
}

export const DemandPanel: React.FC<DemandPanelProps> = ({
  cropId,
  cropName,
  approxBenchmarkModal,
  nearestHubId = 1,
  nearestHubName = 'Delhi North',
}) => {
  const [demandForecast, setDemandForecast] = useState<ForecastDemandResponse | null>(null);
  const [hubsForecast, setHubsForecast] = useState<ForecastHubsResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);
  const [benchmarkData, setBenchmarkData] = useState<PricingBenchmarkResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [showChart, setShowChart] = useState<boolean>(false);
  const [showModelModal, setShowModelModal] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    Promise.all([
      getDemandForecast(nearestHubId, cropId, 7),
      getHubsForecast(cropId, 7),
      fetchPricingBenchmarkApi({ crop_id: cropId, hub_id: nearestHubId }).catch(() => null),
    ])
      .then(([df, hf, bm]) => {
        if (!isMounted) return;
        setDemandForecast(df);
        setHubsForecast(hf);
        if (bm) setBenchmarkData(bm);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Failed to load forecast intelligence:', err);
        setError('Forecast intelligence temporarily unavailable.');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [cropId, nearestHubId]);

  const handleOpenModelCard = async () => {
    setShowModelModal(true);
    if (!modelInfo) {
      try {
        const info = await getModelInfo();
        setModelInfo(info);
      } catch (err) {
        console.error('Failed to fetch model card:', err);
      }
    }
  };

  const modalPrice = benchmarkData?.benchmark
    ? benchmarkData.benchmark.modal_price_per_kg
    : (approxBenchmarkModal ?? 22.5);
  const fairBand = benchmarkData?.fair_band;
  const benchmarkSource = benchmarkData?.benchmark?.source;
  const isLgbm = demandForecast?.method === 'LIGHTGBM';

  // Compute 7-day total and daily avg for nearest hub
  const sevenDayTotal = demandForecast
    ? demandForecast.forecast.reduce((sum, item) => sum + item.point_forecast_kg, 0)
    : 0;
  const sevenDayDailyAvg = sevenDayTotal / 7;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">
      {/* Header & Source Badge */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-800">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-gray-900">Demand &amp; Price Intelligence</h3>
            <p className="text-xs text-gray-500">Live 7-Day ML Projections &amp; Market Benchmark Band</p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5">
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${
              isLgbm
                ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                : 'bg-amber-50 text-amber-800 border-amber-300'
            }`}
          >
            {isLgbm ? 'LightGBM Point + 80% CI' : 'Seasonal Naive Fallback'}
          </span>
          <button
            type="button"
            onClick={handleOpenModelCard}
            title="Inspect Model Card & Gate Results"
            className="p-1 text-gray-400 hover:text-emerald-700 transition-colors"
          >
            <HelpCircle className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Benchmark Info Card */}
      <div className="bg-slate-50 rounded-lg p-3 border border-gray-200/80 space-y-2 text-xs">
        <div className="flex items-center justify-between text-gray-500">
          <span className="flex items-center space-x-1">
            <MapPin className="w-3.5 h-3.5 text-gray-400" />
            <span>Target Nearest Hub:</span>
          </span>
          <div className="flex items-center gap-1.5">
            <strong className="text-gray-900 font-semibold">{nearestHubName}</strong>
            {benchmarkSource && (
              <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-gray-200 text-gray-700">
                {benchmarkSource}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-baseline justify-between pt-1">
          <span className="text-gray-500">{cropName} Benchmark Modal:</span>
          <div className="text-right">
            <span className="text-base font-bold text-gray-900 font-mono">₹{modalPrice.toFixed(2)}</span>
            <span className="text-gray-500"> / kg</span>
          </div>
        </div>

        <div className="flex items-center justify-between pt-1 border-t border-gray-200/60">
          <span className="text-gray-500">Recommended Fair Ask Band:</span>
          {fairBand ? (
            <span className="font-semibold text-emerald-700 font-mono">
              ₹{fairBand.low.toFixed(2)} – ₹{fairBand.high.toFixed(2)} / kg
            </span>
          ) : (
            <span className="font-semibold text-emerald-700 font-mono">
              ₹{(modalPrice * 0.95).toFixed(2)} – ₹{(modalPrice * 1.15).toFixed(2)} / kg
            </span>
          )}
        </div>
      </div>

      {/* Forecast Status & Projections */}
      {loading ? (
        <div className="py-6 text-center text-xs text-gray-500 space-y-1">
          <span className="animate-spin inline-block w-4 h-4 border-2 border-emerald-600 border-t-transparent rounded-full" />
          <p>Calculating 7-day demand projections...</p>
        </div>
      ) : error ? (
        <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-amber-600" />
          <span>{error}</span>
        </div>
      ) : demandForecast ? (
        <div className="space-y-3">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-emerald-50/50 border border-emerald-200/70 p-2.5 rounded-lg">
              <span className="text-[11px] text-emerald-900 font-medium block">7-Day Projected Demand</span>
              <div className="text-base font-extrabold text-emerald-950 font-mono mt-0.5">
                {sevenDayTotal.toLocaleString('en-IN', { maximumFractionDigits: 0 })} <span className="text-xs font-normal text-emerald-800">kg</span>
              </div>
              <span className="text-[10px] text-emerald-700 block mt-0.5">
                ~{sevenDayDailyAvg.toFixed(0)} kg / day
              </span>
            </div>

            <div className="bg-slate-50 border border-gray-200 p-2.5 rounded-lg">
              <span className="text-[11px] text-gray-600 font-medium block">80% Interval Band</span>
              <div className="text-xs font-bold text-gray-800 font-mono mt-1">
                {isLgbm && demandForecast.forecast[0].interval_lo_kg !== null ? (
                  <span>
                    {demandForecast.forecast[0].interval_lo_kg?.toFixed(0)} –{' '}
                    {demandForecast.forecast[0].interval_hi_kg?.toFixed(0)} kg (Day 1)
                  </span>
                ) : (
                  <span className="text-gray-400 font-normal">N/A (Naive Point)</span>
                )}
              </div>
              <span className="text-[10px] text-gray-400 block mt-0.5">Direct direct-strategy</span>
            </div>
          </div>

          {/* Toggle Trajectory Chart */}
          <div>
            <button
              type="button"
              onClick={() => setShowChart(!showChart)}
              className="w-full py-1.5 px-3 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg text-xs font-semibold text-gray-700 flex items-center justify-between transition-colors"
            >
              <span>{showChart ? 'Hide Trajectory Chart' : 'Show Demand Trajectory Chart'}</span>
              {showChart ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>

            {showChart && (
              <div className="mt-2.5">
                <ForecastChart
                  history={demandForecast.history}
                  forecast={demandForecast.forecast}
                  method={demandForecast.method}
                  cropName={cropName}
                  hubName={nearestHubName}
                />
              </div>
            )}
          </div>

          {/* Regional Hub Opportunities (Rule D-026) */}
          {hubsForecast && hubsForecast.hubs.length > 0 && (
            <div className="space-y-1.5 pt-2 border-t border-gray-100">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-gray-800">Regional Hub Shortage Ranking:</span>
                <span className="text-[10px] text-gray-500">Supply-Demand Ratio</span>
              </div>

              <div className="space-y-1">
                {hubsForecast.hubs.map((hub) => {
                  const isShortage = hub.opportunity_label === 'HIGH_DEFICIT';
                  const isBalanced = hub.opportunity_label === 'BALANCED';
                  return (
                    <div
                      key={hub.hub_id}
                      className={`flex items-center justify-between p-2 rounded-lg text-xs border ${
                        hub.hub_id === nearestHubId
                          ? 'border-emerald-300 bg-emerald-50/30'
                          : 'border-gray-200 bg-white'
                      }`}
                    >
                      <div className="flex items-center space-x-1.5">
                        <span className="font-semibold text-gray-900">{hub.hub_name}</span>
                        {hub.hub_id === nearestHubId && (
                          <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-1.5 py-0.2 rounded">
                            Local
                          </span>
                        )}
                      </div>

                      <div className="flex items-center space-x-2">
                        <span className="text-gray-500 text-[11px] font-mono">
                          {hub.total_forecast_kg.toFixed(0)} kg
                        </span>
                        <span
                          className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                            isShortage
                              ? 'bg-rose-50 text-rose-800 border-rose-200'
                              : isBalanced
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                              : 'bg-slate-50 text-slate-700 border-slate-200'
                          }`}
                        >
                          {isShortage ? 'Deficit (High Opp)' : isBalanced ? 'Balanced' : 'Oversupplied'}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Model Card Link & Synthetic Notice */}
          <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-500">
            <button
              type="button"
              onClick={handleOpenModelCard}
              className="inline-flex items-center space-x-1 text-emerald-700 hover:text-emerald-900 font-semibold"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Model Card &amp; Validation Integrity</span>
            </button>
            <span className="text-[10px] text-gray-400">Demand: Synthetic DS-01</span>
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
