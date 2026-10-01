import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import { createListingApi } from '../../api/listings';
import { DemandPanel } from '../../components/domain/DemandPanel';
import { ArrowLeft, AlertTriangle, CheckCircle2, AlertCircle } from 'lucide-react';

const CROPS = [
  { id: 1, name: 'Tomato', shelfLife: 7, basePrice: 22.50, isHighPerish: true },
  { id: 2, name: 'Onion', shelfLife: 60, basePrice: 21.50, isHighPerish: false },
  { id: 3, name: 'Potato', shelfLife: 60, basePrice: 17.50, isHighPerish: false },
  { id: 4, name: 'Cauliflower', shelfLife: 5, basePrice: 27.50, isHighPerish: true },
  { id: 5, name: 'Green Chilli', shelfLife: 7, basePrice: 45.00, isHighPerish: true },
];

export const NewListingPage: React.FC = () => {
  const navigate = useNavigate();
  const { token } = useAuth();

  const getTodayStr = () => new Date().toISOString().split('T')[0];
  const getDateOffsetStr = (days: number) => {
    const d = new Date();
    d.setDate(d.getDate() + days);
    return d.toISOString().split('T')[0];
  };

  const [cropId, setCropId] = useState<number>(1);
  const [variety, setVariety] = useState<string>('');
  const [grade, setGrade] = useState<'A' | 'B' | 'C'>('A');
  const [quantity, setQuantity] = useState<number>(1000);
  const [minOrder, setMinOrder] = useState<number>(100);
  const [askPrice, setAskPrice] = useState<number>(24.0);
  const [harvestDate, setHarvestDate] = useState<string>(getTodayStr());
  const [availableFrom, setAvailableFrom] = useState<string>(getTodayStr());
  const [availableUntil, setAvailableUntil] = useState<string>(getDateOffsetStr(4));

  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);

  const selectedCrop = CROPS.find((c) => c.id === cropId) || CROPS[0];
  const benchmarkModal = selectedCrop.basePrice;
  const isHighAboveBenchmark = askPrice > 3 * benchmarkModal;

  const handleCropChange = (id: number) => {
    setCropId(id);
    const chosen = CROPS.find((c) => c.id === id);
    if (chosen) {
      setAskPrice(chosen.basePrice);
      setAvailableUntil(getDateOffsetStr(chosen.isHighPerish ? 4 : 10));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setError(null);
    setWarning(null);

    if (minOrder > quantity) {
      setError('Minimum order volume cannot exceed total lot volume.');
      return;
    }
    if (availableUntil < availableFrom) {
      setError('available_until cannot be earlier than available_from.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await createListingApi(token, {
        crop_id: cropId,
        variety: variety.trim() ? variety.trim() : null,
        grade,
        quantity_kg: quantity,
        min_order_kg: minOrder,
        ask_price_per_kg: askPrice,
        harvest_date: harvestDate,
        available_from: availableFrom,
        available_until: availableUntil,
      });

      if (res.warnings && res.warnings.length > 0) {
        setWarning(`Note: ${res.warnings.join(', ')}`);
      }

      // Small success pause then redirect
      setTimeout(() => {
        navigate('/producer/listings');
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create produce listing');
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Title */}
      <div className="flex items-center space-x-3">
        <button
          onClick={() => navigate('/producer/listings')}
          className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50 text-muted transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-ink">Publish New Produce Lot</h1>
          <p className="text-xs text-muted">
            Provide harvest specs, grade quality, and minimum order parameters.
          </p>
        </div>
      </div>

      {/* Main Grid: Form on Left (60%), Demand Panel on Right (40%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Form Container */}
        <div className="lg:col-span-7 bg-surface rounded-xl border border-gray-200 p-6 shadow-xs space-y-6">
          {error && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
              <span>{error}</span>
            </div>
          )}

          {warning && (
            <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-600" />
              <span>{warning}</span>
            </div>
          )}


          {isHighAboveBenchmark && (
            <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-600" />
              <div>
                <strong>Price sanity notice:</strong> Ask price ₹{askPrice}/kg is more than 3× the
                nearest benchmark modal price (₹{benchmarkModal}/kg). It will be accepted with warning{' '}
                <code>PRICE_FAR_ABOVE_BENCHMARK</code>.
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Crop Selection */}
            <div>
              <label className="block text-xs font-bold text-ink mb-2 uppercase tracking-wide">
                Select Crop Commodity *
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {CROPS.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => handleCropChange(c.id)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      cropId === c.id
                        ? 'border-primary bg-primary-soft/40 shadow-xs'
                        : 'border-gray-200 hover:border-gray-300 bg-bg'
                    }`}
                  >
                    <div className="font-bold text-xs text-ink">{c.name}</div>
                    <div className="text-[11px] text-muted mt-0.5">
                      Shelf: {c.shelfLife}d · ₹{c.basePrice}/kg
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Grade Selection */}
            <div>
              <label className="block text-xs font-bold text-ink mb-2 uppercase tracking-wide">
                Produce Grade *
              </label>
              <div className="grid grid-cols-3 gap-3">
                {(['A', 'B', 'C'] as const).map((g) => (
                  <button
                    key={g}
                    type="button"
                    onClick={() => setGrade(g)}
                    className={`py-2 px-3 rounded-lg border text-center text-xs font-bold transition-all ${
                      grade === g
                        ? 'border-primary bg-primary text-white shadow-xs'
                        : 'border-gray-200 hover:bg-gray-50 text-ink bg-bg'
                    }`}
                  >
                    Grade {g}
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-muted mt-1">
                Grade A: Premium wholesale · Grade B: Standard retail · Grade C: Processing/Sauce
              </p>
            </div>

            {/* Variety (Optional) */}
            <div>
              <label className="block text-xs font-semibold text-ink mb-1">
                Cultivar / Variety (Optional)
              </label>
              <input
                type="text"
                value={variety}
                onChange={(e) => setVariety(e.target.value)}
                placeholder="e.g. Desi, Hybrid, Pusa Ruby"
                maxLength={100}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>

            {/* Quantities: Total & Min Order */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-ink mb-1">
                  Total Lot Volume (kg) *
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="10"
                    min="1"
                    max="100000"
                    value={quantity}
                    onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
                    required
                    className="w-full pl-3 pr-10 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary font-mono"
                  />
                  <span className="absolute right-3 top-2.5 text-xs text-muted">kg</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink mb-1">
                  Minimum Order (kg) *
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="10"
                    min="1"
                    max={quantity}
                    value={minOrder}
                    onChange={(e) => setMinOrder(parseFloat(e.target.value) || 0)}
                    required
                    className="w-full pl-3 pr-10 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary font-mono"
                  />
                  <span className="absolute right-3 top-2.5 text-xs text-muted">kg</span>
                </div>
              </div>
            </div>

            {/* Ask Price */}
            <div>
              <label className="block text-xs font-semibold text-ink mb-1">
                Producer Ask Price (₹/kg) *
              </label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-sm text-muted">₹</span>
                <input
                  type="number"
                  step="0.25"
                  min="0.5"
                  max="100000"
                  value={askPrice}
                  onChange={(e) => setAskPrice(parseFloat(e.target.value) || 0)}
                  required
                  className="w-full pl-8 pr-12 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary font-mono font-bold"
                />
                <span className="absolute right-3 top-2.5 text-xs text-muted">/ kg</span>
              </div>
              <p className="text-[11px] text-muted mt-1">
                Modelled APMC benchmark: ₹{benchmarkModal.toFixed(2)}/kg
              </p>
            </div>

            {/* Dates: Harvest & Availability */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Harvest Date *</label>
                <input
                  type="date"
                  value={harvestDate}
                  max={getTodayStr()}
                  onChange={(e) => setHarvestDate(e.target.value)}
                  required
                  className="w-full px-2.5 py-2 text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Available From *</label>
                <input
                  type="date"
                  value={availableFrom}
                  onChange={(e) => setAvailableFrom(e.target.value)}
                  required
                  className="w-full px-2.5 py-2 text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink mb-1">Available Until *</label>
                <input
                  type="date"
                  value={availableUntil}
                  min={availableFrom}
                  onChange={(e) => setAvailableUntil(e.target.value)}
                  required
                  className="w-full px-2.5 py-2 text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="pt-4 border-t border-gray-100 flex items-center justify-between">
              <button
                type="button"
                onClick={() => navigate('/producer/listings')}
                disabled={submitting}
                className="text-xs font-medium text-muted hover:text-ink px-4 py-2"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={submitting || quantity <= 0 || askPrice <= 0}
                className="inline-flex items-center space-x-1.5 bg-primary hover:bg-primary-hover text-white text-xs font-bold px-6 py-2.5 rounded-lg shadow-sm disabled:opacity-50 transition-colors"
              >
                {submitting ? (
                  <span>Publishing Lot...</span>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Publish Produce Lot</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Right Side: Demand Panel & Benchmark Context */}
        <div className="lg:col-span-5 space-y-4">
          <DemandPanel
            cropId={selectedCrop.id}
            cropName={selectedCrop.name}
            approxBenchmarkModal={benchmarkModal}
          />
        </div>
      </div>
    </div>
  );
};
