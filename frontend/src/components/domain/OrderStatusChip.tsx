import React from 'react';

interface OrderStatusChipProps {
  status:
    | 'PLACED'
    | 'CONFIRMED'
    | 'REJECTED'
    | 'CANCELLED'
    | 'IN_TRANSIT'
    | 'DELIVERED'
    | string;
}

export const OrderStatusChip: React.FC<OrderStatusChipProps> = ({ status }) => {
  const normStatus = status.toUpperCase();

  let colorClasses = 'bg-gray-100 text-gray-700 border-gray-200';
  let label = normStatus;

  switch (normStatus) {
    case 'PLACED':
      colorClasses = 'bg-blue-50 text-blue-800 border-blue-300';
      label = 'Placed';
      break;
    case 'CONFIRMED':
      colorClasses = 'bg-emerald-50 text-emerald-800 border-emerald-300';
      label = 'Confirmed';
      break;
    case 'REJECTED':
      colorClasses = 'bg-rose-50 text-rose-800 border-rose-300';
      label = 'Rejected';
      break;
    case 'CANCELLED':
      colorClasses = 'bg-gray-100 text-gray-600 border-gray-300';
      label = 'Cancelled';
      break;
    case 'IN_TRANSIT':
      colorClasses = 'bg-amber-50 text-amber-800 border-amber-300';
      label = 'In Transit';
      break;
    case 'DELIVERED':
      colorClasses = 'bg-emerald-50 text-emerald-800 border-emerald-300';
      label = 'Delivered';
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
