import React, { useEffect, useState } from 'react';
import { useAuth } from '../../lib/auth';
import { fetchListingOpportunitiesApi } from '../../api/matching';
import { ProducerOpportunitiesResponse } from '../../api/types';
import {
  AlertCircle,
  Building,
  CheckCircle2,
  MapPin,
  Sparkles,
  TrendingUp,
  X,
} from 'lucide-react';

interface ProducerOpportunitiesModalProps {
  listingId: number | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ProducerOpportunitiesModal: React.FC<ProducerOpportunitiesModalProps> = ({
  listingId,
  isOpen,
  onClose,
}) => {
  const { token } = useAuth();
  const [data, setData] = useState<ProducerOpportunitiesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && listingId && token) {
      loadOpportunities(listingId);
    } else {
      setData(null);
      setError(null);
    }
  }, [isOpen, listingId, token]);

  const loadOpportunities = async (id: number) => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchListingOpportunitiesApi(token, id);
      setData(res);
    } catch (err: any) {
      setError(err?.message || 'Failed to load buyer opportunities');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !listingId) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-surface rounded-2xl max-w-2xl w-full border border-gray-200 shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-base text-ink flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-primary" />
              <span>Matching Buyer Demands</span>
            </h3>
            <p className="text-xs text-muted mt-0.5">
              Open procurement requirements compatible with your produce lot #{listingId}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-ink hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-4">
          {loading && (
            <div className="py-12 text-center space-y-2">
              <span className="animate-spin inline-block w-6 h-6 border-2 border-primary border-t-transparent rounded-full" />
              <p className="text-xs text-muted">Finding compatible buyers...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {!loading && !error && data && (
            <>
              {/* Listing & Hub Forecast Context Header */}
              <div className="bg-bg rounded-xl p-4 border border-gray-200 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-sm text-ink">{data.listing.crop.name}</span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-primary-soft text-primary">
                      Grade {data.listing.grade}
                    </span>
                  </div>
                  <span className="font-mono text-xs font-semibold text-muted">
                    {data.listing.quantity_available_kg.toLocaleString()} kg available @ ₹
                    {data.listing.ask_price_per_kg.toFixed(2)}/kg
                  </span>
                </div>

                {data.hub_context && (
                  <div className="flex items-center justify-between pt-2 border-t border-gray-200/80 text-xs">
                    <div className="flex items-center space-x-1.5 text-muted">
                      <TrendingUp className="w-3.5 h-3.5 text-primary" />
                      <span>Regional Hub: {data.hub_context.hub.name}</span>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-muted text-[11px]">
                        7d Demand: {data.hub_context.forecast_7d_kg.toLocaleString()} kg
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          data.hub_context.status === 'SHORTAGE'
                            ? 'bg-rose-100 text-rose-800'
                            : data.hub_context.status === 'SURPLUS'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {data.hub_context.status}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Opportunities List */}
              <div className="space-y-3">
                <h4 className="font-bold text-xs text-ink uppercase tracking-wider">
                  Active Buyer Opportunities ({data.opportunities.length})
                </h4>

                {data.opportunities.length === 0 ? (
                  <div className="py-8 text-center bg-gray-50 rounded-xl border border-dashed border-gray-200 p-6 space-y-2">
                    <p className="text-xs font-semibold text-ink">No matching buyer requirements found</p>
                    <p className="text-[11px] text-muted max-w-sm mx-auto">
                      Currently there are no open buyer demands matching this crop and grade within the
                      300 km delivery radius.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {data.opportunities.map((opp) => (
                      <div
                        key={opp.requirement.id}
                        className="bg-surface rounded-xl border border-gray-200 p-4 shadow-xs space-y-3 hover:border-gray-300 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center space-x-2">
                              <Building className="w-4 h-4 text-primary shrink-0" />
                              <span className="font-bold text-sm text-ink">{opp.buyer.org_name}</span>
                              <span className="text-[10px] bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded font-medium">
                                {opp.buyer.buyer_type}
                              </span>
                            </div>
                            <div className="flex items-center space-x-1 text-xs text-muted mt-1">
                              <MapPin className="w-3.5 h-3.5 text-gray-400" />
                              <span>
                                {opp.buyer.city || 'City'}, {opp.buyer.state || 'State'} ·{' '}
                                {opp.distance_km} km away
                              </span>
                            </div>
                          </div>

                          <div className="text-right">
                            <span className="text-[10px] uppercase font-bold text-primary block">
                              Match Score
                            </span>
                            <span className="font-mono font-bold text-sm text-primary">
                              {(opp.scores.total * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>

                        {/* Quantity & Budget Details */}
                        <div className="grid grid-cols-3 gap-2 bg-bg p-2.5 rounded-lg border border-gray-200/60 text-xs">
                          <div>
                            <span className="text-muted block text-[10px]">Demanded Quantity</span>
                            <span className="font-mono font-semibold text-ink">
                              {opp.requirement.quantity_kg.toLocaleString()} kg
                            </span>
                          </div>

                          <div>
                            <span className="text-muted block text-[10px]">Max Landed Budget</span>
                            <span className="font-mono font-semibold text-ink">
                              ₹{opp.requirement.max_landed_price_per_kg.toFixed(2)}/kg
                            </span>
                          </div>

                          <div>
                            <span className="text-muted block text-[10px]">Needed By</span>
                            <span className="font-semibold text-ink">
                              {opp.requirement.needed_by}
                            </span>
                          </div>
                        </div>

                        {/* Numerical match reasons */}
                        {opp.reasons && opp.reasons.length > 0 && (
                          <div className="space-y-1 text-xs">
                            {opp.reasons.map((r, i) => (
                              <div key={i} className="flex items-start space-x-1.5 text-[11px] text-muted">
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                                <span>{r}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-gray-100 bg-gray-50 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-xs font-semibold text-ink hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
