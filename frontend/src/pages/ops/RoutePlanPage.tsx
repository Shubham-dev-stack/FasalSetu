import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  fetchRoutePlanDetailApi,
  approveRoutePlanApi,
  discardRoutePlanApi,
  transitionShipmentApi,
} from '../../api/routes';
import { RoutePlanResponse, ShipmentDetailResponse } from '../../api/types';

export const RoutePlanPage: React.FC = () => {
  const { planId } = useParams<{ planId: string }>();
  const navigate = useNavigate();

  const [plan, setPlan] = useState<RoutePlanResponse | null>(null);
  const [shipmentsDetail, setShipmentsDetail] = useState<Record<number, ShipmentDetailResponse>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const loadPlan = async () => {
    if (!planId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRoutePlanDetailApi(planId);
      setPlan(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load route plan details.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlan();
  }, [planId]);

  const handleApprove = async () => {
    if (!planId) return;
    setActionLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await approveRoutePlanApi(planId);
      setPlan(res.plan);
      const detailMap: Record<number, ShipmentDetailResponse> = {};
      for (const s of res.shipments) {
        detailMap[s.id] = s;
      }
      setShipmentsDetail(detailMap);
      setSuccessMsg('Route plan approved successfully. Shipments created and transport costs allocated.');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to approve route plan.');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleDiscard = async () => {
    if (!planId) return;
    setActionLoading(true);
    setError(null);
    try {
      const res = await discardRoutePlanApi(planId);
      setPlan(res);
      setSuccessMsg('Route plan discarded.');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to discard route plan.');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleTransitionShipment = async (shipmentId: number, toStatus: 'DISPATCHED' | 'DELIVERED') => {
    setActionLoading(true);
    setError(null);
    try {
      const updated = await transitionShipmentApi(shipmentId, toStatus);
      setShipmentsDetail((prev) => ({ ...prev, [shipmentId]: updated }));
      setSuccessMsg(`Shipment #${shipmentId} updated to ${toStatus}.`);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(`Failed to update shipment status to ${toStatus}.`);
      }
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center space-y-3">
        <span className="animate-spin inline-block w-8 h-8 border-3 border-emerald-600 border-t-transparent rounded-full" />
        <p className="text-sm text-gray-500">Loading route optimization plan...</p>
      </div>
    );
  }

  if (error && !plan) {
    return (
      <div className="max-w-3xl mx-auto p-6 bg-white rounded-xl border border-rose-200 text-center space-y-4">
        <div className="text-rose-600 font-bold text-lg">Unable to Load Plan</div>
        <p className="text-sm text-gray-600">{error}</p>
        <button
          onClick={() => navigate('/ops/logistics')}
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs font-semibold rounded-lg"
        >
          Back to Logistics
        </button>
      </div>
    );
  }

  if (!plan) return null;

  const t = plan.totals;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Link to="/ops/logistics" className="text-xs text-emerald-700 hover:underline">
              ← Logistics Operations
            </Link>
            <span className="text-gray-300">/</span>
            <span className="text-xs text-gray-500 font-mono">Plan #{plan.plan_id.slice(0, 8)}</span>
          </div>
          <div className="flex items-center gap-3 mt-1">
            <h1 className="text-2xl font-black text-gray-900">Route Optimization Plan</h1>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                plan.status === 'APPROVED'
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                  : plan.status === 'DISCARDED'
                  ? 'bg-gray-100 text-gray-600 border border-gray-300'
                  : 'bg-amber-100 text-amber-800 border border-amber-300'
              }`}
            >
              {plan.status}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            Method: <strong className="text-gray-700">{plan.method}</strong> • Distance Source:{' '}
            <strong className="text-gray-700">{plan.distance_source}</strong> • Solve Time:{' '}
            <span className="font-mono">{plan.solve_time_ms}ms</span>
          </p>
        </div>

        {plan.status === 'PROPOSED' && (
          <div className="flex items-center gap-3">
            <button
              onClick={handleDiscard}
              disabled={actionLoading}
              className="px-4 py-2 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 text-xs font-semibold rounded-lg shadow-sm"
            >
              Discard Plan
            </button>
            <button
              onClick={handleApprove}
              disabled={actionLoading}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-sm flex items-center gap-2"
            >
              {actionLoading ? (
                <>
                  <span className="animate-spin inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full" />
                  <span>Approving...</span>
                </>
              ) : (
                <>
                  <span>✓</span>
                  <span>Approve & Create Shipments</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 font-medium flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-500 font-bold hover:text-rose-800">
            ✕
          </button>
        </div>
      )}
      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 font-medium flex items-center justify-between">
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-600 font-bold hover:text-emerald-900">
            ✕
          </button>
        </div>
      )}

      {/* KPI Comparison Row (AC-RTE-04) */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Optimized Cost</div>
          <div className="text-xl font-bold text-gray-900 mt-1">₹{t.optimized_cost.toLocaleString()}</div>
          <div className="text-[11px] text-gray-500 mt-0.5">{t.optimized_km.toFixed(1)} km total</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Baseline Cost</div>
          <div className="text-xl font-bold text-gray-500 mt-1">₹{t.baseline_cost.toLocaleString()}</div>
          <div className="text-[11px] text-gray-400 mt-0.5">{t.baseline_km.toFixed(1)} km dedicated trips</div>
        </div>

        <div className="bg-emerald-50/70 p-4 rounded-xl border border-emerald-200 shadow-sm">
          <div className="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider">Cost Savings</div>
          <div className="text-xl font-bold text-emerald-700 mt-1">
            ₹{t.savings_cost.toLocaleString()}{' '}
            <span className="text-xs font-semibold">({t.savings_pct_cost.toFixed(1)}%)</span>
          </div>
          <div className="text-[11px] text-emerald-600 mt-0.5">{t.savings_km.toFixed(1)} km saved</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          <div className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Vehicles Used</div>
          <div className="text-xl font-bold text-gray-900 mt-1">{t.vehicles_used}</div>
          <div className="text-[11px] text-gray-500 mt-0.5">{plan.shipments.length} vehicle routes</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm col-span-2 lg:col-span-1">
          <div className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Avg Capacity Util.</div>
          <div className="text-xl font-bold text-gray-900 mt-1">{t.avg_utilization_pct.toFixed(1)}%</div>
          <div className="text-[11px] text-gray-500 mt-0.5">Peak load weight</div>
        </div>
      </div>

      {/* Baseline explanation card */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-3 text-xs text-gray-600 flex items-start gap-2">
        <span className="text-base">ℹ️</span>
        <div className="text-[11px] leading-relaxed">
          <strong>Baseline Comparison: </strong> {plan.baseline_note}
        </div>
      </div>

      {/* Vehicle Routes & Stops */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">Consolidated Vehicle Routes ({plan.shipments.length})</h2>
          <span className="text-xs text-gray-500">
            Capacity-constrained multi-stop pickup & drop sequences
          </span>
        </div>

        <div className="space-y-4">
          {plan.shipments.map((shp, idx) => {
            const actualShpId = shp.shipment_id;
            const liveShp = actualShpId ? shipmentsDetail[actualShpId] : null;
            const currentStatus = liveShp ? liveShp.status : plan.status === 'APPROVED' ? 'PLANNED' : 'PROPOSED';

            return (
              <div key={shp.temp_id || idx} className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                {/* Vehicle Header Bar */}
                <div className="p-4 bg-gray-50/70 border-b border-gray-200 flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-xs">
                      #{idx + 1}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-gray-900">{shp.vehicle.name}</h3>
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-200 text-gray-700">
                          {shp.vehicle.vehicle_type}
                        </span>
                        {actualShpId && (
                          <span className="text-xs font-mono font-semibold text-emerald-700">
                            Shipment #{actualShpId}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-gray-500">
                        Capacity: {shp.vehicle.capacity_kg} kg • Peak Load:{' '}
                        <strong>{shp.peak_load_kg.toFixed(0)} kg</strong> ({shp.utilization_pct.toFixed(1)}% util)
                      </p>
                    </div>
                  </div>

                  {/* Route metrics & manual transition buttons */}
                  <div className="flex items-center gap-4">
                    <div className="text-right text-xs">
                      <div className="font-bold text-gray-900">₹{shp.total_cost.toLocaleString()}</div>
                      <div className="text-[11px] text-gray-500">
                        {shp.total_distance_km.toFixed(1)} km • ~{shp.est_duration_min} min
                      </div>
                    </div>

                    {actualShpId && plan.status === 'APPROVED' && (
                      <div className="flex items-center gap-2 pl-2 border-l border-gray-200">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">
                          {currentStatus}
                        </span>

                        {currentStatus === 'PLANNED' && (
                          <button
                            onClick={() => handleTransitionShipment(actualShpId, 'DISPATCHED')}
                            disabled={actionLoading}
                            className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-semibold rounded-md shadow-sm"
                          >
                            Dispatch
                          </button>
                        )}
                        {currentStatus === 'DISPATCHED' && (
                          <button
                            onClick={() => handleTransitionShipment(actualShpId, 'DELIVERED')}
                            disabled={actionLoading}
                            className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-semibold rounded-md shadow-sm"
                          >
                            Mark Delivered
                          </button>
                        )}
                        {currentStatus === 'DELIVERED' && (
                          <span className="text-[11px] font-bold text-emerald-700">✓ Completed</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Stops Timeline Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-gray-50/40 border-b border-gray-100 text-gray-400 font-semibold uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="py-2.5 px-4 w-12 text-center">#</th>
                        <th className="py-2.5 px-4 w-28">Type</th>
                        <th className="py-2.5 px-4">Location / Node</th>
                        <th className="py-2.5 px-4 text-right">Cum. Dist</th>
                        <th className="py-2.5 px-4 text-right">Load After</th>
                        <th className="py-2.5 px-4 text-right">ETA</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 text-gray-700">
                      {shp.stops.map((st) => (
                        <tr key={st.sequence} className="hover:bg-gray-50/50">
                          <td className="py-2.5 px-4 text-center font-mono text-[11px] text-gray-400">
                            {st.sequence}
                          </td>
                          <td className="py-2.5 px-4">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                st.stop_type === 'PICKUP'
                                  ? 'bg-amber-100 text-amber-800'
                                  : st.stop_type === 'DROP'
                                  ? 'bg-blue-100 text-blue-800'
                                  : 'bg-gray-100 text-gray-600'
                              }`}
                            >
                              {st.stop_type}
                            </span>
                          </td>
                          <td className="py-2.5 px-4">
                            <div className="font-medium text-gray-900">{st.label}</div>
                            {st.order_id && (
                              <span className="text-[10px] text-emerald-700 font-semibold">
                                Order #{st.order_id}
                              </span>
                            )}
                          </td>
                          <td className="py-2.5 px-4 text-right font-mono text-gray-600">
                            {st.cum_distance_km.toFixed(1)} km
                          </td>
                          <td className="py-2.5 px-4 text-right font-mono text-gray-900 font-semibold">
                            {st.load_after_kg.toFixed(0)} kg
                          </td>
                          <td className="py-2.5 px-4 text-right text-gray-500 font-mono text-[11px]">
                            +{st.eta_min_from_start}m
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Unassigned Orders Card (if any) */}
      {plan.unassigned && plan.unassigned.length > 0 && (
        <div className="bg-amber-50/70 border border-amber-200 rounded-2xl p-5 space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-base">⚠️</span>
            <h3 className="text-sm font-bold text-amber-900">
              Unassigned Orders ({plan.unassigned.length})
            </h3>
          </div>
          <p className="text-xs text-amber-800">
            The following orders could not be consolidated within vehicle capacity or time limits and remain in the pool:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {plan.unassigned.map((u) => (
              <div
                key={u.order_id}
                className="bg-white p-3 rounded-lg border border-amber-200 text-xs flex items-center justify-between"
              >
                <div>
                  <strong className="text-gray-900">Order #{u.order_id}</strong>
                  <span className="text-gray-500 text-[11px] block">{u.quantity_kg} kg</span>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-rose-100 text-rose-800">
                  {u.reason}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
