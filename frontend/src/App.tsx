import { useEffect, useState } from 'react';
import { fetchHealth, HealthResponse } from './api/client';

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isDemo = import.meta.env.VITE_DEMO_MODE === 'true';

  useEffect(() => {
    fetchHealth()
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-bg p-4 md:p-8 flex flex-col items-center justify-center">
      <div className="max-w-xl w-full bg-surface rounded-xl shadow-sm border border-gray-200 p-6 md:p-8 space-y-6">
        <div className="flex items-center justify-between border-b pb-4">
          <div>
            <h1 className="text-2xl font-bold text-primary tracking-tight">KrishiSetu</h1>
            <p className="text-xs text-muted">AI-Assisted Agricultural Supply-Chain Platform</p>
          </div>
          {isDemo && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-accent text-ink">
              DEMO DATA
            </span>
          )}
        </div>

        <div className="space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
            Phase 0 — System Skeleton & Health
          </h2>

          {loading && (
            <div className="flex items-center space-x-2 text-muted text-sm py-4">
              <span className="animate-spin inline-block w-4 h-4 border-2 border-primary border-t-transparent rounded-full" />
              <span>Checking backend connection...</span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-danger text-sm">
              <p className="font-semibold">Backend Unreachable</p>
              <p className="text-xs mt-1 text-red-600">{error}</p>
            </div>
          )}

          {health && (
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="p-3 bg-bg rounded-lg border border-gray-100">
                <span className="text-xs text-muted block">API Status</span>
                <span className="font-medium text-success capitalize">{health.status}</span>
              </div>
              <div className="p-3 bg-bg rounded-lg border border-gray-100">
                <span className="text-xs text-muted block">Database</span>
                <span className="font-medium text-success uppercase">{health.db}</span>
              </div>
              <div className="p-3 bg-bg rounded-lg border border-gray-100">
                <span className="text-xs text-muted block">ML Model</span>
                <span className="font-medium text-ink">
                  {health.model.loaded ? 'Loaded' : 'Not Loaded (Phase 0)'}
                </span>
              </div>
              <div className="p-3 bg-bg rounded-lg border border-gray-100">
                <span className="text-xs text-muted block">App Version</span>
                <span className="font-medium text-ink">v{health.version}</span>
              </div>
            </div>
          )}
        </div>

        <div className="text-xs text-muted border-t pt-4 flex justify-between items-center">
          <span>Loop: PREDICT → MATCH → MOVE → SELL → ANALYSE</span>
          <span className="text-success font-medium">Phase 0 Ready</span>
        </div>
      </div>
    </div>
  );
}
