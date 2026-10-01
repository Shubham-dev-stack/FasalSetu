import React from 'react';
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ForecastDailyItem, ForecastHistoryItem } from '../../api/types';

interface ForecastChartProps {
  history: ForecastHistoryItem[];
  forecast: ForecastDailyItem[];
  method: string;
  cropName: string;
  hubName: string;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  history,
  forecast,
  method,
  cropName,
  hubName,
}) => {
  // Use last 14 days of history for clear visual contrast with 7-day forecast
  const visibleHistory = history.slice(-14);

  // Build unified series
  const data: Array<{
    date: string;
    label: string;
    observed_demand?: number;
    forecast_point?: number;
    interval_range?: [number, number];
    interval_lo?: number;
    interval_hi?: number;
  }> = [];

  // Historical points
  visibleHistory.forEach((h) => {
    const dStr = h.date.slice(5); // MM-DD
    data.push({
      date: h.date,
      label: dStr,
      observed_demand: h.demand_kg,
    });
  });

  // Connect transition point (last historical point connects to forecast)
  if (visibleHistory.length > 0 && forecast.length > 0) {
    const lastHist = visibleHistory[visibleHistory.length - 1];
    data[data.length - 1].forecast_point = lastHist.demand_kg;
    if (forecast[0].interval_lo_kg !== null && forecast[0].interval_lo_kg !== undefined) {
      data[data.length - 1].interval_range = [lastHist.demand_kg, lastHist.demand_kg];
      data[data.length - 1].interval_lo = lastHist.demand_kg;
      data[data.length - 1].interval_hi = lastHist.demand_kg;
    }
  }

  // Forecast points
  forecast.forEach((f) => {
    const dStr = f.date.slice(5);
    const hasInterval = f.interval_lo_kg !== null && f.interval_lo_kg !== undefined;
    data.push({
      date: f.date,
      label: `${dStr} (${f.day_of_week.slice(0, 3)})`,
      forecast_point: f.point_forecast_kg,
      interval_range: hasInterval ? [f.interval_lo_kg!, f.interval_hi_kg!] : undefined,
      interval_lo: f.interval_lo_kg ?? undefined,
      interval_hi: f.interval_hi_kg ?? undefined,
    });
  });

  const isLgbm = method === 'LIGHTGBM';

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3">
        <div>
          <h3 className="text-sm font-bold text-gray-900">
            {cropName} Demand Trajectory — {hubName}
          </h3>
          <p className="text-xs text-gray-500">
            14-Day Observed History &amp; 7-Day Forward Projections
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${
              isLgbm
                ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                : 'bg-amber-50 text-amber-800 border-amber-300'
            }`}
          >
            {isLgbm ? 'LightGBM Quantile (80% Interval)' : 'Seasonal Naive Fallback'}
          </span>
        </div>
      </div>

      <div className="w-full h-72" style={{ minHeight: '280px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="label"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              unit=" kg"
              tickFormatter={(val) => `${val}`}
            />
            <Tooltip
              formatter={(value: any, name: string) => {
                if (name === 'interval_range') return null;
                const formatted = typeof value === 'number' ? `${value.toFixed(1)} kg` : value;
                if (name === 'observed_demand') return [formatted, 'Observed Demand'];
                if (name === 'forecast_point') return [formatted, 'Forecast (ŷ)'];
                return [formatted, name];
              }}
              labelFormatter={(label, payload) => {
                const item = payload && payload[0]?.payload;
                return item?.date ? `Date: ${item.date} (${label})` : label;
              }}
              contentStyle={{
                backgroundColor: '#ffffff',
                borderColor: '#e2e8f0',
                borderRadius: '0.5rem',
                fontSize: '0.75rem',
              }}
            />
            <Legend
              verticalAlign="top"
              height={32}
              formatter={(value) => {
                if (value === 'observed_demand') return 'Observed Demand';
                if (value === 'forecast_point') return 'Forecast Demand';
                if (value === 'interval_range') return '80% Confidence Interval';
                return value;
              }}
            />

            {/* 80% Confidence Band (Area) */}
            {isLgbm && (
              <Area
                type="monotone"
                dataKey="interval_range"
                stroke="none"
                fill="#10b981"
                fillOpacity={0.18}
                name="interval_range"
                isAnimationActive={false}
              />
            )}

            {/* Historical Observed Demand */}
            <Line
              type="monotone"
              dataKey="observed_demand"
              stroke="#64748b"
              strokeWidth={2}
              dot={{ r: 3, fill: '#64748b' }}
              name="observed_demand"
              isAnimationActive={false}
            />

            {/* Projected Demand Point */}
            <Line
              type="monotone"
              dataKey="forecast_point"
              stroke="#059669"
              strokeWidth={2.5}
              strokeDasharray={isLgbm ? undefined : '4 4'}
              dot={{ r: 4, fill: '#059669' }}
              name="forecast_point"
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500 pt-1 border-t border-gray-100">
        <span>History: Observed bulk buyer demand (kg/day)</span>
        <span>Forecast: Information cutoff strictly at or before T</span>
      </div>
    </div>
  );
};
