import { useState } from 'react';
import { PricingOutput } from '../types/rfp';
import { GlobalOverrides, PricingRecalculateResponse } from '../types/review';

interface PricingOverridePanelProps {
  initialPricing: PricingOutput;
  currency: string;
  globalOverrides: GlobalOverrides;
  onGlobalOverridesChange: (overrides: GlobalOverrides) => void;
  onRecalculate: (overrides: GlobalOverrides) => Promise<PricingRecalculateResponse>;
}

export function PricingOverridePanel({
  initialPricing,
  currency,
  globalOverrides,
  onGlobalOverridesChange,
  onRecalculate,
}: PricingOverridePanelProps) {
  const [recalculatedPricing, setRecalculatedPricing] = useState<PricingRecalculateResponse | null>(null);
  const [recalculating, setRecalculating] = useState(false);
  const [warnings, setWarnings] = useState<string[]>([]);

  const displayPricing = recalculatedPricing || initialPricing;
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const handleRecalculate = async () => {
    setRecalculating(true);
    setWarnings([]);
    try {
      const result = await onRecalculate(globalOverrides);
      setRecalculatedPricing(result);
      if (result.warnings) {
        setWarnings(result.warnings);
      }
    } catch (error) {
      console.error('Recalculation failed:', error);
      alert('Failed to recalculate pricing. Please check the console.');
    } finally {
      setRecalculating(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 border border-slate-200 dark:border-slate-700 space-y-6">
      <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Pricing Overrides</h2>

      {/* Global Overrides */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-slate-50 dark:bg-slate-800/40 rounded-lg">
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Margin (fraction, e.g., 0.1 = 10%)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={globalOverrides.margin_fraction || ''}
            onChange={(e) =>
              onGlobalOverridesChange({
                ...globalOverrides,
                margin_fraction: e.target.value ? parseFloat(e.target.value) : null,
              })
            }
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Tax (fraction, e.g., 0.18 = 18%)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={globalOverrides.tax_fraction || ''}
            onChange={(e) =>
              onGlobalOverridesChange({
                ...globalOverrides,
                tax_fraction: e.target.value ? parseFloat(e.target.value) : null,
              })
            }
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
          />
        </div>
        <div className="flex items-end">
          <button
            onClick={handleRecalculate}
            disabled={recalculating}
            className="w-full px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
          >
            {recalculating ? 'Recalculating...' : 'Recalculate Pricing'}
          </button>
        </div>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-yellow-800 dark:text-yellow-300 mb-2">Warnings</h3>
          <ul className="list-disc list-inside text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
            {warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Pricing Preview */}
      <div>
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Pricing Preview</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="text-left py-2 px-3 font-semibold text-slate-700 dark:text-slate-300">Line ID</th>
                <th className="text-left py-2 px-3 font-semibold text-slate-700 dark:text-slate-300">SKU</th>
                <th className="text-right py-2 px-3 font-semibold text-slate-700 dark:text-slate-300">Unit Price</th>
                <th className="text-right py-2 px-3 font-semibold text-slate-700 dark:text-slate-300">Material Total</th>
                <th className="text-right py-2 px-3 font-semibold text-slate-700 dark:text-slate-300">Tests Total</th>
                <th className="text-right py-2 px-3 font-semibold text-slate-700 dark:text-slate-300">Grand Total</th>
              </tr>
            </thead>
            <tbody>
              {displayPricing.line_items.map((item, idx) => (
                <tr
                  key={item.line_id}
                  className={`border-b border-slate-100 dark:border-slate-700 ${idx % 2 === 0 ? 'bg-slate-50 dark:bg-slate-800/40' : 'bg-white dark:bg-slate-800/60'}`}
                >
                  <td className="py-2 px-3 font-mono text-xs text-slate-600 dark:text-slate-300">{item.line_id}</td>
                  <td className="py-2 px-3 font-mono text-xs text-slate-600 dark:text-slate-300">{item.best_sku}</td>
                  <td className="py-2 px-3 text-right text-slate-800 dark:text-slate-100">{formatCurrency(item.unit_price)}</td>
                  <td className="py-2 px-3 text-right font-medium text-slate-800 dark:text-slate-100">
                    {formatCurrency(item.material_total)}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-800 dark:text-slate-100">
                    {formatCurrency(item.tests_total || (item as any).line_level_tests_total || 0)}
                  </td>
                  <td className="py-2 px-3 text-right font-semibold text-slate-900 dark:text-slate-100">
                    {formatCurrency(item.grand_total || item.material_total + (item.tests_total || 0))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Totals */}
        <div className="mt-4 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-900 rounded-lg border border-blue-200 dark:border-slate-700">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-slate-600 dark:text-slate-300 uppercase tracking-wide mb-1">Total Material</p>
              <p className="text-xl font-bold text-slate-800 dark:text-slate-100">
                {formatCurrency(displayPricing.totals.material_total)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-600 dark:text-slate-300 uppercase tracking-wide mb-1">Total Tests/Services</p>
              <p className="text-xl font-bold text-slate-800 dark:text-slate-100">
                {formatCurrency(displayPricing.totals.tests_total)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-600 dark:text-slate-300 uppercase tracking-wide mb-1">Overall Total</p>
              <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">
                {formatCurrency(displayPricing.totals.overall_total)}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

