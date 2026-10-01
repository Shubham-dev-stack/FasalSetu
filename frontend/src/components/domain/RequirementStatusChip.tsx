import React from 'react';

interface RequirementStatusChipProps {
  status: 'OPEN' | 'PARTIALLY_FULFILLED' | 'FULFILLED' | 'CANCELLED' | 'EXPIRED' | string;
}

export const RequirementStatusChip: React.FC<RequirementStatusChipProps> = ({ status }) => {
  const normStatus = status.toUpperCase();

  let colorClasses = 'bg-gray-100 text-gray-700 border-gray-200';
  let label = normStatus;

  switch (normStatus) {
    case 'OPEN':
      colorClasses = 'bg-emerald-50 text-emerald-800 border-emerald-300';
      label = 'Open';
      break;
    case 'PARTIALLY_FULFILLED':
      colorClasses = 'bg-sky-50 text-sky-800 border-sky-300';
      label = 'Partially Fulfilled';
      break;
    case 'FULFILLED':
      colorClasses = 'bg-teal-50 text-teal-800 border-teal-300';
      label = 'Fulfilled';
      break;
    case 'CANCELLED':
      colorClasses = 'bg-rose-50 text-rose-800 border-rose-300';
      label = 'Cancelled';
      break;
    case 'EXPIRED':
      colorClasses = 'bg-amber-50 text-amber-800 border-amber-300';
      label = 'Expired';
      break;
    default:
      break;
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${colorClasses}`}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-70" />
      {label}
    </span>
  );
};
