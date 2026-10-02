import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import { DEMO_PERSONAS, DemoPersona } from '../../api/types';

export const LoginPage: React.FC = () => {
  const { login, demoLogin, loading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [submittingPersona, setSubmittingPersona] = useState<string | null>(null);

  const isDemo = import.meta.env.VITE_DEMO_MODE === 'true';

  const getDestinationForRole = (role?: string) => {
    if (!role) return '/producer/listings';
    const r = role.toUpperCase();
    if (r === 'PRODUCER' || role === 'farmer' || role === 'fpo') return '/producer/listings';
    if (r === 'BUYER' || role.startsWith('buyer_')) return '/buyer/requirements';
    if (r === 'ADMIN' || role === 'operator') return '/ops/logistics';
    return '/market';
  };

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    try {
      const loggedUser = await login(email, password);
      navigate(getDestinationForRole(loggedUser?.role));
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Invalid credentials');
    }
  };

  const handlePersonaSelect = async (persona: DemoPersona) => {
    setErrorMessage(null);
    setSubmittingPersona(persona.key);
    try {
      const loggedUser = await demoLogin(persona.key);
      navigate(getDestinationForRole(loggedUser?.role ?? persona.role));
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Demo login failed');
    } finally {
      setSubmittingPersona(null);
    }
  };

  return (
    <div className="min-h-screen bg-bg flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary text-white font-bold text-2xl mb-3 shadow-sm">
          FS
        </div>
        <h1 className="text-3xl font-extrabold text-ink tracking-tight">FasalSetu</h1>
        <p className="mt-1 text-sm font-medium text-primary">
          Predict · Match · Move · Sell · Analyse
        </p>
        <p className="text-xs text-muted mt-1">
          Direct Agricultural Supply-Chain Coordination Platform
        </p>

        {isDemo && (
          <div className="mt-4 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center justify-center space-x-1.5">
            <span className="inline-block w-2 h-2 rounded-full bg-accent" />
            <span>
              <strong>Demo notice:</strong> Demo data only. All records are synthetic.
            </span>
          </div>
        )}
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-surface py-8 px-6 shadow-sm border border-gray-200 rounded-xl sm:px-10">
          {errorMessage && (
            <div className="mb-5 p-3 rounded-lg bg-red-50 border border-red-200 text-danger text-sm">
              <span className="font-semibold block">Sign In Failed</span>
              <span>{errorMessage}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleCredentialsSubmit}>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-ink">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="fpo_sonipat@demo.fasalsetu.local"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary text-sm"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-ink">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="demo1234"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary text-sm"
              />
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-primary hover:bg-green-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 transition-colors"
              >
                {loading && !submittingPersona ? 'Signing in...' : 'Sign in'}
              </button>
            </div>
          </form>

          {isDemo && (
            <div className="mt-8">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-surface px-2 text-muted font-semibold tracking-wider">
                    Or select demo persona
                  </span>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-1 gap-2.5">
                {DEMO_PERSONAS.map((persona) => {
                  const isCurrentSubmitting = submittingPersona === persona.key;
                  return (
                    <button
                      key={persona.key}
                      type="button"
                      disabled={loading}
                      onClick={() => handlePersonaSelect(persona)}
                      className="w-full text-left p-2.5 rounded-lg border border-gray-200 hover:border-primary hover:bg-primary-soft/30 transition-all flex items-center justify-between group disabled:opacity-50"
                    >
                      <div className="flex-1 min-w-0 pr-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-ink group-hover:text-primary truncate">
                            {persona.label}
                          </span>
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-700 uppercase">
                            {persona.role}
                          </span>
                        </div>
                        <p className="text-xs text-muted truncate">
                          {persona.sublabel} · {persona.location}
                        </p>
                      </div>
                      <span className="text-xs font-semibold text-primary opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                        {isCurrentSubmitting ? 'Loading...' : 'Select →'}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
