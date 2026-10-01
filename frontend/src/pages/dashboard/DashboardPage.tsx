import React, { useEffect, useState } from 'react';
import { useAuth } from '../../lib/auth';
import { fetchHealth, fetchReferenceDataApi, HealthResponse } from '../../api/client';
import { ReferenceDataResponse } from '../../api/types';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [reference, setReference] = useState<ReferenceDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [healthRes, refRes] = await Promise.all([
          fetchHealth(),
          fetchReferenceDataApi(),
        ]);
        setHealth(healthRes);
        setReference(refRes);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load system data');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Welcome Card */}
      <div className="bg-surface rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-bold text-ink">Welcome, {user?.name}</h2>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-primary-soft text-primary uppercase">
                {user?.role}
              </span>
            </div>
            <p className="text-xs text-muted mt-1">
              User ID: <code className="text-ink font-mono">{user?.id}</code> · Email: {user?.email}
            </p>
          </div>
          {user?.profile && (
            <div className="text-left sm:text-right text-xs text-muted">
              <div>Location: <strong className="text-ink">{user.profile.district}, {user.profile.state}</strong></div>
              <div>PIN: <strong className="text-ink">{user.profile.pincode}</strong> (Lat: {user.profile.lat.toFixed(4)}, Lon: {user.profile.lon.toFixed(4)})</div>
            </div>
          )}
        </div>
      </div>

      {/* System Status & Diagnostics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
          <span className="text-xs text-muted block uppercase font-semibold">Backend API</span>
          <div className="mt-2 flex items-center space-x-2">
            <span className={`w-2.5 h-2.5 rounded-full ${health?.status === 'ok' ? 'bg-success' : 'bg-danger'}`} />
            <span className="text-lg font-bold text-ink capitalize">{health?.status || 'Unknown'}</span>
          </div>
          <span className="text-xs text-muted mt-1 block">FasalSetu API v{health?.version || '0.1.0'}</span>
        </div>

        <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
          <span className="text-xs text-muted block uppercase font-semibold">Database Engine</span>
          <div className="mt-2 flex items-center space-x-2">
            <span className={`w-2.5 h-2.5 rounded-full ${health?.db === 'connected' ? 'bg-success' : 'bg-danger'}`} />
            <span className="text-lg font-bold text-ink uppercase">{health?.db || 'Unknown'}</span>
          </div>
          <span className="text-xs text-muted mt-1 block">SQLite with WAL mode & Foreign Keys</span>
        </div>

        <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
          <span className="text-xs text-muted block uppercase font-semibold">Current Phase</span>
          <div className="mt-2 flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-primary" />
            <span className="text-lg font-bold text-ink">Phase 1 Complete</span>
          </div>
          <span className="text-xs text-muted mt-1 block">Foundation + Auth + Schema + Logistics Utils</span>
        </div>
      </div>

      {loading && (
        <div className="p-8 text-center text-sm text-muted">
          <span className="animate-spin inline-block w-5 h-5 border-2 border-primary border-t-transparent rounded-full mr-2" />
          Loading reference data...
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-danger text-sm">
          <span className="font-semibold block">Failed to load platform data</span>
          <span>{error}</span>
        </div>
      )}

      {/* Reference Data Overview */}
      {reference && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Crops */}
          <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="text-sm font-bold text-ink mb-3 flex items-center justify-between">
              <span>Seeded Crops</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-muted">
                {reference.crops.length} items
              </span>
            </h3>
            <div className="space-y-2.5">
              {reference.crops.map((c) => (
                <div key={c.code} className="p-2.5 rounded-lg bg-bg border border-gray-100 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-ink block">{c.name}</span>
                    <span className="text-muted">Shelf life: {c.shelf_life_days}d · {c.perishability_class}</span>
                  </div>
                  <span className="font-mono font-medium text-ink bg-surface px-1.5 py-0.5 rounded border border-gray-200">
                    {c.code}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Hubs */}
          <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="text-sm font-bold text-ink mb-3 flex items-center justify-between">
              <span>Seeded Regional Hubs</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-muted">
                {reference.hubs.length} hubs
              </span>
            </h3>
            <div className="space-y-2.5">
              {reference.hubs.map((h) => (
                <div key={h.code} className="p-2.5 rounded-lg bg-bg border border-gray-100 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-ink block">{h.name}</span>
                    <span className="text-muted">{h.district}, {h.state} ({h.capacity_mt} MT)</span>
                  </div>
                  <span className="text-[10px] uppercase font-bold text-primary bg-primary-soft px-1.5 py-0.5 rounded">
                    {h.type === 'COLLECTION_CENTER' ? 'CC' : h.type === 'DISTRIBUTION_HUB' ? 'DH' : 'CM'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Vehicles */}
          <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="text-sm font-bold text-ink mb-3 flex items-center justify-between">
              <span>Seeded Fleet Types</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-muted">
                {reference.vehicles.length} types
              </span>
            </h3>
            <div className="space-y-2.5">
              {reference.vehicles.map((v) => (
                <div key={v.code} className="p-2.5 rounded-lg bg-bg border border-gray-100 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-ink block">{v.name}</span>
                    <span className="text-muted">Payload: {(v.capacity_payload_kg / 1000).toFixed(1)} MT · ₹{v.cost_per_km_loaded}/km loaded</span>
                  </div>
                  <span className="text-[10px] font-mono text-muted bg-surface px-1.5 py-0.5 rounded border border-gray-200">
                    {v.code}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
