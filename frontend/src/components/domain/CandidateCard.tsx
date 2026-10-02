import React, { useState } from 'react';
import { Candidate } from '../../api/types';
import { ScoreBreakdown } from './ScoreBreakdown';
import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  MapPin,
  Sparkles,
  Truck,
  UserCheck,
} from 'lucide-react';

interface CandidateCardProps {
  candidate: Candidate;
  isAllocated?: boolean;
}

export const CandidateCard: React.FC<CandidateCardProps> = ({
  candidate,
  isAllocated = false,
}) => {
  const [showScoreDetails, setShowScoreDetails] = useState(false);

  return (
    <div
      className={`rounded-xl border transition-all duration-200 p-5 shadow-xs ${
        isAllocated
          ? 'bg-surface border-primary/30 ring-1 ring-primary/20 shadow-sm'
          : 'bg-surface border-gray-200 hover:border-gray-300'
      }`}
    >
      {/* Top Header: Rank, Producer & Allocation Pill */}
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold font-mono ${
                candidate.rank === 1
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              #{candidate.rank} {candidate.rank === 1 ? 'Top Match' : 'Candidate'}
            </span>

            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-primary-soft text-primary">
              Grade {candidate.listing.grade}
            </span>

            {candidate.listing.producer.producer_type && (
              <span className="text-[11px] font-medium text-muted bg-gray-50 px-2 py-0.5 rounded border border-gray-200/60">
                {candidate.listing.producer.producer_type}
              </span>
            )}
          </div>

          <h4 className="font-bold text-base text-ink flex items-center space-x-1.5 pt-0.5">
            <UserCheck className="w-4 h-4 text-primary shrink-0" />
            <span>{candidate.listing.producer.org_name}</span>
          </h4>

          <div className="flex items-center space-x-1 text-xs text-muted">
            <MapPin className="w-3.5 h-3.5 text-gray-400 shrink-0" />
            <span>
              {candidate.listing.producer.district || 'Region'},{' '}
              {candidate.listing.producer.state || 'India'}
            </span>
          </div>
        </div>

        {/* Allocation status tag */}
        <div className="text-right">
          {candidate.allocated_kg > 0 ? (
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-1.5 text-right">
              <span className="text-[10px] uppercase font-bold text-emerald-800 block">
                Allocated
              </span>
              <span className="text-sm font-bold font-mono text-emerald-900">
                {candidate.allocated_kg.toLocaleString()} kg
              </span>
            </div>
          ) : (
            <div className="bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1 text-right">
              <span className="text-[10px] uppercase font-semibold text-gray-500 block">
                Available
              </span>
              <span className="text-xs font-semibold font-mono text-gray-700">
                {candidate.available_kg.toLocaleString()} kg
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Financials & Price Waterfall */}
      <div className="mt-4 bg-bg rounded-lg p-3.5 border border-gray-200/70 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div>
          <span className="text-muted block text-[11px]">Farmgate Ask</span>
          <span className="font-mono font-semibold text-ink">
            ₹{candidate.ask_price_per_kg.toFixed(2)}
          </span>
          <span className="text-[10px] text-muted">/kg</span>
        </div>

        <div>
          <span className="text-muted block text-[11px]">Est. Transport</span>
          <span className="font-mono font-semibold text-ink">
            +₹{candidate.transport_cost_per_kg.toFixed(2)}
          </span>
          <span className="text-[10px] text-muted">/kg</span>
        </div>

        <div>
          <span className="text-muted block text-[11px]">Platform Fee (2%)</span>
          <span className="font-mono font-semibold text-ink">
            +₹{candidate.platform_fee_per_kg.toFixed(2)}
          </span>
          <span className="text-[10px] text-muted">/kg</span>
        </div>

        <div className="bg-white/80 rounded p-1.5 border border-primary/20">
          <span className="text-primary font-bold block text-[11px]">LANDED PRICE</span>
          <span className="font-mono font-bold text-sm text-primary">
            ₹{candidate.landed_price_per_kg.toFixed(2)}
          </span>
          <span className="text-[10px] text-muted">/kg</span>
        </div>
      </div>

      {/* Transit & Freshness Metrics */}
      <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] text-muted border-t border-gray-100 pt-2.5">
        <div className="flex items-center space-x-1.5">
          <Truck className="w-3.5 h-3.5 text-gray-400 shrink-0" />
          <span>
            {candidate.distance_km} km ({candidate.transit_hours}h transit est.)
          </span>
        </div>

        <div className="flex items-center space-x-1.5 justify-end">
          <Clock className="w-3.5 h-3.5 text-gray-400 shrink-0" />
          <span>Harvest age: {candidate.age_at_delivery_days}d at delivery</span>
        </div>
      </div>

      {/* Deterministic Numerical Reasons */}
      {candidate.reasons && candidate.reasons.length > 0 && (
        <div className="mt-3.5 bg-sky-50/60 rounded-lg p-3 border border-sky-100 text-xs text-sky-900 space-y-1.5">
          <div className="font-semibold text-[11px] uppercase tracking-wider text-sky-800 flex items-center space-x-1">
            <Sparkles className="w-3 h-3 text-sky-600" />
            <span>Deterministic Match Factors</span>
          </div>
          <ul className="space-y-1">
            {candidate.reasons.map((r, idx) => (
              <li key={idx} className="flex items-start space-x-1.5 text-xs text-sky-950">
                <CheckCircle2 className="w-3.5 h-3.5 text-sky-600 shrink-0 mt-0.5" />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Expandable Score Breakdown */}
      <div className="mt-3 border-t border-gray-100 pt-2">
        <button
          type="button"
          onClick={() => setShowScoreDetails(!showScoreDetails)}
          className="w-full flex items-center justify-between text-xs text-muted hover:text-ink font-medium py-1 transition-colors"
        >
          <span>Score Breakdown ({(candidate.scores.total * 100).toFixed(1)}%)</span>
          {showScoreDetails ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </button>

        {showScoreDetails && (
          <div className="mt-2.5 p-3 bg-bg rounded-lg border border-gray-200">
            <ScoreBreakdown
              scores={candidate.scores}
              weights={candidate.weights}
              showWeights={true}
            />
          </div>
        )}
      </div>
    </div>
  );
};
