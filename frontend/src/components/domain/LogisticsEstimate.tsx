import React from 'react';
import { LogisticsEstimateResponse } from '../../api/types';

interface LogisticsEstimateProps {
  estimate: LogisticsEstimateResponse;
  quantityKg: number;
}

export const LogisticsEstimate: React.FC<LogisticsEstimateProps> = ({
  estimate,
  quantityKg,
}) => {
  return (
    <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-4 space-y-3 text-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 font-semibold text-emerald-900">
          <span>🚚</span>
          <span>Dedicated Logistics Estimate</span>
        </div>
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 uppercase tracking-wider">
          {estimate.basis}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-ink">
        <div className="bg-white p-2.5 rounded-lg border border-emerald-100">
          <span className="text-[10px] text-muted block">Distance</span>
          <span className="font-bold text-sm text-gray-900">{estimate.distance_km} km</span>
          <span className="text-[9px] text-muted block mt-0.5 truncate">
            {estimate.distance_source === 'ESTIMATED_HAVERSINE' ? 'Haversine (1.35x)' : estimate.distance_source}
          </span>
        </div>

        <div className="bg-white p-2.5 rounded-lg border border-emerald-100">
          <span className="text-[10px] text-muted block">Est. Transit</span>
          <span className="font-bold text-sm text-gray-900">{estimate.transit_hours} hrs</span>
          <span className="text-[9px] text-muted block mt-0.5">@ 30 km/h + 40m svc</span>
        </div>

        <div className="bg-white p-2.5 rounded-lg border border-emerald-100">
          <span className="text-[10px] text-muted block">Transport / kg</span>
          <span className="font-bold text-sm text-emerald-700">₹{estimate.cost_per_kg.toFixed(2)}</span>
          <span className="text-[9px] text-muted block mt-0.5">for {quantityKg} kg</span>
        </div>

        <div className="bg-white p-2.5 rounded-lg border border-emerald-100">
          <span className="text-[10px] text-muted block">Total Transport</span>
          <span className="font-bold text-sm text-gray-900">₹{estimate.cost_total.toFixed(2)}</span>
          <span className="text-[9px] text-muted block mt-0.5">
            {estimate.trips} trip{estimate.trips > 1 ? 's' : ''} round-trip
          </span>
        </div>
      </div>

      {estimate.vehicle_plan && estimate.vehicle_plan.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <span className="text-[11px] font-medium text-emerald-900 block">Vehicle Allocation:</span>
          <div className="space-y-1">
            {estimate.vehicle_plan.map((leg, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between bg-white/80 px-2.5 py-1.5 rounded-lg border border-emerald-100 text-[11px]"
              >
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-800">
                    {leg.trips > 1 ? `${leg.trips}x ` : ''}
                    {leg.vehicle_type.replace('_', ' ')}
                  </span>
                  <span className="text-muted text-[10px]">
                    (cap: {leg.capacity_kg} kg • load: {leg.load_kg} kg)
                  </span>
                </div>
                <span className="font-medium text-gray-900">
                  ₹{leg.total_cost.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
