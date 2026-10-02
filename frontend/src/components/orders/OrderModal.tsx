import React, { useEffect, useState } from 'react';
import { Listing, LogisticsEstimateResponse, Order } from '../../api/types';
import { createOrderApi } from '../../api/orders';
import { fetchLogisticsEstimateApi } from '../../api/logistics';
import { LogisticsEstimate } from '../domain/LogisticsEstimate';

interface OrderModalProps {
  listing: Listing;
  token: string;
  onClose: () => void;
  onSuccess: (order: Order) => void;
}

export const OrderModal: React.FC<OrderModalProps> = ({
  listing,
  token,
  onClose,
  onSuccess,
}) => {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 2);
  const defaultDateStr = tomorrow.toISOString().split('T')[0];

  const minOrder = Number(listing.min_order_kg) || 100;
  const maxAvailable = Number(listing.quantity_available_kg) || 0;

  const [quantity, setQuantity] = useState<number>(minOrder);
  const [deliveryDate, setDeliveryDate] = useState<string>(defaultDateStr);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Live Logistics Estimate state
  const [logisticsEst, setLogisticsEst] = useState<LogisticsEstimateResponse | null>(null);

  useEffect(() => {
    if (quantity >= minOrder && quantity <= maxAvailable) {
      fetchLogisticsEstimateApi(
        {
          listing_id: listing.id,
          quantity_kg: quantity,
        },
        token
      )
        .then((est) => {
          setLogisticsEst(est);
        })
        .catch(() => {
          // If profile coordinates are unavailable or error occurs, fallback to listing landed_estimate
          setLogisticsEst(null);
        });
    } else {
      setLogisticsEst(null);
    }
  }, [listing.id, quantity, minOrder, maxAvailable, token]);

  // Financial calculations
  const askPrice = Number(listing.ask_price_per_kg) || 0;
  const farmgateTotal = quantity * askPrice;
  const transportPerKg = logisticsEst ? logisticsEst.cost_per_kg : (listing.landed_estimate?.transport_cost_per_kg || 0);
  const transportTotal = logisticsEst ? logisticsEst.cost_total : (quantity * transportPerKg);
  const platformFeePerKg = Math.round(askPrice * 0.02 * 100) / 100;
  const platformFeeTotal = quantity * platformFeePerKg;
  const landedTotal = farmgateTotal + transportTotal + platformFeeTotal;
  const landedPerKg = quantity > 0 ? (landedTotal / quantity).toFixed(2) : '0.00';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (quantity < minOrder) {
      setError(`Minimum order quantity is ${minOrder} kg.`);
      return;
    }

    if (quantity > maxAvailable) {
      setError(`Maximum available quantity is ${maxAvailable} kg.`);
      return;
    }

    if (!deliveryDate) {
      setError('Please select a requested delivery date.');
      return;
    }

    setSubmitting(true);
    try {
      const order = await createOrderApi(token, {
        listing_id: listing.id,
        quantity_kg: quantity,
        delivery_date: deliveryDate,
      });
      onSuccess(order);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to place order. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-gray-200 space-y-5">
        <div className="flex justify-between items-start border-b border-gray-100 pb-3">
          <div>
            <span className="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              Direct Marketplace Purchase
            </span>
            <h2 className="text-lg font-bold text-gray-900 mt-1">
              Order {listing.crop.name} (Grade {listing.grade})
            </h2>
            <p className="text-xs text-gray-500">
              Sold by {listing.producer.org_name} • {listing.producer.district}, {listing.producer.state}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs p-3 rounded-lg flex items-start gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Order Quantity (kg)
              </label>
              <input
                type="number"
                min={minOrder}
                max={maxAvailable}
                step={10}
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:outline-none"
                required
              />
              <p className="text-[11px] text-gray-500 mt-1">
                Min: {minOrder} kg • Available: {maxAvailable} kg
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Requested Delivery Date
              </label>
              <input
                type="date"
                min={new Date().toISOString().split('T')[0]}
                value={deliveryDate}
                onChange={(e) => setDeliveryDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:outline-none"
                required
              />
              <p className="text-[11px] text-gray-500 mt-1">Required in IST</p>
            </div>
          </div>

          {/* Dedicated Logistics Estimate Component */}
          {logisticsEst && (
            <LogisticsEstimate estimate={logisticsEst} quantityKg={quantity} />
          )}

          {/* Pricing Preview */}
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-2 text-xs">
            <div className="flex justify-between text-gray-600">
              <span>Farmgate ({quantity} kg × ₹{askPrice.toFixed(2)}):</span>
              <span className="font-medium text-gray-900">₹{farmgateTotal.toFixed(2)}</span>
            </div>
            {transportPerKg > 0 && (
              <div className="flex justify-between text-gray-600">
                <span>
                  Est. Transport ({quantity} kg × ₹{transportPerKg.toFixed(2)})
                  {logisticsEst && <span className="text-[10px] text-emerald-600 ml-1 font-semibold">(live calc)</span>}:
                </span>
                <span className="font-medium text-gray-900">₹{transportTotal.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between text-gray-600">
              <span>Platform Fee 2%:</span>
              <span className="font-medium text-gray-900">₹{platformFeeTotal.toFixed(2)}</span>
            </div>
            <div className="pt-2 border-t border-gray-200 flex justify-between items-baseline text-sm">
              <span className="font-bold text-gray-900">Est. Total Landed Cost:</span>
              <div className="text-right">
                <span className="font-bold text-emerald-700 text-base">
                  ₹{landedTotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <p className="text-[11px] text-gray-500">approx. ₹{landedPerKg}/kg</p>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 text-sm font-medium text-white bg-primary hover:bg-emerald-700 rounded-lg shadow-sm disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {submitting && (
                <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
              )}
              <span>{submitting ? 'Placing Order...' : 'Confirm Order'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
