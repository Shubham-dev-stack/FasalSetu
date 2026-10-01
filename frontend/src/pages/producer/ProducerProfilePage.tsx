import React, { useEffect, useState } from 'react';
import { useAuth } from '../../lib/auth';
import { fetchProducerProfileApi, updateProducerProfileApi } from '../../api/profiles';
import { ProducerProfileOut } from '../../api/types';
import { Building2, Users, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';


export const ProducerProfilePage: React.FC = () => {
  const { token, user } = useAuth();
  const [profile, setProfile] = useState<ProducerProfileOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form fields
  const [orgName, setOrgName] = useState('');
  const [state, setState] = useState('');
  const [district, setDistrict] = useState('');
  const [locality, setLocality] = useState('');
  const [lat, setLat] = useState<number>(28.99);
  const [lng, setLng] = useState<number>(77.02);
  const [memberFarmers, setMemberFarmers] = useState<number | ''>('');

  const loadProfile = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProducerProfileApi(token);
      setProfile(data);
      setOrgName(data.org_name);
      setState(data.state);
      setDistrict(data.district);
      setLocality(data.locality || '');
      setLat(data.lat);
      setLng(data.lng);
      setMemberFarmers(data.member_farmers ?? '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load producer profile');
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

    try {
      const updated = await updateProducerProfileApi(token, {
        org_name: orgName,
        state,
        district,
        locality: locality.trim() ? locality.trim() : null,
        lat,
        lng,
        member_farmers: profile?.producer_type === 'FPO' && memberFarmers !== '' ? Number(memberFarmers) : undefined,
      });
      setProfile(updated);
      setSuccess('Profile updated successfully.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-surface rounded-xl border border-gray-200 p-8 text-center text-xs text-muted">
        <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-primary" />
        <span>Loading producer profile...</span>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header Card */}
      <div className="bg-surface rounded-xl border border-gray-200 p-6 shadow-xs flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-primary-soft text-primary flex items-center justify-center font-bold">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-ink">{profile?.org_name}</h1>
            <p className="text-xs text-muted">
              {profile?.producer_type} Producer · {user?.email}
            </p>
          </div>
        </div>

        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-primary-soft text-primary">
          {profile?.producer_type}
        </span>
      </div>

      {/* Form Container */}
      <div className="bg-surface rounded-xl border border-gray-200 p-6 shadow-xs space-y-5">
        <h2 className="text-sm font-bold text-ink border-b border-gray-100 pb-3">
          Organization & Geographic Details
        </h2>

        {error && (
          <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-start space-x-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-600" />
            <span>{success}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-ink mb-1">
              Organization / Farmer Display Name *
            </label>
            <input
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              required
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-ink mb-1">State *</label>
              <input
                type="text"
                value={state}
                onChange={(e) => setState(e.target.value)}
                required
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-ink mb-1">District *</label>
              <input
                type="text"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                required
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink mb-1">
              Locality / Village / Mandi Vicinity
            </label>
            <input
              type="text"
              value={locality}
              onChange={(e) => setLocality(e.target.value)}
              placeholder="e.g. Rai Industrial Estate / Grain Market Rd"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-ink mb-1">
                Latitude (India 6° to 38°) *
              </label>
              <input
                type="number"
                step="0.0001"
                min="6.0"
                max="38.0"
                value={lat}
                onChange={(e) => setLat(parseFloat(e.target.value) || 0)}
                required
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-ink mb-1">
                Longitude (India 68° to 98°) *
              </label>
              <input
                type="number"
                step="0.0001"
                min="68.0"
                max="98.0"
                value={lng}
                onChange={(e) => setLng(parseFloat(e.target.value) || 0)}
                required
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary font-mono"
              />
            </div>
          </div>

          {profile?.producer_type === 'FPO' && (
            <div>
              <label className="block text-xs font-semibold text-ink mb-1">
                Member Farmers Count
              </label>
              <div className="relative">
                <Users className="w-4 h-4 text-muted absolute left-3 top-2.5" />
                <input
                  type="number"
                  min="1"
                  value={memberFarmers}
                  onChange={(e) => setMemberFarmers(e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                  placeholder="Total registered farmers in collective"
                  className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary font-mono"
                />
              </div>
            </div>
          )}

          <div className="pt-4 border-t border-gray-100 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="bg-primary hover:bg-primary-hover text-white text-xs font-bold px-6 py-2.5 rounded-lg shadow-sm disabled:opacity-50 transition-colors"
            >
              {saving ? 'Updating...' : 'Save Profile Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
