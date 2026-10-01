import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import { createRequirementApi } from '../../api/requirements';
import { ArrowLeft, CheckCircle2, AlertCircle, Info, Calculator } from 'lucide-react';

const CROPS = [
  { id: 1, name: 'Tomato', basePrice: 22.50, unit: 'kg' },
  { id: 2, name: 'Onion', basePrice: 21.50, unit: 'kg' },
  { id: 3, name: 'Potato', basePrice: 17.50, unit: 'kg' },
  { id: 4, name: 'Cauliflower', basePrice: 27.50, unit: 'kg' },
  { id: 5, name: 'Green Chilli', basePrice: 45.00, unit: 'kg' },
];

export const NewRequirementPage: React.FC = () => {
  const navigate = useNavigate();
  const { token } = useAuth();

  const getTodayStr = () => new Date().toISOString().split('T')[0];
  const getDateOffsetStr = (days: number) => {
    const d = new Date();
    d.setDate(d.getDate() + days);
    return d.toISOString().split('T')[0];
  };

  const [cropId, setCropId] = useState<number>(1);
  const [gradeMin, setGradeMin] = useState<'A' | 'B' | 'C'>('B');
  const [quantity, setQuantity] = useState<number>(1500);
  const [maxPrice, setMaxPrice] = useState<number>(29.0);
  const [neededBy, setNeededBy] = useState<string>(getDateOffsetStr(2));
  const [notes, setNotes] = useState<string>('');

  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const selectedCrop = CROPS.find((c) => c.id === cropId) || CROPS[0];

  const handleCropChange = (id: number) => {
    setCropId(id);
    const chosen = CROPS.find((c) => c.id === id);
    if (chosen) {
      // Suggest indicative landed price ~20-25% above reference farmgate
      setMaxPrice(Math.round((chosen.basePrice * 1.25) * 2) / 2);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setError(null);

    const todayStr = getTodayStr();
    if (neededBy < todayStr) {
      setError('Needed By date cannot be in the past.');
      return;
    }
    if (quantity <= 0) {
      setError('Required quantity must be greater than zero.');
      return;
    }
    if (maxPrice <= 0) {
      setError('Max landed price must be greater than zero.');
      return;
    }

    setSubmitting(true);
    try {
      await createRequirementApi(token, {
        crop_id: cropId,
        grade_min: gradeMin,
        quantity_kg: quantity,
        max_landed_price_per_kg: maxPrice,
        needed_by: neededBy,
        notes: notes.trim() || null,
      });
      navigate('/buyer/requirements');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to post requirement');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back Button & Title */}
      <div>
        <button
          onClick={() => navigate('/buyer/requirements')}
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-muted hover:text-ink mb-3 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Requirements</span>
        </button>

        <h1 className="text-xl font-bold text-ink">Post Procurement Requirement</h1>
        <p className="text-sm text-muted mt-1">
          Specify commodity volume, quality requirements, and maximum landed price budget for regional matching.
        </p>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-800 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Submission failed</p>
            <p className="text-xs mt-0.5 text-rose-700">{error}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form Column */}
        <div className="lg:col-span-2">
          <form
            onSubmit={handleSubmit}
            className="bg-surface rounded-xl border border-gray-200 p-6 shadow-xs space-y-5"
          >
            {/* Crop Selector */}
            <div>
              <label className="block text-xs font-semibold text-ink mb-1.5">
                Target Crop / Commodity
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {CROPS.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => handleCropChange(c.id)}
                    className={`py-2 px-3 text-xs font-medium rounded-lg border text-left transition-all ${
                      cropId === c.id
                        ? 'bg-primary-soft border-primary text-primary font-bold shadow-xs'
                        : 'border-gray-200 hover:border-gray-300 text-ink bg-white'
                    }`}
                  >
                    <div>{c.name}</div>
                    <div className="text-[10px] text-muted font-normal mt-0.5">
                      Ref ~₹{c.basePrice}/kg
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Minimum Grade */}
            <div>
              <label className="block text-xs font-semibold text-ink mb-1.5">
                Minimum Acceptable Quality Grade
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'A', title: 'Grade A', desc: 'Premium, uniform size, zero blemishes' },
                  { id: 'B', title: 'Grade B', desc: 'Standard market grade, commercial standard' },
                  { id: 'C', title: 'Grade C', desc: 'Processing / canning grade, value lot' },
                ].map((g) => (
                  <label
                    key={g.id}
                    className={`border rounded-lg p-3 cursor-pointer text-left transition-all flex flex-col justify-between ${
                      gradeMin === g.id
                        ? 'border-primary bg-primary-soft/30 text-ink ring-1 ring-primary'
                        : 'border-gray-200 hover:border-gray-300 text-muted'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-xs text-ink">{g.title}</span>
                      <input
                        type="radio"
                        name="gradeMin"
                        value={g.id}
                        checked={gradeMin === g.id}
                        onChange={() => setGradeMin(g.id as 'A' | 'B' | 'C')}
                        className="text-primary focus:ring-primary h-3.5 w-3.5"
                      />
                    </div>
                    <p className="text-[11px] leading-tight text-muted">{g.desc}</p>
                  </label>
                ))}
              </div>
            </div>

            {/* Quantity and Price */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-ink mb-1">
                  Required Volume (kg)
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="50"
                    min="1"
                    max="100000"
                    value={quantity}
                    onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
                    required
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                  />
                  <span className="absolute right-3 top-2 text-xs text-muted">kg</span>
                </div>
              </div>

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
                    max="100000"
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(parseFloat(e.target.value) || 0)}
                    required
                    className="w-full pl-8 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                  />
                </div>
              </div>
            </div>

            {/* Needed By Date */}
            <div>
              <label className="block text-xs font-semibold text-ink mb-1">
                Needed By Date (Delivery Deadline)
              </label>
              <input
                type="date"
                min={getTodayStr()}
                value={neededBy}
                onChange={(e) => setNeededBy(e.target.value)}
                required
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
              <p className="text-[11px] text-muted mt-1">
                Requirements past this date without fulfillment dynamically expire (Rule D-021).
              </p>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-xs font-semibold text-ink mb-1">
                Procurement Notes (Optional)
              </label>
              <textarea
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. Preferred morning dock delivery, crates packaging, specific moisture level"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>

            {/* Action buttons */}
            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-100">
              <button
                type="button"
                onClick={() => navigate('/buyer/requirements')}
                disabled={submitting}
                className="px-4 py-2 border border-gray-300 rounded-lg text-xs font-semibold text-ink hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center space-x-1.5 bg-primary hover:bg-primary-hover text-white text-xs font-bold px-5 py-2.5 rounded-lg shadow-xs disabled:opacity-50 transition-colors"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>{submitting ? 'Broadcasting...' : 'Publish Requirement'}</span>
              </button>
            </div>
          </form>
        </div>

        {/* Educational Guidance Column */}
        <div className="space-y-5">
          {/* Landed Price Guidance Box */}
          <div className="bg-surface rounded-xl border border-gray-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center space-x-2 text-ink">
              <Calculator className="w-4 h-4 text-primary" />
              <h3 className="text-xs font-bold uppercase tracking-wider">
                Landed Price Architecture
              </h3>
            </div>

            <div className="bg-bg rounded-lg p-3 border border-gray-200 text-xs font-mono text-ink/90 leading-relaxed">
              max_landed_price &ge; farmgate_ask + transport_cost + platform_fee (2%)
            </div>

            <div className="space-y-2 text-xs text-muted">
              <div className="flex items-start space-x-2">
                <Info className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                <p>
                  <strong>Includes farmgate ask + transport + 2% platform fee.</strong>
                </p>
              </div>
              <p>
                When multi-source matching runs in Phase 7, candidate producer listings must have
                their farmgate ask plus haulage and platform fee fit comfortably inside your landed budget.
              </p>
            </div>

            <div className="border-t border-gray-100 pt-3 text-xs space-y-1.5">
              <div className="flex justify-between text-muted">
                <span>Selected Crop:</span>
                <span className="font-semibold text-ink">{selectedCrop.name}</span>
              </div>
              <div className="flex justify-between text-muted">
                <span>Approx. Market Benchmark:</span>
                <span className="font-semibold text-ink">₹{selectedCrop.basePrice.toFixed(2)}/kg</span>
              </div>
              <div className="flex justify-between text-muted">
                <span>Total Budget Estimate:</span>
                <span className="font-semibold text-ink font-mono">
                  ₹{(quantity * maxPrice).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
