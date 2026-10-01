import React, { useState } from 'react';
import { useAuth } from '../../lib/auth';
import { DEMO_PERSONAS } from '../../api/types';

interface NavbarProps {
  title?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ title = 'Dashboard' }) => {
  const { user, logout, demoLogin, loading } = useAuth();
  const [showPersonaMenu, setShowPersonaMenu] = useState(false);
  const isDemo = import.meta.env.VITE_DEMO_MODE === 'true';

  const handleSwitchPersona = async (key: string) => {
    setShowPersonaMenu(false);
    await demoLogin(key);
  };

  return (
    <header className="bg-surface border-b border-gray-200 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Brand & Title */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="w-8 h-8 rounded-lg bg-primary text-white font-bold flex items-center justify-center text-sm shadow-sm">
                FS
              </span>
              <span className="font-bold text-lg text-ink hidden sm:inline">FasalSetu</span>
            </div>
            <span className="text-gray-300 hidden sm:inline">|</span>
            <h1 className="text-base font-semibold text-ink truncate">{title}</h1>
          </div>

          {/* Right items */}
          <div className="flex items-center space-x-3">
            {isDemo && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-accent text-ink border border-amber-400">
                DEMO DATA
              </span>
            )}

            {isDemo && (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowPersonaMenu(!showPersonaMenu)}
                  disabled={loading}
                  className="text-xs border border-gray-300 rounded-md px-2.5 py-1.5 bg-bg hover:bg-gray-100 font-medium text-ink flex items-center space-x-1"
                >
                  <span>Switch Persona ▾</span>
                </button>
                {showPersonaMenu && (
                  <div className="absolute right-0 mt-2 w-64 bg-surface rounded-lg shadow-lg border border-gray-200 py-1 z-50 text-xs">
                    <div className="px-3 py-1.5 border-b border-gray-100 font-semibold text-muted">
                      Quick Persona Switch
                    </div>
                    {DEMO_PERSONAS.map((p) => (
                      <button
                        key={p.key}
                        onClick={() => handleSwitchPersona(p.key)}
                        className={`w-full text-left px-3 py-2 hover:bg-primary-soft/40 flex flex-col ${
                          user?.email === p.email ? 'bg-primary-soft/60 font-semibold' : ''
                        }`}
                      >
                        <div className="flex justify-between items-center">
                          <span className="text-ink">{p.label}</span>
                          <span className="text-[10px] uppercase text-muted">{p.role}</span>
                        </div>
                        <span className="text-[11px] text-muted">{p.location}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {user && (
              <div className="flex items-center space-x-3 pl-2 border-l border-gray-200">
                <div className="text-right hidden md:block">
                  <div className="text-xs font-semibold text-ink">{user.name}</div>
                  <div className="text-[11px] text-muted uppercase tracking-wider">{user.role}</div>
                </div>
                <button
                  onClick={logout}
                  className="text-xs font-medium text-muted hover:text-danger border border-gray-200 hover:border-danger/30 rounded-md px-2.5 py-1.5 transition-colors"
                >
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
