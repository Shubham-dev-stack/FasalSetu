import React from 'react';
import { TrendingUp, Info, MapPin } from 'lucide-react';
import { BenchmarkContext } from '../../api/types';

interface DemandPanelPlaceholderProps {
  selectedCropName?: string;
  benchmarkContext?: BenchmarkContext | null;
  approxBenchmarkModal?: number | null;
}

export const DemandPanelPlaceholder: React.FC<DemandPanelPlaceholderProps> = ({
  selectedCropName = 'Crop',
  benchmarkContext,
  approxBenchmarkModal,
}) => {
  const hubName = benchmarkContext?.nearest_hub_name || 'Delhi North';
  const modalPrice = benchmarkContext?.benchmark_modal_per_kg ?? approxBenchmarkModal ?? 22.50;
  const source = benchmarkContext?.benchmark_source || 'SYNTHETIC_DEMO';

  return (
    <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">
      {/* Header & Source Badge */}
      <div className="flex items-center justify-between border-b border-gray-100 pb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-primary-soft text-primary">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-ink">Demand & Price Intelligence</h3>
            <p className="text-xs text-muted">Nearest Hub Benchmark Context</p>
          </div>
        </div>

        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${
            source === 'AGMARKNET_SNAPSHOT'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
              : 'bg-amber-50 text-amber-800 border-amber-300'
          }`}
        >
          {source === 'AGMARKNET_SNAPSHOT' ? 'Agmarknet Snapshot' : 'Synthetic Benchmark'}
        </span>
      </div>

      {/* Benchmark Info Card */}
      <div className="bg-bg rounded-lg p-3 border border-gray-200/80 space-y-2">
        <div className="flex items-center justify-between text-xs text-muted">
          <span className="flex items-center space-x-1">
            <MapPin className="w-3.5 h-3.5" />
            <span>Nearest Demand Hub:</span>
          </span>
          <strong className="text-ink font-semibold">{hubName}</strong>
        </div>

        <div className="flex items-baseline justify-between pt-1">
          <span className="text-xs text-muted">{selectedCropName} Benchmark Modal:</span>
          <div className="text-right">
            <span className="text-lg font-bold text-ink font-mono">₹{modalPrice.toFixed(2)}</span>
            <span className="text-xs text-muted"> / kg</span>
          </div>
        </div>

        <div className="text-xs text-muted flex items-center justify-between pt-1 border-t border-gray-200/60">
          <span>Recommended Fair Ask Band:</span>
          <span className="font-semibold text-emerald-700">
            ₹{(modalPrice * 0.95).toFixed(2)} – ₹{(modalPrice * 1.15).toFixed(2)} / kg
          </span>
        </div>
      </div>

      {/* Phase 6 Projections Slot Notice */}
      <div className="p-3.5 rounded-lg bg-blue-50/70 border border-blue-200 text-xs text-blue-900 space-y-1.5">
        <div className="flex items-center space-x-1.5 font-semibold text-blue-800">
          <Info className="w-4 h-4 shrink-0" />
          <span>7-Day ML Demand Projections (Phase 6)</span>
        </div>
        <p className="text-blue-800/80 leading-relaxed">
          LightGBM quantile forecasting with 80% confidence intervals and multi-hub shortage ranking
          will activate here in Phase 6 to assist optimal lot allocation.
        </p>
      </div>
    </div>
  );
};
