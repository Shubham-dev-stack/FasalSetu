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
              <h2 className="text-xl font-bold text-ink">Welcome, {user?.display_name || user?.name || user?.email}</h2>
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
              <div>PIN: <strong className="text-ink">{user.profile.pincode}</strong> {user.profile.lat ? `(Lat: ${user.profile.lat.toFixed(4)}, Lon: ${user.profile.lon?.toFixed(4)})` : ''}</div>
            </div>
          )}
        </div>

        {/* Quick Role Navigation */}
        <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-2">
          {(user?.role?.toUpperCase() === 'PRODUCER' || user?.role === 'fpo' || user?.role === 'farmer') && (
            <>
              <a href="/producer/listings" className="px-3 py-1.5 bg-primary text-white text-xs font-semibold rounded-lg hover:bg-green-800 transition-colors">
                📦 My Produce Listings →
              </a>
              <a href="/producer/listings/new" className="px-3 py-1.5 bg-primary-soft text-primary text-xs font-semibold rounded-lg hover:bg-green-100 transition-colors">
                + Publish New Lot
              </a>
              <a href="/forecast" className="px-3 py-1.5 bg-gray-100 text-ink text-xs font-medium rounded-lg hover:bg-gray-200 transition-colors">
                📈 Demand Forecasts
              </a>
            </>
          )}

          {(user?.role?.toUpperCase() === 'BUYER' || user?.role?.startsWith('buyer_')) && (
            <>
              <a href="/buyer/requirements" className="px-3 py-1.5 bg-primary text-white text-xs font-semibold rounded-lg hover:bg-green-800 transition-colors">
                📋 My Demands / Requirements →
              </a>
              <a href="/buyer/requirements/new" className="px-3 py-1.5 bg-primary-soft text-primary text-xs font-semibold rounded-lg hover:bg-green-100 transition-colors">
                + Post Demand
              </a>
              <a href="/market" className="px-3 py-1.5 bg-gray-100 text-ink text-xs font-medium rounded-lg hover:bg-gray-200 transition-colors">
                🛒 Marketplace
              </a>
            </>
          )}

          {(user?.role?.toUpperCase() === 'ADMIN' || user?.role === 'operator') && (
            <>
              <a href="/ops/logistics" className="px-3 py-1.5 bg-primary text-white text-xs font-semibold rounded-lg hover:bg-green-800 transition-colors">
                🚚 Logistics & Route Optimizer →
              </a>
              <a href="/orders" className="px-3 py-1.5 bg-primary-soft text-primary text-xs font-semibold rounded-lg hover:bg-green-100 transition-colors">
                📑 Orders Management
              </a>
              <a href="/analytics" className="px-3 py-1.5 bg-gray-100 text-ink text-xs font-medium rounded-lg hover:bg-gray-200 transition-colors">
                📊 Impact Analytics
              </a>
            </>
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
            <span className={`w-2.5 h-2.5 rounded-full ${health?.db === 'ok' ? 'bg-success' : 'bg-danger'}`} />
            <span className="text-lg font-bold text-ink uppercase">{health?.db || 'Unknown'}</span>
          </div>
          <span className="text-xs text-muted mt-1 block">SQLite with WAL mode & Foreign Keys</span>
        </div>

        <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
          <span className="text-xs text-muted block uppercase font-semibold">Forecasting Engine</span>
          <div className="mt-2 flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-primary" />
            <span className="text-lg font-bold text-ink">{health?.model?.deployed_method || 'LightGBM'}</span>
          </div>
          <span className="text-xs text-muted mt-1 block">Causal features & LightGBM Model</span>
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
                {reference.crops?.length ?? 0} items
              </span>
            </h3>
            <div className="space-y-2.5">
              {reference.crops?.map((c) => (
                <div key={c.id} className="p-2.5 rounded-lg bg-bg border border-gray-100 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-ink block">{c.name}</span>
                    <span className="text-muted">Shelf life: {c.shelf_life_days}d · {c.perishability}</span>
                  </div>
                  <span className="font-mono font-medium text-ink bg-surface px-1.5 py-0.5 rounded border border-gray-200">
                    #{c.id}
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
                {reference.hubs?.length ?? 0} hubs
              </span>
            </h3>
            <div className="space-y-2.5">
              {reference.hubs?.map((h) => (
                <div key={h.id} className="p-2.5 rounded-lg bg-bg border border-gray-100 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-ink block">{h.name}</span>
                    <span className="text-muted">{h.city}, {h.state}</span>
                  </div>
                  <span className="text-[10px] uppercase font-bold text-primary bg-primary-soft px-1.5 py-0.5 rounded">
                    Hub #{h.id}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Vehicles / Enums */}
          <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="text-sm font-bold text-ink mb-3 flex items-center justify-between">
              <span>Fleet Vehicle Types</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-muted">
                {(reference.enums?.vehicle_type ?? reference.vehicles ?? ['MINI_TRUCK', 'PICKUP_TRUCK', 'MEDIUM_TRUCK']).length} types
              </span>
            </h3>
            <div className="space-y-2.5">
              {(reference.enums?.vehicle_type ?? ['MINI_TRUCK', 'PICKUP_TRUCK', 'MEDIUM_TRUCK']).map((v) => (
                <div key={v} className="p-2.5 rounded-lg bg-bg border border-gray-100 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-ink block">
                      {v.replace('_', ' ')}
                    </span>
                    <span className="text-muted">
                      Seeded routing vehicle
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-muted bg-surface px-1.5 py-0.5 rounded border border-gray-200">
                    ACTIVE
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
