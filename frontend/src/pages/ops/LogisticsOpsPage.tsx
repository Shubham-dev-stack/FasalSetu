import React, { useEffect, useState } from 'react';
import { useAuth } from '../../lib/auth';
import { fetchVehiclesApi } from '../../api/logistics';
import { FleetVehicle } from '../../api/types';

export const LogisticsOpsPage: React.FC = () => {
  const { token } = useAuth();
  const [vehicles, setVehicles] = useState<FleetVehicle[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadVehicles = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchVehiclesApi(token);
      setVehicles(res.items);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load fleet vehicles.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVehicles();
  }, [token]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-gray-900">Logistics & Fleet Operations</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
              Phase 8 Active
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Regional fleet inventory and dedicated trip cost models for Delhi-NCR agricultural distribution.
          </p>
        </div>
        <div>
          <button
            disabled
            title="Multi-stop VRP route optimization is enabled in Phase 9"
            className="px-4 py-2 bg-gray-200 text-gray-400 text-xs font-semibold rounded-lg cursor-not-allowed flex items-center gap-1.5"
          >
            <span>⚡</span>
            <span>Optimize Routes (Phase 9)</span>
          </button>
        </div>
      </div>

      {/* Fleet Inventory Table */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-gray-900">Fleet Vehicles Inventory</h2>
            <p className="text-xs text-gray-500">
              Active transport vehicles available for dedicated freight and multi-stop consolidation.
            </p>
          </div>
          <span className="text-xs font-semibold px-2 py-1 bg-gray-100 text-gray-700 rounded-md">
            {vehicles.length} Vehicles Registered
          </span>
        </div>

        {loading ? (
          <div className="p-10 text-center space-y-2">
            <span className="animate-spin inline-block w-6 h-6 border-2 border-primary border-t-transparent rounded-full" />
            <p className="text-xs text-muted">Loading fleet inventory...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center space-y-3">
            <p className="text-xs text-rose-600 font-medium">{error}</p>
            <button
              onClick={loadVehicles}
              className="px-3 py-1.5 text-xs bg-rose-50 text-rose-700 rounded-lg border border-rose-200 hover:bg-rose-100"
            >
              Retry
            </button>
          </div>
        ) : vehicles.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted">
            No vehicles currently registered in fleet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50/70 border-b border-gray-200 text-gray-500 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Vehicle ID & Name</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4 text-right">Capacity (kg)</th>
                  <th className="py-3 px-4 text-right">Cost / km (₹)</th>
                  <th className="py-3 px-4 text-right">Fixed Trip (₹)</th>
                  <th className="py-3 px-4 text-right">Avg Speed</th>
                  <th className="py-3 px-4">Home Depot</th>
                  <th className="py-3 px-4 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-700">
                {vehicles.map((v) => (
                  <tr key={v.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="py-3 px-4 font-bold text-gray-900">
                      #{v.id} • {v.name}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                        {v.vehicle_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-medium">{v.capacity_kg.toLocaleString()} kg</td>
                    <td className="py-3 px-4 text-right">₹{v.cost_per_km.toFixed(2)}</td>
                    <td className="py-3 px-4 text-right">₹{v.fixed_cost_per_trip.toFixed(2)}</td>
                    <td className="py-3 px-4 text-right">{v.avg_speed_kmph} km/h</td>
                    <td className="py-3 px-4 text-gray-600">
                      <div className="truncate max-w-[200px]" title={v.depot_name}>
                        {v.depot_name}
                      </div>
                      <span className="text-[10px] text-gray-400 block">
                        ({v.depot_lat.toFixed(2)}, {v.depot_lng.toFixed(2)})
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          v.is_available
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {v.is_available ? 'AVAILABLE' : 'OFFLINE'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Dedicated Logistics Formula Note */}
      <div className="bg-blue-50/60 border border-blue-200 rounded-xl p-4 text-xs text-blue-900 space-y-1.5">
        <div className="flex items-center gap-1.5 font-bold">
          <span>ℹ️</span>
          <span>Dedicated Logistics Cost Formulation (ML.md §11)</span>
        </div>
        <p className="text-[11px] text-blue-800 leading-relaxed">
          Trip cost is calculated deterministically as:{' '}
          <code className="bg-white px-1 py-0.5 rounded text-blue-950 font-mono text-[10px]">
            Fixed Cost + (Cost/km × Road Distance × 2.0 Return Factor)
          </code>
          . Multi-trip loads select the largest available vehicle type first, with remainder allocated to the smallest fitting vehicle. Multi-stop capacitated vehicle routing (VRP) will be enabled in Phase 9.
        </p>
      </div>
    </div>
  );
};
