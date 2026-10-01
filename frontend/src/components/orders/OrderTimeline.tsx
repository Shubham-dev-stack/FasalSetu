import React from 'react';
import { OrderEvent } from '../../api/types';
import { OrderStatusChip } from '../domain/OrderStatusChip';

interface OrderTimelineProps {
  events: OrderEvent[];
}

export const OrderTimeline: React.FC<OrderTimelineProps> = ({ events }) => {
  if (!events || events.length === 0) {
    return null;
  }

  // Format date helper
  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleString('en-IN', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">
      <h3 className="font-semibold text-gray-900 text-sm border-b border-gray-100 pb-3">
        Order Lifecycle & Audit Timeline
      </h3>

      <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-200">
        {events.map((event, idx) => (
          <div key={event.id || idx} className="relative flex flex-col gap-1 text-sm">
            <span className="absolute -left-6 top-1.5 w-2.5 h-2.5 rounded-full border-2 border-white bg-primary shadow-sm" />
            
            <div className="flex items-center gap-2 flex-wrap">
              <OrderStatusChip status={event.to_status} />
              <span className="text-xs text-gray-400">•</span>
              <span className="text-xs font-medium text-gray-600 uppercase tracking-wider">
                {event.actor_role}
              </span>
              <span className="text-xs text-gray-400">•</span>
              <span className="text-xs text-gray-500">{formatDate(event.at)}</span>
            </div>

            {event.note && (
              <p className="text-xs text-gray-600 bg-gray-50 p-2 rounded border border-gray-100 mt-1">
                {event.note}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
