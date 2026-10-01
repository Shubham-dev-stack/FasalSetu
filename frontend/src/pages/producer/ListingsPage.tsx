import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import { fetchListingsApi, updateListingApi } from '../../api/listings';
import { Listing, ListingUpdateRequest } from '../../api/types';
import { ListingCard } from '../../components/domain/ListingCard';
import { EditListingModal } from '../../components/domain/EditListingModal';
import { Plus, Package, RefreshCw, AlertCircle } from 'lucide-react';

const STATUS_TABS = [
  { key: 'ALL', label: 'All Lots' },
  { key: 'ACTIVE', label: 'Active' },
  { key: 'SOLD_OUT', label: 'Sold Out' },
  { key: 'EXPIRED', label: 'Expired' },
  { key: 'WITHDRAWN', label: 'Withdrawn' },
];

export const ListingsPage: React.FC = () => {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('ALL');

  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [editingListing, setEditingListing] = useState<Listing | null>(null);

  const loadListings = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchListingsApi({
        mine: true,
        status: activeTab === 'ALL' ? undefined : activeTab,
        token,
      });
      setListings(res.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch produce listings');
    } finally {
      setLoading(false);
    }
  }, [token, activeTab]);

  useEffect(() => {
    loadListings();
  }, [loadListings]);

  const handleUpdateListing = async (id: number, data: ListingUpdateRequest) => {
    if (!token) return;
    await updateListingApi(token, id, data);
    await loadListings();
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-surface rounded-xl border border-gray-200 p-6 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-ink">My Produce Listings</h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-primary-soft text-primary font-bold">
              {listings.length} Lots
            </span>
          </div>
          <p className="text-xs text-muted mt-1">
            Manage your harvest inventory, monitor active lot allocations, and edit ask prices.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={loadListings}
            disabled={loading}
            className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-muted transition-colors"
            title="Refresh listings"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <Link
            to="/producer/listings/new"
            className="inline-flex items-center space-x-1.5 bg-primary hover:bg-primary-hover text-white text-xs font-bold px-4 py-2.5 rounded-lg shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Publish New Lot</span>
          </Link>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 border-b border-gray-200 overflow-x-auto pb-1 text-xs">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-3 py-1.5 font-semibold rounded-lg transition-colors whitespace-nowrap ${
              activeTab === tab.key
                ? 'bg-primary text-white shadow-xs'
                : 'text-muted hover:text-ink hover:bg-gray-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="bg-surface rounded-xl border border-gray-200 p-5 shadow-xs animate-pulse space-y-4"
            >
              <div className="flex justify-between items-center">
                <div className="h-5 bg-gray-200 rounded w-1/3" />
                <div className="h-4 bg-gray-200 rounded w-16" />
              </div>
              <div className="h-20 bg-gray-100 rounded-lg" />
              <div className="h-4 bg-gray-200 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-rose-500 mx-auto" />
          <h3 className="font-bold text-sm text-rose-800">Unable to load produce listings</h3>
          <p className="text-xs text-rose-700">{error}</p>
          <button
            onClick={loadListings}
            className="px-4 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      ) : listings.length === 0 ? (
        <div className="bg-surface rounded-xl border border-gray-200 p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-primary-soft text-primary flex items-center justify-center mx-auto">
            <Package className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-ink">No produce lots found</h3>
            <p className="text-xs text-muted max-w-sm mx-auto mt-1">
              {activeTab === 'ALL'
                ? "You haven't published any crop lots yet. Create your first lot to connect with direct buyers."
                : `No produce lots currently match status "${activeTab}".`}
            </p>
          </div>
          <Link
            to="/producer/listings/new"
            className="inline-flex items-center space-x-1.5 bg-primary hover:bg-primary-hover text-white text-xs font-bold px-4 py-2 rounded-lg shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Publish First Lot</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {listings.map((item) => (
            <ListingCard
              key={item.id}
              listing={item}
              onEdit={(lot) => setEditingListing(lot)}
            />
          ))}
        </div>
      )}

      {/* Edit Modal */}
      {editingListing && (
        <EditListingModal
          listing={editingListing}
          isOpen={true}
          onClose={() => setEditingListing(null)}
          onSave={handleUpdateListing}
        />
      )}
    </div>
  );
};
