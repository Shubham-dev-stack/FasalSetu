import React from 'react';
import { Link } from 'react-router-dom';
import { Requirement } from '../../api/types';
import { RequirementStatusChip } from './RequirementStatusChip';
import { Calendar, Clock, Edit2, Info, Sparkles } from 'lucide-react';

interface RequirementCardProps {
  requirement: Requirement;
  onEdit?: (requirement: Requirement) => void;
  showActions?: boolean;
}

export const RequirementCard: React.FC<RequirementCardProps> = ({
  requirement,
  onEdit,
  showActions = true,
}) => {
  const percentFulfilled =
    requirement.quantity_kg > 0
      ? Math.round((requirement.quantity_fulfilled_kg / requirement.quantity_kg) * 100)
      : 0;

  const today = new Date();
  const neededDate = new Date(requirement.needed_by);
  const diffDays = Math.ceil((neededDate.getTime() - today.getTime()) / (1000 * 3600 * 24));

  const isEditable =
    requirement.status === 'OPEN' || requirement.status === 'PARTIALLY_FULFILLED';

  return (
    <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-xs hover:shadow-md transition-shadow duration-200 flex flex-col justify-between space-y-4">
      {/* Header: Crop, Min Grade & Status */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="font-bold text-base text-ink">{requirement.crop.name}</h3>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-primary-soft text-primary uppercase">
              Min Grade {requirement.grade_min}
            </span>
          </div>
          <p className="text-xs text-muted mt-0.5">
            {requirement.buyer.org_name} · {requirement.buyer.city}, {requirement.buyer.state}
          </p>
        </div>

        <RequirementStatusChip status={requirement.status} />
      </div>

      {/* Pricing & Quantities */}
      <div className="bg-bg rounded-lg p-3.5 border border-gray-200/70 space-y-2.5">
        <div className="flex items-baseline justify-between">
          <div>
            <span className="text-xs text-muted block">Max Landed Budget</span>
            <span className="text-lg font-bold text-ink font-mono">
              ₹{requirement.max_landed_price_per_kg.toFixed(2)}
            </span>
            <span className="text-xs text-muted"> / kg</span>
          </div>

          <div className="text-right">
            <span className="text-xs text-muted block">Total Quantity</span>
            <span className="text-sm font-semibold text-ink font-mono">
              {requirement.quantity_kg.toLocaleString()} kg
            </span>
          </div>
        </div>

        {/* Fulfillment progress */}
        <div>
          <div className="flex justify-between text-xs text-muted mb-1">
            <span>Fulfillment Progress</span>
            <span className="font-semibold text-ink">
              {requirement.quantity_fulfilled_kg.toLocaleString()} / {requirement.quantity_kg.toLocaleString()} kg ({percentFulfilled}%)
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                percentFulfilled >= 100
                  ? 'bg-teal-500'
                  : percentFulfilled > 0
                  ? 'bg-sky-500'
                  : 'bg-gray-300'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, percentFulfilled))}%` }}
            />
          </div>
        </div>

        {/* Landed Price Guidance Note (Educational) */}
        <div className="flex items-start space-x-1.5 pt-1 text-[11px] text-muted">
          <Info className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
          <span>Includes farmgate ask + transport + 2% platform fee</span>
        </div>
      </div>

      {/* Meta tags: Needed By date & Notes */}
      <div className="space-y-1.5 border-t border-gray-100 pt-3">
        <div className="grid grid-cols-2 gap-2 text-[11px] text-muted">
          <div className="flex items-center space-x-1.5">
            <Calendar className="w-3.5 h-3.5 text-gray-400 shrink-0" />
            <span>Needed by: {requirement.needed_by}</span>
          </div>

          <div className="flex items-center space-x-1.5 justify-end">
            <Clock className="w-3.5 h-3.5 text-gray-400 shrink-0" />
            <span className={diffDays < 0 ? 'text-rose-600 font-semibold' : ''}>
              {diffDays < 0
                ? 'Past deadline'
                : diffDays === 0
                ? 'Needed today'
                : `In ${diffDays} day${diffDays === 1 ? '' : 's'}`}
            </span>
          </div>
        </div>

        {requirement.notes && (
          <p className="text-xs text-ink/80 bg-gray-50 p-2 rounded border border-gray-100 italic">
            "{requirement.notes}"
          </p>
        )}
      </div>

      {/* Action Buttons */}
      {showActions && (
        <div className="pt-2 flex items-center space-x-2">
          {isEditable && (
            <Link
              to={`/buyer/requirements/${requirement.id}/match`}
              className="flex-1 inline-flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded-lg bg-primary text-white text-xs font-semibold hover:bg-primary-hover transition-colors shadow-xs"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Find Matches</span>
            </Link>
          )}

          {isEditable && onEdit && (
            <button
              type="button"
              onClick={() => onEdit(requirement)}
              className="inline-flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded-lg border border-gray-300 text-xs font-semibold text-ink hover:bg-gray-50 transition-colors"
            >
              <Edit2 className="w-3.5 h-3.5 text-muted" />
              <span>Edit</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};
