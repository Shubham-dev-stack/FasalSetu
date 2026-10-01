import React from 'react';
import { useLocation, Link } from 'react-router-dom';

interface PlaceholderPageProps {
  title: string;
  phase: string;
  description: string;
}

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({
  title,
  phase,
  description,
}) => {
  const location = useLocation();

  return (
    <div className="bg-surface rounded-xl border border-gray-200 p-8 shadow-sm text-center max-w-2xl mx-auto space-y-4 my-8">
      <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-primary-soft text-primary uppercase tracking-wider">
        {phase}
      </div>
      <h2 className="text-2xl font-bold text-ink">{title}</h2>
      <p className="text-sm text-muted max-w-md mx-auto">{description}</p>
      <div className="p-3 bg-bg rounded-lg text-xs font-mono text-muted inline-block">
        Route: {location.pathname}
      </div>
      <div className="pt-4">
        <Link
          to="/"
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-xs font-semibold text-ink hover:bg-gray-100 transition-colors"
        >
          ← Return to Dashboard
        </Link>
      </div>
    </div>
  );
};
