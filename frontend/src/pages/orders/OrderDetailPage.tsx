import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import { fetchOrderByIdApi, transitionOrderApi } from '../../api/orders';
import { Order } from '../../api/types';
import { OrderStatusChip } from '../../components/domain/OrderStatusChip';
import { OrderPriceBreakdown } from '../../components/orders/OrderPriceBreakdown';
import { OrderTimeline } from '../../components/orders/OrderTimeline';
import {
  ArrowLeft,
  Calendar,
  CheckCircle,
  XCircle,
  AlertCircle,
  Package,
  MapPin,
  Building2,
  Info,
  Truck,
} from 'lucide-react';

export const OrderDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { token, user } = useAuth();
  const navigate = useNavigate();

  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Transition modal state
  const [transitionTarget, setTransitionTarget] = useState<
    'CONFIRMED' | 'REJECTED' | 'CANCELLED' | null
  >(null);
  const [transitionNote, setTransitionNote] = useState<string>('');
  const [submittingTransition, setSubmittingTransition] = useState<boolean>(false);
  const [transitionError, setTransitionError] = useState<string | null>(null);

  const loadOrder = useCallback(async () => {
    if (!token || !id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchOrderByIdApi(token, Number(id));
      setOrder(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load order details');
    } finally {
      setLoading(false);
    }
  }, [token, id]);

  useEffect(() => {
    loadOrder();
  }, [loadOrder]);

  const handleTransitionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !order || !transitionTarget) return;

    setSubmittingTransition(true);
    setTransitionError(null);
    try {
      const updated = await transitionOrderApi(token, order.id, {
        to_status: transitionTarget,
        note: transitionNote.trim() || undefined,
      });
      setOrder(updated);
      setTransitionTarget(null);
      setTransitionNote('');
    } catch (err) {
      setTransitionError(
        err instanceof Error ? err.message : 'Failed to update order status'
      );
    } finally {
      setSubmittingTransition(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="flex items-center space-x-2 text-muted text-sm">
          <span className="animate-spin inline-block w-5 h-5 border-2 border-primary border-t-transparent rounded-full" />
          <span>Loading order #ORD-{id}...</span>
        </div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="max-w-2xl mx-auto py-12 text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-danger mx-auto" />
        <h2 className="text-lg font-bold text-ink">Order Not Found</h2>
        <p className="text-sm text-muted">{error || 'This order does not exist or you do not have permission to view it.'}</p>
        <button
          onClick={() => navigate('/orders')}
          className="inline-flex items-center space-x-1.5 px-4 py-2 bg-primary text-white text-xs font-bold rounded-lg hover:bg-primary-hover shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Orders</span>
        </button>
      </div>
    );
  }

  // Authorization checks for transitions
  const roleUpper = user?.role?.toUpperCase();
  const isAdmin = roleUpper === 'ADMIN';
  const isOwnerProducer =
    roleUpper === 'PRODUCER' || user?.role === 'farmer' || user?.role === 'fpo';
  const isOwnerBuyer =
    roleUpper === 'BUYER' || user?.role?.startsWith('buyer_');

  const canConfirm =
    order.status === 'PLACED' && (isOwnerProducer || isAdmin);

  const canReject =
    order.status === 'PLACED' && (isOwnerProducer || isAdmin);

  const canCancel =
    (order.status === 'PLACED' && (isOwnerBuyer || isAdmin)) ||
    (order.status === 'CONFIRMED' &&
      order.shipment_id === null &&
      (isOwnerBuyer || isOwnerProducer || isAdmin));

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-surface rounded-xl border border-gray-200 p-6 shadow-xs">
        <div>
          <Link
            to="/orders"
            className="inline-flex items-center space-x-1 text-xs text-muted hover:text-ink font-medium mb-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Orders</span>
          </Link>

          <div className="flex items-center space-x-3 flex-wrap">
            <h1 className="text-2xl font-bold font-mono text-ink">
              #ORD-{order.id.toString().padStart(4, '0')}
            </h1>
            <OrderStatusChip status={order.status} />
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 text-gray-700 border border-gray-200">
              {order.origin}
            </span>
            {order.is_demo && (
              <span className="text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                Demo
              </span>
            )}
          </div>
        </div>

        {/* Transition Action Buttons */}
        <div className="flex items-center space-x-2 flex-wrap">
          {canConfirm && (
            <button
              onClick={() => {
                setTransitionTarget('CONFIRMED');
                setTransitionError(null);
              }}
              className="inline-flex items-center space-x-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2.5 rounded-lg shadow-sm transition-colors"
            >
              <CheckCircle className="w-4 h-4" />
              <span>Confirm Order</span>
            </button>
          )}

          {canReject && (
            <button
              onClick={() => {
                setTransitionTarget('REJECTED');
                setTransitionError(null);
              }}
              className="inline-flex items-center space-x-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold px-4 py-2.5 rounded-lg shadow-sm transition-colors"
            >
              <XCircle className="w-4 h-4" />
              <span>Reject Order</span>
            </button>
          )}

          {canCancel && (
            <button
              onClick={() => {
                setTransitionTarget('CANCELLED');
                setTransitionError(null);
              }}
              className="inline-flex items-center space-x-1.5 border border-gray-300 hover:bg-gray-100 text-gray-700 text-xs font-bold px-4 py-2.5 rounded-lg transition-colors"
            >
              <XCircle className="w-4 h-4 text-gray-500" />
              <span>Cancel Order</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols on lg) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Order Details Card */}
          <div className="bg-surface rounded-xl border border-gray-200 p-6 shadow-xs space-y-4">
            <h2 className="text-sm font-bold text-ink uppercase tracking-wider border-b border-gray-100 pb-3 flex items-center gap-2">
              <Package className="w-4 h-4 text-primary" />
              Produce & Delivery Specifications
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-muted block text-[11px] uppercase tracking-wider">
                  Crop Lot
                </span>
                <span className="text-base font-bold text-ink mt-0.5 block">
                  {order.crop.name}
                </span>
                <span className="text-muted">
                  Lot Listing #{order.listing_id}
                </span>
              </div>

              <div>
                <span className="text-muted block text-[11px] uppercase tracking-wider">
                  Committed Quantity
                </span>
                <span className="text-base font-bold text-ink mt-0.5 block">
                  {order.quantity_kg.toLocaleString()} kg
                </span>
                <span className="text-muted">
                  Agreed Farmgate: ₹{order.agreed_price_per_kg.toFixed(2)}/kg
                </span>
              </div>

              <div>
                <span className="text-muted block text-[11px] uppercase tracking-wider">
                  Delivery Date
                </span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span className="text-ink font-semibold text-sm">
                    {order.delivery_date}
                  </span>
                </div>
              </div>

              <div>
                <span className="text-muted block text-[11px] uppercase tracking-wider">
                  Procurement Source
                </span>
                <span className="text-ink font-medium mt-0.5 block">
                  {order.origin === 'MARKETPLACE'
                    ? 'Direct Unified Marketplace Order'
                    : 'Smart Algorithm Matching'}
                </span>
                {order.requirement_id && (
                  <span className="text-muted text-[11px]">
                    Fulfills Demand #{order.requirement_id}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Counterparties Card */}
          <div className="bg-surface rounded-xl border border-gray-200 p-6 shadow-xs space-y-4">
            <h2 className="text-sm font-bold text-ink uppercase tracking-wider border-b border-gray-100 pb-3 flex items-center gap-2">
              <Building2 className="w-4 h-4 text-primary" />
              Supply Chain Participants
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
              {/* Producer */}
              <div className="bg-gray-50/70 p-4 rounded-xl border border-gray-200/80 space-y-2">
                <span className="text-[10px] font-bold text-muted uppercase tracking-wider block">
                  Selling Producer
                </span>
                <h3 className="font-bold text-ink text-sm">
                  {order.producer.org_name}
                </h3>
                <div className="text-muted flex items-center gap-1.5 text-xs">
                  <MapPin className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                  <span>
                    {order.producer.district}, {order.producer.state}
                  </span>
                </div>
              </div>

              {/* Buyer */}
              <div className="bg-gray-50/70 p-4 rounded-xl border border-gray-200/80 space-y-2">
                <span className="text-[10px] font-bold text-muted uppercase tracking-wider block">
                  Procuring Buyer
                </span>
                <h3 className="font-bold text-ink text-sm">
                  {order.buyer.org_name}
                </h3>
                <div className="text-muted flex items-center gap-1.5 text-xs">
                  <Building2 className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                  <span>Registered Buyer Organization</span>
                </div>
              </div>
            </div>
          </div>

          {/* Landed Cost Breakdown */}
          <OrderPriceBreakdown
            orderId={order.id}
            token={token}
            fallbackQuantityKg={order.quantity_kg}
            fallbackAgreedPricePerKg={order.agreed_price_per_kg}
            fallbackTransportCostPerKg={order.transport_cost_estimate_per_kg}
            fallbackPlatformFeePerKg={order.platform_fee_per_kg}
            fallbackLandedPricePerKg={order.landed_price_per_kg_estimate}
            fallbackTotalAmount={order.total_amount_estimate}
          />
        </div>

        {/* Right Column (1 Col on lg) */}
        <div className="space-y-6">
          {/* Order Lifecycle Timeline */}
          <OrderTimeline events={order.events} />

          {/* Logistics & Dispatch Info */}
          <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-xs space-y-3 text-xs">
            <h3 className="font-semibold text-ink text-sm border-b border-gray-100 pb-2 flex items-center gap-2">
              <Truck className="w-4 h-4 text-primary" />
              Logistics Dispatch Info
            </h3>

            {order.shipment_id ? (
              <div className="space-y-2">
                <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px] font-bold border border-emerald-200 inline-block">
                  Assigned to Shipment #{order.shipment_id}
                </span>
                <p className="text-muted">
                  This order has been bundled into a multi-stop vehicle route.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <span className="text-amber-700 bg-amber-50 px-2 py-0.5 rounded text-[11px] font-bold border border-amber-200 inline-block">
                  Unrouted Order
                </span>
                <p className="text-muted leading-relaxed">
                  Upon confirmation by the producer, this order is eligible for automated vehicle route optimization during regional batch dispatch.
                </p>
              </div>
            )}
          </div>

          {/* Platform Notice */}
          <div className="bg-blue-50/60 rounded-xl border border-blue-200/70 p-4 text-xs text-blue-900 space-y-2">
            <div className="flex items-center gap-1.5 font-bold">
              <Info className="w-4 h-4 text-blue-600 shrink-0" />
              <span>Direct Coordination Policy</span>
            </div>
            <p className="text-blue-800 leading-relaxed text-[11px]">
              FasalSetu coordinates transparent agricultural discovery, pricing, and logistics. Settlement and physical verification take place directly between parties upon delivery.
            </p>
          </div>
        </div>
      </div>

      {/* Transition Modal */}
      {transitionTarget && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4 border border-gray-200 animate-in fade-in">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <h3 className="text-base font-bold text-gray-900">
                {transitionTarget === 'CONFIRMED' && 'Confirm Order Commitment'}
                {transitionTarget === 'REJECTED' && 'Reject Order Request'}
                {transitionTarget === 'CANCELLED' && 'Cancel Order'}
              </h3>
              <button
                onClick={() => setTransitionTarget(null)}
                className="text-gray-400 hover:text-gray-600 p-1"
              >
                ✕
              </button>
            </div>

            {transitionError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-xs">
                {transitionError}
              </div>
            )}

            <p className="text-xs text-gray-600 leading-relaxed">
              {transitionTarget === 'CONFIRMED' &&
                'Confirming commits this produce lot for dispatch. The order will be scheduled for vehicle route planning.'}
              {transitionTarget === 'REJECTED' &&
                'Rejecting will decline this order and immediately return the reserved quantity back to the active produce listing.'}
              {transitionTarget === 'CANCELLED' &&
                'Cancelling will terminate this order and immediately restore the reserved quantity back to the marketplace.'}
            </p>

            <form onSubmit={handleTransitionSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Reason or Operational Note (Optional)
                </label>
                <textarea
                  value={transitionNote}
                  onChange={(e) => setTransitionNote(e.target.value)}
                  placeholder="e.g. Harvest packaged and ready for pickup, or buyer requested cancellation."
                  rows={3}
                  className="w-full text-xs p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setTransitionTarget(null)}
                  disabled={submittingTransition}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>

                <button
                  type="submit"
                  disabled={submittingTransition}
                  className={`px-4 py-2 rounded-lg text-xs font-bold text-white shadow-sm flex items-center space-x-1.5 ${
                    transitionTarget === 'CONFIRMED'
                      ? 'bg-emerald-600 hover:bg-emerald-700'
                      : 'bg-rose-600 hover:bg-rose-700'
                  }`}
                >
                  {submittingTransition && (
                    <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  )}
                  <span>
                    {transitionTarget === 'CONFIRMED' && 'Yes, Confirm Order'}
                    {transitionTarget === 'REJECTED' && 'Yes, Reject Order'}
                    {transitionTarget === 'CANCELLED' && 'Yes, Cancel Order'}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
