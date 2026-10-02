import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import {
  fetchRequirementCandidatesApi,
  acceptMatchingAllocationApi,
} from '../../api/matching';
import { MatchingCandidatesResponse } from '../../api/types';
import { CandidateCard } from '../../components/domain/CandidateCard';
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  XCircle,
} from 'lucide-react';

export const MatchPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token } = useAuth();

  const [data, setData] = useState<MatchingCandidatesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deliveryDate, setDeliveryDate] = useState<string>('');
  const [accepting, setAccepting] = useState(false);
  const [acceptError, setAcceptError] = useState<string | null>(null);
  const [showNearMisses, setShowNearMisses] = useState(false);

  useEffect(() => {
    if (!token || !id) return;
    loadCandidates();
  }, [token, id]);

  const loadCandidates = async () => {
    if (!token || !id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchRequirementCandidatesApi(token, Number(id));
      setData(res);

      // Default delivery date to earliest feasible delivery date or needed_by
      if (res.earliest_delivery_date) {
        setDeliveryDate(res.earliest_delivery_date);
      } else if (res.requirement.needed_by) {
        setDeliveryDate(res.requirement.needed_by);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load matching candidates');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptAllocation = async () => {
    if (!token || !data || !id) return;
    if (data.allocations.length === 0) return;

    setAccepting(true);
    setAcceptError(null);
    try {
      await acceptMatchingAllocationApi(token, {
        requirement_id: Number(id),
        allocations: data.allocations,
        delivery_date: deliveryDate,
      });
      // Redirect to orders page on success
      navigate('/orders');
    } catch (err: any) {
      setAcceptError(err?.message || 'Failed to accept allocation');
    } finally {
      setAccepting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/4" />
          <div className="h-28 bg-gray-200 rounded-xl" />
          <div className="h-64 bg-gray-200 rounded-xl" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <Link
          to="/buyer/requirements"
          className="inline-flex items-center space-x-1.5 text-xs text-muted hover:text-ink font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Requirements</span>
        </Link>

        <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 space-y-3">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <h3 className="font-bold text-sm">Unable to compute matching</h3>
          </div>
          <p className="text-xs text-rose-700">{error || 'Unknown error occurred'}</p>
          <button
            type="button"
            onClick={loadCandidates}
            className="px-4 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-semibold hover:bg-rose-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const { requirement, fill_status, fulfilled_kg, shortfall_kg, candidates, near_misses } =
    data;
  const percentFulfilled =
    requirement.quantity_kg > 0
      ? Math.round((fulfilled_kg / requirement.quantity_kg) * 100)
      : 0;

  // Calculate total estimated landed amount for allocated lots
  const totalAllocatedAmount = candidates.reduce((sum, c) => {
    return sum + (c.allocated_kg > 0 ? c.allocated_kg * c.landed_price_per_kg : 0);
  }, 0);

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-24">
      {/* Navigation header */}
      <div className="flex items-center justify-between">
        <Link
          to="/buyer/requirements"
          className="inline-flex items-center space-x-1.5 text-xs text-muted hover:text-ink font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Requirements</span>
        </Link>

        <span className="text-xs text-muted">
          Requirement #{requirement.id} · {requirement.crop.name}
        </span>
      </div>

      {/* Requirement Summary Card */}
      <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-ink">{requirement.crop.name}</h2>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-primary-soft text-primary uppercase">
                Min Grade {requirement.grade_min}
              </span>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${
                  fill_status === 'FULL'
                    ? 'bg-emerald-100 text-emerald-800'
                    : fill_status === 'PARTIAL'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-rose-100 text-rose-800'
                }`}
              >
                {fill_status === 'FULL' && '100% Fully Matched'}
                {fill_status === 'PARTIAL' && 'Partially Matched'}
                {fill_status === 'NONE' && 'No Eligible Match'}
              </span>
            </div>
            <p className="text-xs text-muted mt-1">
              Deterministic allocation engine evaluating hard filters F1–F6 & multi-factor scoring
            </p>
          </div>

          <div className="flex items-center space-x-4 text-xs font-mono">
            <div>
              <span className="text-muted block text-[11px]">Max Budget</span>
              <span className="font-bold text-ink">
                ₹{requirement.max_landed_price_per_kg.toFixed(2)}/kg
              </span>
            </div>
            <div>
              <span className="text-muted block text-[11px]">Needed By</span>
              <span className="font-semibold text-ink">{requirement.needed_by}</span>
            </div>
          </div>
        </div>

        {/* Allocation progress bar */}
        <div className="space-y-1.5 pt-2 border-t border-gray-100">
          <div className="flex justify-between text-xs">
            <span className="text-muted font-medium">Supply Allocation</span>
            <span className="font-mono font-semibold text-ink">
              {fulfilled_kg.toLocaleString()} / {requirement.quantity_kg.toLocaleString()} kg (
              {percentFulfilled}%)
            </span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
            <div
              className={`h-2.5 rounded-full transition-all duration-300 ${
                fill_status === 'FULL'
                  ? 'bg-emerald-500'
                  : fill_status === 'PARTIAL'
                  ? 'bg-amber-500'
                  : 'bg-rose-400'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, percentFulfilled))}%` }}
            />
          </div>
        </div>

        {/* Shortfall banner if partial or none */}
        {shortfall_kg > 0 && (
          <div
            className={`p-3.5 rounded-lg border text-xs flex items-start space-x-2.5 ${
              fill_status === 'PARTIAL'
                ? 'bg-amber-50 border-amber-200 text-amber-900'
                : 'bg-rose-50 border-rose-200 text-rose-900'
            }`}
          >
            <AlertTriangle
              className={`w-4 h-4 shrink-0 mt-0.5 ${
                fill_status === 'PARTIAL' ? 'text-amber-600' : 'text-rose-600'
              }`}
            />
            <div>
              <span className="font-bold">
                {fill_status === 'PARTIAL'
                  ? `Shortfall of ${shortfall_kg.toLocaleString()} kg`
                  : 'No supply lots fit your requirements'}
              </span>
              <p className="mt-0.5 text-[11px] opacity-90">
                {fill_status === 'PARTIAL'
                  ? `Allocated ${fulfilled_kg.toLocaleString()} kg across available eligible lots. No further unreserved produce lots meet your budget, grade, and radius criteria.`
                  : `None of the active produce lots meet your max landed budget of ₹${requirement.max_landed_price_per_kg.toFixed(
                      2
                    )}/kg, grade minimum, or delivery distance.`}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Ranked Candidates Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-base text-ink flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-primary" />
            <span>Matched Produce Lots ({candidates.length})</span>
          </h3>
          <span className="text-xs text-muted">
            Sorted by total score with deterministic tie-breaking
          </span>
        </div>

        {candidates.length === 0 ? (
          <div className="bg-surface rounded-xl border border-dashed border-gray-300 p-10 text-center space-y-3">
            <XCircle className="w-10 h-10 text-gray-400 mx-auto" />
            <h4 className="font-bold text-sm text-ink">No eligible candidates found</h4>
            <p className="text-xs text-muted max-w-md mx-auto">
              No active listings satisfy all hard filters (Grade {requirement.grade_min}+, budget ₹
              {requirement.max_landed_price_per_kg.toFixed(2)}, max distance 300 km). Review near misses
              below for detailed gap diagnostics.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {candidates.map((cand) => (
              <CandidateCard
                key={cand.listing.id}
                candidate={cand}
                isAllocated={cand.allocated_kg > 0}
              />
            ))}
          </div>
        )}
      </div>

      {/* Near Misses Diagnostic Accordion */}
      {near_misses.length > 0 && (
        <div className="bg-surface rounded-xl border border-gray-200 overflow-hidden shadow-xs">
          <button
            type="button"
            onClick={() => setShowNearMisses(!showNearMisses)}
            className="w-full p-4 flex items-center justify-between bg-gray-50/70 hover:bg-gray-100/70 text-left transition-colors"
          >
            <div className="flex items-center space-x-2">
              <span className="font-bold text-xs text-ink">
                Near-Miss Excluded Lots ({near_misses.length})
              </span>
              <span className="text-[11px] text-muted">
                — lots excluded by hard filters (F1–F6)
              </span>
            </div>
            {showNearMisses ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </button>

          {showNearMisses && (
            <div className="p-4 divide-y divide-gray-100 text-xs">
              {near_misses.map((nm, idx) => (
                <div key={idx} className="py-2.5 first:pt-0 last:pb-0 flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-semibold text-ink">Listing #{nm.listing_id}</span>
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">
                        {nm.excluded_reason}
                      </span>
                    </div>
                    <p className="text-[11px] text-muted">{nm.detail}</p>
                  </div>

                  <div className="text-right text-[11px] font-mono shrink-0">
                    {nm.landed_price_per_kg && (
                      <span className="text-ink block">
                        Landed: ₹{nm.landed_price_per_kg.toFixed(2)}/kg
                      </span>
                    )}
                    {nm.distance_km && (
                      <span className="text-muted block">{nm.distance_km.toFixed(1)} km</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Accept Allocation Error Banner */}
      {acceptError && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <span>{acceptError}</span>
        </div>
      )}

      {/* Sticky Bottom Action Footer */}
      {data.allocations.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-surface/95 backdrop-blur-md border-t border-gray-200 p-4 shadow-lg z-30">
          <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center space-x-6 text-xs w-full sm:w-auto justify-between sm:justify-start">
              <div>
                <span className="text-muted block text-[11px]">Allocated Produce</span>
                <span className="font-bold text-sm font-mono text-ink">
                  {fulfilled_kg.toLocaleString()} kg
                </span>
                <span className="text-[11px] text-muted ml-1">
                  ({data.allocations.length} lot{data.allocations.length === 1 ? '' : 's'})
                </span>
              </div>

              <div>
                <span className="text-muted block text-[11px]">Est. Total Landed Amount</span>
                <span className="font-bold text-sm font-mono text-primary">
                  ₹{totalAllocatedAmount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-gray-400" />
                <div>
                  <span className="text-muted block text-[11px]">Delivery Date</span>
                  <input
                    type="date"
                    value={deliveryDate}
                    max={requirement.needed_by}
                    onChange={(e) => setDeliveryDate(e.target.value)}
                    className="border border-gray-300 rounded px-2 py-0.5 text-xs font-mono font-medium focus:ring-1 focus:ring-primary focus:border-primary outline-hidden"
                  />
                </div>
              </div>
            </div>

            <button
              type="button"
              disabled={accepting || !deliveryDate}
              onClick={handleAcceptAllocation}
              className="w-full sm:w-auto px-6 py-2.5 bg-primary text-white rounded-lg text-xs font-bold hover:bg-primary-hover disabled:opacity-50 transition-all flex items-center justify-center space-x-2 shadow-xs"
            >
              {accepting ? (
                <>
                  <span className="animate-spin inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full" />
                  <span>Accepting & Creating Orders...</span>
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  <span>Accept Allocation ({data.allocations.length} Orders)</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
