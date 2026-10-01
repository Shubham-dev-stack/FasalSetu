import React from 'react';

interface OrderPriceBreakdownProps {
  quantityKg: number;
  agreedPricePerKg: number;
  transportCostPerKg: number;
  platformFeePerKg: number;
  landedPricePerKg: number;
  totalAmount: number;
  basis?: string;
}

export const OrderPriceBreakdown: React.FC<OrderPriceBreakdownProps> = ({
  quantityKg,
  agreedPricePerKg,
  transportCostPerKg,
  platformFeePerKg,
  landedPricePerKg,
  totalAmount,
}) => {
  const farmgateTotal = (agreedPricePerKg * quantityKg).toFixed(2);
  const transportTotal = (transportCostPerKg * quantityKg).toFixed(2);
  const platformFeeTotal = (platformFeePerKg * quantityKg).toFixed(2);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3">
        <h3 className="font-semibold text-gray-900 text-sm">
          Landed Cost Breakdown
        </h3>
        <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
          Transparent Coordination
        </span>
      </div>

      <div className="space-y-2.5 text-sm">
        <div className="flex justify-between items-center text-gray-600">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            Farmgate Produce Value
          </span>
          <div className="text-right">
            <span className="font-medium text-gray-900">₹{agreedPricePerKg.toFixed(2)}/kg</span>
            <span className="text-xs text-gray-400 ml-2">(₹{farmgateTotal})</span>
          </div>
        </div>

        <div className="flex justify-between items-center text-gray-600">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
            Estimated Transport Haulage
            <span className="text-[11px] text-gray-400 font-normal">(Dedicated)</span>
          </span>
          <div className="text-right">
            <span className="font-medium text-gray-900">₹{transportCostPerKg.toFixed(2)}/kg</span>
            <span className="text-xs text-gray-400 ml-2">(₹{transportTotal})</span>
          </div>
        </div>

        <div className="flex justify-between items-center text-gray-600">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
            Platform Coordination Fee
            <span className="text-[11px] text-gray-400 font-normal">(2%)</span>
          </span>
          <div className="text-right">
            <span className="font-medium text-gray-900">₹{platformFeePerKg.toFixed(2)}/kg</span>
            <span className="text-xs text-gray-400 ml-2">(₹{platformFeeTotal})</span>
          </div>
        </div>

        <div className="pt-3 border-t border-gray-100 flex justify-between items-baseline">
          <div>
            <span className="font-bold text-gray-900 text-base">Estimated Landed Price</span>
            <p className="text-xs text-gray-500 font-normal">Per-kg delivered cost</p>
          </div>
          <div className="text-right">
            <span className="font-bold text-emerald-700 text-lg">
              ₹{landedPricePerKg.toFixed(2)}
              <span className="text-xs font-normal text-gray-500">/kg</span>
            </span>
            <p className="text-xs font-medium text-gray-700 mt-0.5">
              Total ₹{totalAmount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-gray-50 rounded-lg p-2.5 text-xs text-gray-500 border border-gray-100">
        Settlement occurs directly between participants outside the platform. Figures reflect direct supply-chain coordination.
      </div>
    </div>
  );
};
