import React from 'react';
import { Listing } from '../../api/types';
import { ListingStatusChip } from './ListingStatusChip';
import { Calendar, Clock, Edit2 } from 'lucide-react';

interface ListingCardProps {
  listing: Listing;
  onEdit?: (listing: Listing) => void;
  showActions?: boolean;
}

export const ListingCard: React.FC<ListingCardProps> = ({
  listing,
  onEdit,
  showActions = true,
}) => {
  const percentAvailable =
    listing.quantity_kg > 0
      ? Math.round((listing.quantity_available_kg / listing.quantity_kg) * 100)
      : 0;

  const today = new Date();
  const untilDate = new Date(listing.available_until);
  const diffDays = Math.ceil((untilDate.getTime() - today.getTime()) / (1000 * 3600 * 24));

  return (
    <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-xs hover:shadow-md transition-shadow duration-200 flex flex-col justify-between space-y-4">
      {/* Header: Crop, Grade & Status */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="font-bold text-base text-ink">{listing.crop.name}</h3>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-primary-soft text-primary uppercase">
              Grade {listing.grade}
            </span>
            {listing.variety && (
              <span className="text-xs text-muted">({listing.variety})</span>
            )}
          </div>
          <p className="text-xs text-muted mt-0.5">
            {listing.producer.org_name} · {listing.producer.district}, {listing.producer.state}
          </p>
        </div>

        <ListingStatusChip status={listing.status} />
      </div>

      {/* Pricing & Quantities */}
      <div className="bg-bg rounded-lg p-3.5 border border-gray-200/70 space-y-2.5">
        <div className="flex items-baseline justify-between">
          <div>
            <span className="text-xs text-muted block">Ask Price</span>
            <span className="text-lg font-bold text-ink font-mono">
              ₹{listing.ask_price_per_kg.toFixed(2)}
            </span>
            <span className="text-xs text-muted"> / kg</span>
          </div>

          <div className="text-right">
            <span className="text-xs text-muted block">Min Order</span>
            <span className="text-sm font-semibold text-ink font-mono">
              {listing.min_order_kg.toLocaleString()} kg
            </span>
          </div>
        </div>

        {/* Quantity progress */}
        <div>
          <div className="flex justify-between text-xs text-muted mb-1">
            <span>Available Volume</span>
            <span className="font-semibold text-ink">
              {listing.quantity_available_kg.toLocaleString()} / {listing.quantity_kg.toLocaleString()} kg ({percentAvailable}%)
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                percentAvailable > 50
                  ? 'bg-emerald-500'
                  : percentAvailable > 20
                  ? 'bg-amber-500'
                  : 'bg-rose-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, percentAvailable))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Meta tags: Harvest date & Expiration */}
      <div className="grid grid-cols-2 gap-2 text-[11px] text-muted border-t border-gray-100 pt-3">
        <div className="flex items-center space-x-1.5">
          <Calendar className="w-3.5 h-3.5 text-gray-400 shrink-0" />
          <span>Harvest: {listing.harvest_age_days === 0 ? 'Today' : `${listing.harvest_age_days}d ago`}</span>
        </div>

        <div className="flex items-center space-x-1.5 justify-end">
          <Clock className="w-3.5 h-3.5 text-gray-400 shrink-0" />
          <span className={diffDays < 0 ? 'text-rose-600 font-semibold' : ''}>
            {diffDays < 0 ? 'Expired' : diffDays === 0 ? 'Expires today' : `Expires in ${diffDays}d`}
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      {showActions && listing.status === 'ACTIVE' && onEdit && (
        <div className="pt-2">
          <button
            type="button"
            onClick={() => onEdit(listing)}
            className="w-full inline-flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded-lg border border-gray-300 text-xs font-semibold text-ink hover:bg-gray-50 transition-colors"
          >
            <Edit2 className="w-3.5 h-3.5 text-muted" />
            <span>Edit / Withdraw</span>
          </button>
        </div>
      )}
    </div>
  );
};
