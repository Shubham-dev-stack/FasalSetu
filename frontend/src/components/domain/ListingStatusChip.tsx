import React from 'react';

interface ListingStatusChipProps {
  status: 'ACTIVE' | 'SOLD_OUT' | 'EXPIRED' | 'WITHDRAWN' | string;
}

export const ListingStatusChip: React.FC<ListingStatusChipProps> = ({ status }) => {
  const normStatus = status.toUpperCase();

  let colorClasses = 'bg-gray-100 text-gray-700 border-gray-200';
  let label = normStatus;

  switch (normStatus) {
    case 'ACTIVE':
      colorClasses = 'bg-emerald-50 text-emerald-800 border-emerald-300';
      label = 'Active';
      break;
    case 'SOLD_OUT':
      colorClasses = 'bg-gray-100 text-gray-600 border-gray-300';
      label = 'Sold Out';
      break;
    case 'EXPIRED':
      colorClasses = 'bg-amber-50 text-amber-800 border-amber-300';
      label = 'Expired';
      break;
    case 'WITHDRAWN':
      colorClasses = 'bg-rose-50 text-rose-800 border-rose-300';
      label = 'Withdrawn';
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
