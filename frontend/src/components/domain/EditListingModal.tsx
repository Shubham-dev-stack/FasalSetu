import React, { useState } from 'react';
import { Listing, ListingUpdateRequest } from '../../api/types';
import { X, AlertCircle } from 'lucide-react';

interface EditListingModalProps {
  listing: Listing;
  isOpen: boolean;
  onClose: () => void;
  onSave: (id: number, data: ListingUpdateRequest) => Promise<void>;
}

export const EditListingModal: React.FC<EditListingModalProps> = ({
  listing,
  isOpen,
  onClose,
  onSave,
}) => {
  const [askPrice, setAskPrice] = useState<number>(listing.ask_price_per_kg);
  const [quantity, setQuantity] = useState<number>(listing.quantity_kg);
  const [minOrder, setMinOrder] = useState<number>(listing.min_order_kg);
  const [availableUntil, setAvailableUntil] = useState<string>(listing.available_until);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const reserved = listing.quantity_kg - listing.quantity_available_kg;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (quantity < reserved) {
      setError(`Quantity cannot be reduced below reserved amount (${reserved.toFixed(1)} kg)`);
      return;
    }
    if (minOrder > quantity) {
      setError('Minimum order cannot exceed total quantity');
      return;
    }
    if (askPrice <= 0) {
      setError('Ask price must be greater than zero');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSave(listing.id, {
        ask_price_per_kg: askPrice,
        quantity_kg: quantity,
        min_order_kg: minOrder,
        available_until: availableUntil,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update listing');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleWithdraw = async () => {
    if (!window.confirm('Are you sure you want to withdraw this produce lot from the marketplace?')) {
      return;
    }
    setIsSubmitting(true);
    try {
      await onSave(listing.id, { status: 'WITHDRAWN' });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to withdraw listing');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
      <div className="bg-surface rounded-2xl max-w-md w-full border border-gray-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h3 className="font-bold text-base text-ink">Edit Produce Lot</h3>
            <p className="text-xs text-muted">
              {listing.crop.name} · Grade {listing.grade} (#{listing.id})
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-ink p-1 rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-ink mb-1">
              Ask Price (₹/kg)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2.5 text-sm text-muted">₹</span>
              <input
                type="number"
                step="0.25"
                min="0.5"
                value={askPrice}
                onChange={(e) => setAskPrice(parseFloat(e.target.value) || 0)}
                required
                className="w-full pl-8 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-ink mb-1">
                Total Quantity (kg)
              </label>
              <input
                type="number"
                step="10"
                min={reserved > 0 ? reserved : 1}
                value={quantity}
                onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
                required
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
              {reserved > 0 && (
                <p className="text-[11px] text-muted mt-1">
                  Reserved: {reserved} kg (min total: {reserved} kg)
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-ink mb-1">
                Min Order (kg)
              </label>
              <input
                type="number"
                step="10"
                min="1"
                max={quantity}
                value={minOrder}
                onChange={(e) => setMinOrder(parseFloat(e.target.value) || 0)}
                required
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink mb-1">
              Available Until Date
            </label>
            <input
              type="date"
              value={availableUntil}
              onChange={(e) => setAvailableUntil(e.target.value)}
              required
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={handleWithdraw}
              disabled={isSubmitting}
              className="text-xs font-semibold text-rose-600 hover:text-rose-800 hover:bg-rose-50 px-3 py-2 rounded-lg transition-colors"
            >
              Withdraw Lot
            </button>

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="text-xs font-medium text-muted hover:text-ink px-3 py-2 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="bg-primary hover:bg-primary-hover text-white text-xs font-bold px-4 py-2 rounded-lg shadow-sm disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
