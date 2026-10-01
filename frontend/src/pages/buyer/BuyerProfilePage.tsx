import React, { useEffect, useState } from 'react';
import { useAuth } from '../../lib/auth';
import { fetchBuyerProfileApi, updateBuyerProfileApi } from '../../api/profiles';
import { BuyerProfileOut } from '../../api/types';
import { Building2, MapPin, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

const HUBS = [
  { id: 1, name: 'Delhi North (Azadpur)' },
  { id: 2, name: 'Gurugram Central' },
  { id: 3, name: 'Noida Sector 62' },
  { id: 4, name: 'Ghaziabad Sahibabad' },
  { id: 5, name: 'Faridabad Industrial' },
];

export const BuyerProfilePage: React.FC = () => {
  const { token, user } = useAuth();
  const [profile, setProfile] = useState<BuyerProfileOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form fields
  const [orgName, setOrgName] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [hubId, setHubId] = useState<number>(1);
  const [lat, setLat] = useState<number>(28.47);
  const [lng, setLng] = useState<number>(77.05);

  const loadProfile = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchBuyerProfileApi(token);
      setProfile(data);
      setOrgName(data.org_name);
      setCity(data.city);
      setState(data.state);
      setHubId(data.hub_id);
      setLat(data.lat);
      setLng(data.lng);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load buyer profile');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setSaving(true);
    setError(null);
    setSuccess(null);

    // Validate coordinates
    if (lat < 6.0 || lat > 38.0) {
      setError('Latitude must be between 6.0 and 38.0 (India geographical bounding box).');
      setSaving(false);
      return;
    }
    if (lng < 68.0 || lng > 98.0) {
      setError('Longitude must be between 68.0 and 98.0 (India geographical bounding box).');
      setSaving(false);
      return;
    }

    try {
      const updated = await updateBuyerProfileApi(token, {
        org_name: orgName,
        city,
        state,
        hub_id: hubId,
        lat,
        lng,
      });
      setProfile(updated);
      setSuccess('Buyer profile updated successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between bg-surface rounded-xl border border-gray-200 p-6 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-ink">Buyer Organization Profile</h1>
            {profile?.is_demo && (
              <span className="text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full border border-amber-300">
                Demo Account
              </span>
            )}
          </div>
          <p className="text-sm text-muted mt-1">
            Registered commercial buyer and demand coordination node for regional intake.
          </p>
        </div>

        <button
          onClick={loadProfile}
          disabled={loading}
          className="p-2 border border-gray-200 rounded-lg text-muted hover:text-ink hover:bg-gray-50 transition-colors"
          title="Reload profile"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-800 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Update failed</p>
            <p className="text-xs mt-0.5 text-rose-700">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-sm text-emerald-800 flex items-start space-x-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Success</p>
            <p className="text-xs mt-0.5 text-emerald-700">{success}</p>
          </div>
        </div>
      )}

      {/* Profile Form */}
      {loading && !profile ? (
        <div className="bg-surface rounded-xl border border-gray-200 p-8 text-center text-muted">
          Loading profile...
        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          className="bg-surface rounded-xl border border-gray-200 p-6 shadow-xs space-y-5"
        >
          {/* Readonly Overview Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-3.5 bg-bg rounded-lg border border-gray-200 text-xs">
            <div>
              <span className="text-muted block text-[11px]">Buyer Type</span>
              <span className="font-bold text-ink inline-flex items-center space-x-1 mt-0.5">
                <Building2 className="w-3.5 h-3.5 text-primary" />
                <span>{profile?.buyer_type}</span>
              </span>
            </div>

            <div>
              <span className="text-muted block text-[11px]">Account Email</span>
              <span className="font-semibold text-ink mt-0.5 block truncate">
                {user?.email}
              </span>
            </div>

            <div>
              <span className="text-muted block text-[11px]">Profile ID</span>
              <span className="font-mono text-ink mt-0.5 block">
                #{profile?.id}
              </span>
            </div>
          </div>

          {/* Org Name */}
          <div>
            <label className="block text-xs font-semibold text-ink mb-1">
              Organization Name
            </label>
            <input
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              required
              minLength={2}
              maxLength={255}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>

          {/* Regional Demand Hub */}
          <div>
            <label className="block text-xs font-semibold text-ink mb-1">
              Assigned Demand Hub (Intake Terminal)
            </label>
            <select
              value={hubId}
              onChange={(e) => setHubId(parseInt(e.target.value, 10))}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            >
              {HUBS.map((h) => (
                <option key={h.id} value={h.id}>
                  Hub #{h.id}: {h.name}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-muted mt-1">
              Haulage logistics and regional cluster matching calculate delivery distances against this hub.
            </p>
          </div>

          {/* City & State */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-ink mb-1">City</label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                required
                minLength={2}
                maxLength={100}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-ink mb-1">State</label>
              <input
                type="text"
                value={state}
                onChange={(e) => setState(e.target.value)}
                required
                minLength={2}
                maxLength={100}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
          </div>

          {/* Geo Coordinates */}
          <div>
            <div className="flex items-center space-x-1.5 text-xs font-semibold text-ink mb-1.5">
              <MapPin className="w-3.5 h-3.5 text-primary" />
              <span>Receiving Facility Coordinates (Lat / Lng)</span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] text-muted mb-1">
                  Latitude (6.0 to 38.0)
                </label>
                <input
                  type="number"
                  step="0.0001"
                  min="6.0"
                  max="38.0"
                  value={lat}
                  onChange={(e) => setLat(parseFloat(e.target.value) || 0)}
                  required
                  className="w-full px-3 py-2 text-sm font-mono border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                />
              </div>

              <div>
                <label className="block text-[11px] text-muted mb-1">
                  Longitude (68.0 to 98.0)
                </label>
                <input
                  type="number"
                  step="0.0001"
                  min="68.0"
                  max="98.0"
                  value={lng}
                  onChange={(e) => setLng(parseFloat(e.target.value) || 0)}
                  required
                  className="w-full px-3 py-2 text-sm font-mono border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                />
              </div>
            </div>
            <p className="text-[11px] text-muted mt-1.5">
              Strictly validated to lie within the continental bounds of India.
            </p>
          </div>

          {/* Submit */}
          <div className="flex justify-end pt-4 border-t border-gray-100">
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center space-x-2 bg-primary hover:bg-primary-hover text-white text-xs font-bold px-5 py-2.5 rounded-lg shadow-xs disabled:opacity-50 transition-colors"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{saving ? 'Saving Changes...' : 'Save Profile Changes'}</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
