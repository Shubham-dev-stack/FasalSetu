import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import { fetchVehiclesApi } from '../../api/logistics';
import { fetchOrdersApi } from '../../api/orders';
import { optimizeRoutesApi, fetchRoutePlansApi } from '../../api/routes';
import { FleetVehicle, Order, RoutePlanSummaryItem } from '../../api/types';

export const LogisticsOpsPage: React.FC = () => {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [vehicles, setVehicles] = useState<FleetVehicle[]>([]);
  const [unroutedOrders, setUnroutedOrders] = useState<Order[]>([]);
  const [recentPlans, setRecentPlans] = useState<RoutePlanSummaryItem[]>([]);
  const [selectedOrderIds, setSelectedOrderIds] = useState<number[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [optimizing, setOptimizing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadAllData = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [vehRes, ordRes, planRes] = await Promise.all([
        fetchVehiclesApi(token),
        fetchOrdersApi(token, { status: 'CONFIRMED' }),
        fetchRoutePlansApi(undefined, token),
      ]);
      setVehicles(vehRes.items);
      // Filter orders that have no shipment linked
      const unrouted = ordRes.items.filter((o) => !o.shipment_id);
      setUnroutedOrders(unrouted);
      // Default: all unrouted orders checked
      setSelectedOrderIds(unrouted.map((o) => o.id));
      setRecentPlans(planRes.items);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load logistics operations data.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, [token]);

  const handleToggleOrder = (orderId: number) => {
    setSelectedOrderIds((prev) =>
      prev.includes(orderId) ? prev.filter((id) => id !== orderId) : [...prev, orderId]
    );
  };

  const handleSelectAll = () => {
    if (selectedOrderIds.length === unroutedOrders.length) {
      setSelectedOrderIds([]);
    } else {
      setSelectedOrderIds(unroutedOrders.map((o) => o.id));
    }
  };

  const handleRunOptimization = async () => {
    if (selectedOrderIds.length === 0) return;
    setOptimizing(true);
    setError(null);
    try {
      const plan = await optimizeRoutesApi({
        order_ids: selectedOrderIds,
        time_limit_s: 5,
        distance_mode: 'HAVERSINE',
      });
      navigate(`/ops/routes/${plan.plan_id}`);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Route optimization failed.');
      }
    } finally {
      setOptimizing(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-gray-900">Logistics & Route Operations</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
              Phase 9 Active
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Regional fleet dispatch, capacitated multi-stop VRP route optimization and consolidated transport tracking.
          </p>
        </div>
        <div>
          <button
            onClick={handleRunOptimization}
            disabled={optimizing || unroutedOrders.length === 0 || selectedOrderIds.length === 0}
            className={`px-4 py-2.5 text-xs font-bold rounded-xl shadow-sm flex items-center gap-2 transition-all ${
              optimizing || unroutedOrders.length === 0 || selectedOrderIds.length === 0
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-emerald-600 hover:bg-emerald-700 text-white'
            }`}
          >
            {optimizing ? (
              <>
                <span className="animate-spin inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full" />
                <span>Optimizing VRP Routes...</span>
              </>
            ) : (
              <>
                <span>⚡</span>
                <span>Optimize Selected Routes ({selectedOrderIds.length})</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 font-medium flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-500 font-bold hover:text-rose-800">
            ✕
          </button>
        </div>
      )}

      {/* Orders Pool Checklist */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-gray-900">Unrouted Orders Pool (Ready for Dispatch)</h2>
            <p className="text-xs text-gray-500">
              Confirmed orders without assigned shipments. Select orders to consolidate into optimal multi-stop vehicle routes.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleSelectAll}
              disabled={unroutedOrders.length === 0}
              className="text-xs font-semibold text-emerald-700 hover:underline disabled:text-gray-400"
            >
              {selectedOrderIds.length === unroutedOrders.length ? 'Deselect All' : 'Select All'}
            </button>
            <span className="text-xs font-semibold px-2 py-1 bg-emerald-50 text-emerald-800 rounded-md border border-emerald-200">
              {unroutedOrders.length} Ready
            </span>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center space-y-2">
            <span className="animate-spin inline-block w-6 h-6 border-2 border-emerald-600 border-t-transparent rounded-full" />
            <p className="text-xs text-gray-500">Loading orders pool...</p>
          </div>
        ) : unroutedOrders.length === 0 ? (
          <div className="p-8 text-center text-xs text-gray-500">
            No unrouted confirmed orders currently in the pool. New confirmed orders will appear here for routing.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50/70 border-b border-gray-200 text-gray-500 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4 w-10 text-center">Select</th>
                  <th className="py-3 px-4">Order ID & Crop</th>
                  <th className="py-3 px-4">Origin / Producer</th>
                  <th className="py-3 px-4">Destination / Buyer</th>
                  <th className="py-3 px-4 text-right">Quantity</th>
                  <th className="py-3 px-4 text-right">Est. Cost</th>
                  <th className="py-3 px-4 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-700">
                {unroutedOrders.map((ord) => {
                  const isChecked = selectedOrderIds.includes(ord.id);
                  return (
                    <tr
                      key={ord.id}
                      className={`hover:bg-gray-50/50 cursor-pointer ${isChecked ? 'bg-emerald-50/20' : ''}`}
                      onClick={() => handleToggleOrder(ord.id)}
                    >
                      <td className="py-3 px-4 text-center" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleOrder(ord.id)}
                          className="w-4 h-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500 cursor-pointer"
                        />
                      </td>
                      <td className="py-3 px-4 font-bold text-gray-900">
                        #{ord.id} • {ord.crop?.name || 'Crop'}
                      </td>
                      <td className="py-3 px-4 text-gray-600">
                        {ord.producer?.org_name || 'Producer'}
                      </td>
                      <td className="py-3 px-4 text-gray-600">
                        {ord.buyer?.org_name || 'Buyer'}
                      </td>
                      <td className="py-3 px-4 text-right font-medium text-gray-900">
                        {ord.quantity_kg.toLocaleString()} kg
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-gray-600">
                        ₹{(ord.transport_cost_estimate_per_kg * ord.quantity_kg).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">
                          {ord.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Route Plans */}
      {recentPlans.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-gray-900">Recent Route Optimization Plans</h2>
              <p className="text-xs text-gray-500">
                History of proposed and approved vehicle consolidation plans.
              </p>
            </div>
            <span className="text-xs font-semibold px-2 py-1 bg-gray-100 text-gray-700 rounded-md">
              {recentPlans.length} Plans
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50/70 border-b border-gray-200 text-gray-500 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Plan ID</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Method</th>
                  <th className="py-3 px-4 text-right">Orders</th>
                  <th className="py-3 px-4 text-right">Vehicles</th>
                  <th className="py-3 px-4 text-right">Total Cost</th>
                  <th className="py-3 px-4 text-right">Savings</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-gray-700">
                {recentPlans.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50/50">
                    <td className="py-3 px-4 font-mono font-bold text-gray-900">
                      <Link to={`/ops/routes/${p.id}`} className="text-emerald-700 hover:underline">
                        #{p.id.slice(0, 8)}
                      </Link>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          p.status === 'APPROVED'
                            ? 'bg-emerald-100 text-emerald-800'
                            : p.status === 'DISCARDED'
                            ? 'bg-gray-100 text-gray-600'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {p.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-gray-600">{p.method}</td>
                    <td className="py-3 px-4 text-right">{p.orders_count}</td>
                    <td className="py-3 px-4 text-right">{p.vehicles_used}</td>
                    <td className="py-3 px-4 text-right font-bold text-gray-900">
                      ₹{p.optimized_cost.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-emerald-700">
                      {p.savings_pct.toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/ops/routes/${p.id}`}
                        className="px-2.5 py-1 bg-gray-100 hover:bg-gray-200 text-gray-800 font-semibold rounded text-[11px]"
                      >
                        View Plan →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Fleet Inventory Table */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-gray-900">Fleet Vehicles Inventory</h2>
            <p className="text-xs text-gray-500">
              Active transport vehicles available for multi-stop consolidation and dedicated freight.
            </p>
          </div>
          <span className="text-xs font-semibold px-2 py-1 bg-gray-100 text-gray-700 rounded-md">
            {vehicles.length} Vehicles Registered
          </span>
        </div>

        {loading ? (
          <div className="p-8 text-center space-y-2">
            <span className="animate-spin inline-block w-6 h-6 border-2 border-emerald-600 border-t-transparent rounded-full" />
            <p className="text-xs text-gray-500">Loading fleet inventory...</p>
          </div>
        ) : vehicles.length === 0 ? (
          <div className="p-8 text-center text-xs text-gray-500">
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

      {/* VRP Formulation Note */}
      <div className="bg-blue-50/60 border border-blue-200 rounded-xl p-4 text-xs text-blue-900 space-y-1.5">
        <div className="flex items-center gap-1.5 font-bold">
          <span>ℹ️</span>
          <span>Multi-Stop Vehicle Routing Problem Formulation (ML.md §11)</span>
        </div>
        <p className="text-[11px] text-blue-800 leading-relaxed">
          Google OR-Tools solves multi-vehicle Capacitated Pickup and Delivery (CVRP-PD) with depot returns, precedence constraints, and capacity limits. If OR-Tools exceeds the time limit or encounters infeasibility, greedy heuristic fallback ensures high-quality dispatch plans. Baseline costs are modeled using dedicated point-to-point round trips for each order.
        </p>
      </div>
    </div>
  );
};
