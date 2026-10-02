import React from 'react';
import { MatchingScores, MatchingWeights } from '../../api/types';

interface ScoreBreakdownProps {
  scores: MatchingScores;
  weights: MatchingWeights;
  showWeights?: boolean;
}

export const ScoreBreakdown: React.FC<ScoreBreakdownProps> = ({
  scores,
  weights,
  showWeights = true,
}) => {
  const factors = [
    {
      key: 'price',
      label: 'Price Advantage',
      score: scores.price,
      weight: weights.price,
      color: 'bg-emerald-500',
    },
    {
      key: 'distance',
      label: 'Proximity',
      score: scores.distance,
      weight: weights.distance,
      color: 'bg-blue-500',
    },
    {
      key: 'freshness',
      label: 'Freshness & Shelf Life',
      score: scores.freshness,
      weight: weights.freshness,
      color: 'bg-amber-500',
    },
    {
      key: 'fill',
      label: 'Demand Fill Rate',
      score: scores.fill,
      weight: weights.fill,
      color: 'bg-purple-500',
    },
  ];

  return (
    <div className="space-y-2.5 text-xs">
      <div className="flex items-center justify-between pb-1 border-b border-gray-100">
        <span className="font-semibold text-ink">Deterministic Match Score</span>
        <span className="font-bold text-sm text-primary font-mono">
          {(scores.total * 100).toFixed(1)}%
        </span>
      </div>

      <div className="space-y-2">
        {factors.map((f) => {
          const percent = Math.round(f.score * 100);
          const weightPct = Math.round(f.weight * 100);

          return (
            <div key={f.key} className="space-y-1">
              <div className="flex justify-between items-center text-[11px] text-muted">
                <span className="font-medium text-ink/80">{f.label}</span>
                <span className="font-mono">
                  {percent}%
                  {showWeights && (
                    <span className="text-gray-400 ml-1">({weightPct}% w)</span>
                  )}
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-1.5 rounded-full transition-all duration-300 ${f.color}`}
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
