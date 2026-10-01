import React, { useState } from 'react';
import { Requirement, RequirementUpdateRequest } from '../../api/types';
import { X, AlertCircle } from 'lucide-react';

interface EditRequirementModalProps {
  requirement: Requirement;
  isOpen: boolean;
  onClose: () => void;
  onSave: (id: number, data: RequirementUpdateRequest) => Promise<void>;
}

export const EditRequirementModal: React.FC<EditRequirementModalProps> = ({
  requirement,
  isOpen,
  onClose,
  onSave,
}) => {
  const [maxPrice, setMaxPrice] = useState<number>(requirement.max_landed_price_per_kg);
  const [quantity, setQuantity] = useState<number>(requirement.quantity_kg);
  const [neededBy, setNeededBy] = useState<string>(requirement.needed_by);
  const [notes, setNotes] = useState<string>(requirement.notes || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const fulfilled = requirement.quantity_fulfilled_kg;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (quantity < fulfilled) {
      setError(`Quantity cannot be reduced below already fulfilled amount (${fulfilled.toFixed(1)} kg)`);
      return;
    }
    if (maxPrice <= 0) {
      setError('Max landed price must be greater than zero');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSave(requirement.id, {
        max_landed_price_per_kg: maxPrice,
        quantity_kg: quantity,
        needed_by: neededBy,
        notes: notes.trim() || null,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update requirement');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelRequirement = async () => {
    if (!window.confirm('Are you sure you want to cancel this procurement requirement?')) {
      return;
    }
    setIsSubmitting(true);
    try {
      await onSave(requirement.id, { status: 'CANCELLED' });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel requirement');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
      <div className="bg-surface rounded-2xl max-w-md w-full border border-gray-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h3 className="font-bold text-base text-ink">Edit Requirement</h3>
            <p className="text-xs text-muted">
              {requirement.crop.name} · Min Grade {requirement.grade_min} (#{requirement.id})
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
              Max Landed Price Budget (₹/kg)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2.5 text-sm text-muted">₹</span>
              <input
                type="number"
                step="0.25"
                min="0.5"
                value={maxPrice}
                onChange={(e) => setMaxPrice(parseFloat(e.target.value) || 0)}
                required
                className="w-full pl-8 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
            <p className="text-[11px] text-muted mt-1">
              Includes farmgate ask + transport + 2% platform fee
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink mb-1">
              Required Quantity (kg)
            </label>
            <input
              type="number"
              step="10"
              min={fulfilled > 0 ? fulfilled : 1}
              value={quantity}
              onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
              required
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            />
            {fulfilled > 0 && (
              <p className="text-[11px] text-muted mt-1">
                Already fulfilled: {fulfilled} kg (min total: {fulfilled} kg)
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink mb-1">
              Needed By Date
            </label>
            <input
              type="date"
              value={neededBy}
              onChange={(e) => setNeededBy(e.target.value)}
              required
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink mb-1">
              Procurement Notes
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Delivery slot preferences, destination packaging notes"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={handleCancelRequirement}
              disabled={isSubmitting}
              className="text-xs font-semibold text-rose-600 hover:text-rose-800 hover:bg-rose-50 px-3 py-2 rounded-lg transition-colors"
            >
              Cancel Requirement
            </button>

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="text-xs font-medium text-muted hover:text-ink px-3 py-2 rounded-lg"
              >
                Close
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
