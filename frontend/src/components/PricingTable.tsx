import { PricingOutput } from '../types/rfp';

interface PricingTableProps {
  data: PricingOutput;
  currency: string;
}

export function PricingTable({ data, currency }: PricingTableProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  if (!data.line_items || data.line_items.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-12 border border-slate-200 dark:border-slate-700 text-center">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Pricing</h2>
        <p className="text-slate-500 dark:text-slate-400">No pricing data available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-12 border border-slate-200 dark:border-slate-700 text-center">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Line Items Pricing</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="text-left py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Line ID</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Description</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Best SKU</th>
                <th className="text-right py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Quantity</th>
                <th className="text-right py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Unit Price</th>
                <th className="text-right py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Material Total</th>
                <th className="text-right py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Test Cost</th>
                <th className="text-right py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Grand Total</th>
              </tr>
            </thead>
            <tbody>
              {data.line_items.map((item, idx) => (
                <tr
                  key={item.line_id}
                  className={`border-b border-slate-100 dark:border-slate-700 ${idx % 2 === 0 ? 'bg-slate-50 dark:bg-slate-800/40' : 'bg-white dark:bg-slate-800/60'}`}
                >
                  <td className="py-3 px-4 font-mono text-xs text-slate-600 dark:text-slate-300">{item.line_id}</td>
                  <td className="py-3 px-4 text-slate-800 dark:text-slate-100 max-w-xs truncate">{item.description}</td>
                  <td className="py-3 px-4 font-mono text-xs text-slate-600 dark:text-slate-300">{item.best_sku}</td>
                  <td className="py-3 px-4 text-right text-slate-800 dark:text-slate-100">
                    {item.quantity} {item.unit}
                  </td>
                  <td className="py-3 px-4 text-right text-slate-800 dark:text-slate-100">{formatCurrency(item.unit_price)}</td>
                  <td className="py-3 px-4 text-right font-medium text-slate-800 dark:text-slate-100">
                    {formatCurrency(item.material_total)}
                  </td>
                  <td className="py-3 px-4 text-right text-slate-800 dark:text-slate-100">
                    {formatCurrency(item.tests_total)}
                  </td>
                  <td className="py-3 px-4 text-right font-semibold text-slate-900 dark:text-slate-100">
                    {formatCurrency(item.grand_total)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Totals Card */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-900 rounded-xl shadow-md p-6 border border-blue-200 dark:border-slate-700">
        <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Overall Totals</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-slate-600 dark:text-slate-300 uppercase tracking-wide mb-1">Total Material</p>
            <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{formatCurrency(data.totals.material_total)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-600 dark:text-slate-300 uppercase tracking-wide mb-1">Total Tests/Services</p>
            <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{formatCurrency(data.totals.tests_total)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-600 dark:text-slate-300 uppercase tracking-wide mb-1">Overall Total</p>
            <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">{formatCurrency(data.totals.overall_total)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

