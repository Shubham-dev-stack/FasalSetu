import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import { fetchRequirementsApi, updateRequirementApi } from '../../api/requirements';
import { Requirement, RequirementUpdateRequest } from '../../api/types';
import { RequirementCard } from '../../components/domain/RequirementCard';
import { EditRequirementModal } from '../../components/domain/EditRequirementModal';
import { Plus, ShoppingCart, RefreshCw, AlertCircle } from 'lucide-react';

const STATUS_TABS = [
  { key: 'ALL', label: 'All Demands' },
  { key: 'OPEN', label: 'Open' },
  { key: 'PARTIALLY_FULFILLED', label: 'Partially Fulfilled' },
  { key: 'FULFILLED', label: 'Fulfilled' },
  { key: 'EXPIRED', label: 'Expired' },
  { key: 'CANCELLED', label: 'Cancelled' },
];

export const RequirementsPage: React.FC = () => {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('ALL');

  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [editingRequirement, setEditingRequirement] = useState<Requirement | null>(null);

  const loadRequirements = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchRequirementsApi({
        token,
        status: activeTab === 'ALL' ? undefined : activeTab,
      });
      setRequirements(res.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch requirements');
    } finally {
      setLoading(false);
    }
  }, [token, activeTab]);

  useEffect(() => {
    loadRequirements();
  }, [loadRequirements]);

  const handleUpdateRequirement = async (id: number, data: RequirementUpdateRequest) => {
    if (!token) return;
    await updateRequirementApi(token, id, data);
    await loadRequirements();
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-surface rounded-xl border border-gray-200 p-6 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-ink">My Procurement Requirements</h1>
            <span className="text-xs bg-primary-soft text-primary font-semibold px-2 py-0.5 rounded-full">
              Buyer Portal
            </span>
          </div>
          <p className="text-sm text-muted mt-1">
            Manage your commodity demand, budget constraints, and track fulfillment across regional hubs.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => loadRequirements()}
            disabled={loading}
            className="p-2 border border-gray-200 rounded-lg text-muted hover:text-ink hover:bg-gray-50 transition-colors"
            title="Refresh requirements"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <Link
            to="/buyer/requirements/new"
            className="inline-flex items-center space-x-2 bg-primary hover:bg-primary-hover text-white text-sm font-semibold px-4 py-2.5 rounded-lg shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Post Requirement</span>
          </Link>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-1 border-b border-gray-200 overflow-x-auto pb-px">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap transition-colors border-b-2 ${
              activeTab === tab.key
                ? 'border-primary text-primary'
                : 'border-transparent text-muted hover:text-ink hover:border-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-800 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Unable to load requirements</p>
            <p className="text-xs mt-0.5 text-rose-700">{error}</p>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="bg-surface rounded-xl border border-gray-200 p-5 h-64 animate-pulse flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="h-5 bg-gray-200 rounded w-2/3" />
                <div className="h-4 bg-gray-100 rounded w-1/2" />
              </div>
              <div className="h-20 bg-gray-100 rounded" />
              <div className="h-8 bg-gray-200 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && requirements.length === 0 && (
        <div className="bg-surface rounded-xl border border-dashed border-gray-300 p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-primary-soft text-primary mx-auto flex items-center justify-center">
            <ShoppingCart className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-ink">No procurement requirements found</h3>
            <p className="text-xs text-muted max-w-sm mx-auto mt-1">
              {activeTab === 'ALL'
                ? "You haven't posted any procurement demands yet. Post a demand to trigger aggregator discovery and logistics coordination."
                : `No requirements matching status "${activeTab}".`}
            </p>
          </div>
          <div>
            <Link
              to="/buyer/requirements/new"
              className="inline-flex items-center space-x-1.5 bg-primary text-white text-xs font-semibold px-4 py-2 rounded-lg hover:bg-primary-hover transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Post First Demand</span>
            </Link>
          </div>
        </div>
      )}

      {/* Requirements Grid */}
      {!loading && !error && requirements.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {requirements.map((req) => (
            <RequirementCard
              key={req.id}
              requirement={req}
              onEdit={(r) => setEditingRequirement(r)}
            />
          ))}
        </div>
      )}

      {/* Edit Requirement Modal */}
      {editingRequirement && (
        <EditRequirementModal
          requirement={editingRequirement}
          isOpen={!!editingRequirement}
          onClose={() => setEditingRequirement(null)}
          onSave={handleUpdateRequirement}
        />
      )}
    </div>
  );
};
