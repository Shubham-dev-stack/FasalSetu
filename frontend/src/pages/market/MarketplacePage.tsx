import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import { fetchListingsApi } from '../../api/listings';
import { Listing, Order } from '../../api/types';
import { ListingStatusChip } from '../../components/domain/ListingStatusChip';
import { OrderModal } from '../../components/orders/OrderModal';

export const MarketplacePage: React.FC = () => {
  const { token, user } = useAuth();
  const navigate = useNavigate();

  const [listings, setListings] = useState<Listing[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [cropId, setCropId] = useState<number | undefined>(undefined);
  const [gradeMin, setGradeMin] = useState<string>('');
  const [stateFilter, setStateFilter] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<number | undefined>(undefined);
  const [sort, setSort] = useState<string>('landed');

  // Order modal state
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);

  const loadListings = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchListingsApi({
        crop_id: cropId,
        grade_min: gradeMin || undefined,
        state: stateFilter || undefined,
        max_price: maxPrice,
        sort: sort,
        token: token,
      });
      setListings(data.items);
      setTotal(data.total);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load marketplace listings.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadListings();
  }, [cropId, gradeMin, stateFilter, maxPrice, sort, token]);

  const clearFilters = () => {
    setCropId(undefined);
    setGradeMin('');
    setStateFilter('');
    setMaxPrice(undefined);
    setSort('landed');
  };

  const handleOrderSuccess = (order: Order) => {
    setSelectedListing(null);
    navigate(`/orders/${order.id}`);
  };

  const roleUpper = user?.role?.toUpperCase();
  const isBuyer = roleUpper === 'BUYER' || user?.role?.startsWith('buyer_');

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-gray-900">Unified Marketplace</h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              Live Supply
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Browse verified farmgate produce lots with indicative landed price estimates.
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-gray-400 font-medium uppercase tracking-wider block">
            Active Lots Available
          </span>
          <span className="text-2xl font-bold text-gray-900">{total}</span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-wrap items-center gap-3 text-sm">
        {/* Crop Select */}
        <div>
          <select
            value={cropId || ''}
            onChange={(e) => setCropId(e.target.value ? Number(e.target.value) : undefined)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-medium text-gray-700 bg-white focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Crops</option>
            <option value="1">Tomato</option>
            <option value="2">Onion</option>
            <option value="3">Potato</option>
            <option value="4">Cauliflower</option>
            <option value="5">Green Chilli</option>
          </select>
        </div>

        {/* Grade Select */}
        <div>
          <select
            value={gradeMin}
            onChange={(e) => setGradeMin(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-medium text-gray-700 bg-white focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Grades</option>
            <option value="A">Grade A</option>
            <option value="B">Grade B & Higher</option>
            <option value="C">Grade C & Higher</option>
          </select>
        </div>

        {/* State Filter */}
        <div>
          <input
            type="text"
            placeholder="Filter by state (e.g. Haryana)"
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary w-44"
          />
        </div>

        {/* Max Price Filter */}
        <div>
          <input
            type="number"
            placeholder="Max price ₹/kg"
            value={maxPrice || ''}
            onChange={(e) => setMaxPrice(e.target.value ? Number(e.target.value) : undefined)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary w-32"
          />
        </div>

        {/* Sort Select */}
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-gray-500">Sort by:</span>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-medium text-gray-700 bg-white focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="landed">Landed Price (Lowest)</option>
            <option value="price">Farmgate Price (Lowest)</option>
            <option value="distance">Distance (Nearest)</option>
            <option value="freshness">Freshness (Newest)</option>
          </select>
        </div>

        {(cropId || gradeMin || stateFilter || maxPrice) && (
          <button
            onClick={clearFilters}
            className="text-xs text-rose-600 hover:text-rose-700 font-medium px-2 py-1 rounded hover:bg-rose-50 transition-colors"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="bg-white rounded-2xl border border-gray-200 p-5 space-y-4 animate-pulse"
            >
              <div className="h-4 bg-gray-200 rounded w-1/3"></div>
              <div className="h-6 bg-gray-200 rounded w-2/3"></div>
              <div className="h-16 bg-gray-100 rounded"></div>
              <div className="h-10 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center space-y-3">
          <p className="text-sm font-medium text-rose-800">{error}</p>
          <button
            onClick={loadListings}
            className="px-4 py-2 text-xs font-medium text-white bg-rose-600 rounded-lg hover:bg-rose-700 transition-colors"
          >
            Retry
          </button>
        </div>
      ) : listings.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center space-y-3">
          <span className="text-3xl block">🌾</span>
          <h3 className="text-base font-semibold text-gray-900">No Listings Match Filters</h3>
          <p className="text-xs text-gray-500 max-w-sm mx-auto">
            Try adjusting your search criteria, widening the price budget, or resetting filters.
          </p>
          <button
            onClick={clearFilters}
            className="px-4 py-2 text-xs font-medium text-primary bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {listings.map((item) => {
            const avail = Number(item.quantity_available_kg) || 0;
            const totalQty = Number(item.quantity_kg) || 1;
            const percentAvailable = Math.round((avail / totalQty) * 100);

            return (
              <div
                key={item.id}
                className="bg-white rounded-2xl border border-gray-200 hover:border-emerald-300 hover:shadow-md transition-all p-5 flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                        {item.crop.name}
                      </span>
                      <h3 className="text-lg font-bold text-gray-900">
                        Grade {item.grade} {item.variety ? `• ${item.variety}` : ''}
                      </h3>
                    </div>
                    <ListingStatusChip status={item.status} />
                  </div>

                  <div className="text-xs text-gray-500 flex items-center gap-1.5">
                    <span>🏢</span>
                    <span className="font-medium text-gray-700">{item.producer.org_name}</span>
                    <span>•</span>
                    <span>{item.producer.district}, {item.producer.state}</span>
                  </div>

                  {/* Quantity bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-gray-600">
                      <span>Available: <strong className="text-gray-900">{avail} kg</strong></span>
                      <span className="text-gray-400">Total: {totalQty} kg</span>
                    </div>
                    <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-primary h-full transition-all duration-300"
                        style={{ width: `${percentAvailable}%` }}
                      />
                    </div>
                    <p className="text-[11px] text-gray-400">Min. order: {item.min_order_kg} kg</p>
                  </div>

                  {/* Price Box */}
                  <div className="bg-gray-50 rounded-xl p-3 border border-gray-100 space-y-1.5">
                    <div className="flex justify-between items-baseline">
                      <span className="text-xs text-gray-500">Farmgate Ask:</span>
                      <span className="text-sm font-bold text-gray-900">
                        ₹{Number(item.ask_price_per_kg).toFixed(2)}/kg
                      </span>
                    </div>

                    {item.landed_estimate && (
                      <div className="flex justify-between items-baseline pt-1.5 border-t border-gray-200">
                        <div>
                          <span className="text-xs font-semibold text-emerald-800">
                            Est. Landed Price:
                          </span>
                          <span className="text-[10px] text-gray-400 block font-normal">
                            ({item.landed_estimate.distance_km} km dedicated)
                          </span>
                        </div>
                        <span className="text-base font-extrabold text-emerald-700">
                          ₹{Number(item.landed_estimate.landed_price_per_kg).toFixed(2)}
                          <span className="text-xs font-normal text-gray-500">/kg</span>
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Action */}
                <div>
                  {isBuyer ? (
                    <button
                      onClick={() => setSelectedListing(item)}
                      disabled={avail <= 0 || item.status !== 'ACTIVE'}
                      className="w-full py-2 px-4 rounded-xl text-xs font-semibold text-white bg-primary hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
                    >
                      <span>🛒</span>
                      <span>Order Produce</span>
                    </button>
                  ) : (
                    <div className="text-center py-2 text-xs text-gray-400 bg-gray-50 rounded-xl">
                      Log in as buyer to place direct orders
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Order Modal */}
      {selectedListing && token && (
        <OrderModal
          listing={selectedListing}
          token={token}
          onClose={() => setSelectedListing(null)}
          onSuccess={handleOrderSuccess}
        />
      )}
    </div>
  );
};
