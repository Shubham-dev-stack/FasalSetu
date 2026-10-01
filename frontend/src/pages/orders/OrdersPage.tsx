import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import { fetchOrdersApi } from '../../api/orders';
import { Order } from '../../api/types';
import { OrderStatusChip } from '../../components/domain/OrderStatusChip';
import {
  ClipboardList,
  RefreshCw,
  AlertCircle,
  ArrowRight,
  Calendar,
  Package,
  MapPin,
  TrendingUp,
} from 'lucide-react';

const STATUS_TABS = [
  { key: 'ALL', label: 'All Orders' },
  { key: 'PLACED', label: 'Placed' },
  { key: 'CONFIRMED', label: 'Confirmed' },
  { key: 'IN_TRANSIT', label: 'In Transit' },
  { key: 'DELIVERED', label: 'Delivered' },
  { key: 'CANCELLED', label: 'Cancelled' },
  { key: 'REJECTED', label: 'Rejected' },
];

export const OrdersPage: React.FC = () => {
  const { token, user } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('ALL');

  const [orders, setOrders] = useState<Order[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadOrders = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchOrdersApi(token, {
        status: activeTab === 'ALL' ? undefined : activeTab,
      });
      setOrders(res.items);
      setTotal(res.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch orders');
    } finally {
      setLoading(false);
    }
  }, [token, activeTab]);

  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return isoString;
    }
  };

  const roleUpper = user?.role ? (user.role as string).toUpperCase() : '';
  const isBuyer = roleUpper === 'BUYER' || (user?.role as string | undefined)?.startsWith('buyer_');
  const isProducer =
    roleUpper === 'PRODUCER' || user?.role === 'farmer' || user?.role === 'fpo';

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-surface rounded-xl border border-gray-200 p-6 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-ink">Order Management</h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-primary-soft text-primary font-bold">
              {total} {total === 1 ? 'Order' : 'Orders'}
            </span>
          </div>
          <p className="text-xs text-muted mt-1">
            Track direct trade commitments, confirm orders, and inspect landed cost breakdowns.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={loadOrders}
            disabled={loading}
            className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-muted transition-colors"
            title="Refresh orders"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          {isBuyer && (
            <Link
              to="/market"
              className="inline-flex items-center space-x-1.5 bg-primary hover:bg-primary-hover text-white text-xs font-bold px-4 py-2.5 rounded-lg shadow-sm transition-colors"
            >
              <Package className="w-4 h-4" />
              <span>Browse Marketplace</span>
            </Link>
          )}
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

      {/* Error Banner */}
      {error && (
        <div className="bg-danger-soft border border-danger/30 rounded-xl p-4 flex items-center justify-between text-danger text-sm">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={loadOrders}
            className="text-xs font-bold underline hover:opacity-80"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-32 bg-gray-100 animate-pulse rounded-xl border border-gray-200"
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && orders.length === 0 && (
        <div className="text-center py-16 bg-surface rounded-xl border border-dashed border-gray-300 p-8">
          <ClipboardList className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-ink">No orders found</h3>
          <p className="text-xs text-muted max-w-sm mx-auto mt-1 mb-6">
            {activeTab === 'ALL'
              ? 'No orders have been placed or assigned to your account yet.'
              : `No orders currently match status "${activeTab}".`}
          </p>
          {isBuyer && (
            <Link
              to="/market"
              className="inline-flex items-center space-x-1.5 bg-primary text-white text-xs font-bold px-4 py-2.5 rounded-lg hover:bg-primary-hover shadow-sm transition-colors"
            >
              <span>Explore Farmgate Lots</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>
      )}

      {/* Orders List */}
      {!loading && !error && orders.length > 0 && (
        <div className="space-y-3">
          {orders.map((order) => {
            const counterpartyLabel = isProducer
              ? order.buyer.org_name
              : `${order.producer.org_name} (${order.producer.district}, ${order.producer.state})`;

            return (
              <div
                key={order.id}
                className="bg-surface rounded-xl border border-gray-200 p-5 shadow-xs hover:border-gray-300 transition-all"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 pb-3">
                  <div className="flex items-center space-x-2 flex-wrap">
                    <span className="font-mono font-bold text-ink text-sm">
                      #ORD-{order.id.toString().padStart(4, '0')}
                    </span>
                    <OrderStatusChip status={order.status} />
                    <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-gray-100 text-gray-600 border border-gray-200">
                      {order.origin}
                    </span>
                    {order.is_demo && (
                      <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                        Demo
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-muted">
                    Placed on {formatDate(order.created_at)}
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 py-3 text-xs">
                  {/* Crop & Quantity */}
                  <div>
                    <span className="text-muted block text-[11px] uppercase tracking-wider">
                      Crop & Quantity
                    </span>
                    <span className="text-sm font-bold text-ink mt-0.5 block">
                      {order.crop.name}
                    </span>
                    <span className="text-muted font-medium">
                      {order.quantity_kg.toLocaleString()} kg
                    </span>
                  </div>

                  {/* Counterparty */}
                  <div>
                    <span className="text-muted block text-[11px] uppercase tracking-wider">
                      {isProducer ? 'Buyer' : 'Producer'}
                    </span>
                    <span className="text-ink font-semibold mt-0.5 block truncate">
                      {counterpartyLabel}
                    </span>
                    <span className="text-muted text-[11px] flex items-center gap-1 mt-0.5">
                      <MapPin className="w-3 h-3 text-gray-400" />
                      {isProducer ? 'Delivery Destination' : `${order.producer.district}, ${order.producer.state}`}
                    </span>
                  </div>

                  {/* Delivery Date */}
                  <div>
                    <span className="text-muted block text-[11px] uppercase tracking-wider">
                      Delivery Date
                    </span>
                    <span className="text-ink font-medium mt-0.5 flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-gray-400" />
                      {order.delivery_date}
                    </span>
                    <span className="text-muted text-[11px]">
                      Agreed Farmgate: ₹{order.agreed_price_per_kg.toFixed(2)}/kg
                    </span>
                  </div>

                  {/* Total & Landed Price */}
                  <div>
                    <span className="text-muted block text-[11px] uppercase tracking-wider">
                      Total Landed Cost
                    </span>
                    <span className="text-sm font-bold text-primary mt-0.5 block">
                      ₹{order.total_amount_estimate.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    <span className="text-muted text-[11px]">
                      ≈ ₹{order.landed_price_per_kg_estimate.toFixed(2)}/kg delivered
                    </span>
                  </div>
                </div>

                {/* Footer action */}
                <div className="pt-3 border-t border-gray-100 flex items-center justify-between">
                  <div className="text-[11px] text-muted flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5 text-gray-400" />
                    <span>Includes farmgate produce, dedicated haulage & 2% platform fee</span>
                  </div>
                  <Link
                    to={`/orders/${order.id}`}
                    className="inline-flex items-center space-x-1 text-primary hover:text-primary-hover font-semibold text-xs transition-colors"
                  >
                    <span>View Details & Timeline</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
