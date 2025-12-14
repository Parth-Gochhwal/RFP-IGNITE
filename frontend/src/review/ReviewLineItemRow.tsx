import { TechnicalRecommendation } from '../types/rfp';
import { LineOverride } from '../types/review';

interface ReviewLineItemRowProps {
  recommendation: TechnicalRecommendation;
  override: LineOverride | null;
  onOverrideChange: (override: LineOverride) => void;
}

export function ReviewLineItemRow({
  recommendation,
  override,
  onOverrideChange,
}: ReviewLineItemRowProps) {
  const currentSku = override?.approved_sku || recommendation.best_sku;
  const isManualSku = override?.approved_sku && !recommendation.top_matches.some(m => m.sku === override.approved_sku);
  const manualPrice = override?.manual_unit_price;

  const handleSkuChange = (sku: string) => {
    if (sku === '--manual--') {
      onOverrideChange({
        line_id: recommendation.line_id,
        approved_sku: '',
        manual_unit_price: override?.manual_unit_price || null,
        override_reason: override?.override_reason || null,
      });
    } else {
      onOverrideChange({
        line_id: recommendation.line_id,
        approved_sku: sku,
        manual_unit_price: override?.manual_unit_price || null,
        override_reason: override?.override_reason || null,
      });
    }
  };

  const handleManualSkuChange = (sku: string) => {
    onOverrideChange({
      line_id: recommendation.line_id,
      approved_sku: sku,
      manual_unit_price: override?.manual_unit_price || null,
      override_reason: override?.override_reason || null,
    });
  };

  const handleManualPriceChange = (price: number | null) => {
    onOverrideChange({
      line_id: recommendation.line_id,
      approved_sku: override?.approved_sku || recommendation.best_sku,
      manual_unit_price: price,
      override_reason: override?.override_reason || null,
    });
  };

  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-mono text-xs font-semibold text-slate-600 dark:text-slate-300">{recommendation.line_id}</span>
            <span className="px-2 py-1 bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 rounded text-xs font-medium">
              {recommendation.category}
            </span>
          </div>
          <p className="text-sm text-slate-800 dark:text-slate-100 mb-3">{recommendation.description}</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Select SKU
              </label>
              <select
                value={isManualSku ? '--manual--' : currentSku}
                onChange={(e) => handleSkuChange(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
              >
                <option value={recommendation.best_sku}>
                  {recommendation.best_sku} (AI Recommended)
                </option>
                {recommendation.top_matches.map((match) => (
                  <option key={match.sku} value={match.sku}>
                    {match.sku} ({match.score}%)
                  </option>
                ))}
                <option value="--manual--">-- Manual SKU --</option>
              </select>
            </div>

            {isManualSku && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Manual SKU
                </label>
                <input
                  type="text"
                  value={override?.approved_sku || ''}
                  onChange={(e) => handleManualSkuChange(e.target.value)}
                  placeholder="Enter SKU"
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Manual Unit Price (optional)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={manualPrice || ''}
                onChange={(e) => handleManualPriceChange(e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="Auto from catalog"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
              />
            </div>
          </div>

          {override?.override_reason !== undefined && (
            <div className="mt-2">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Override Reason (optional)
              </label>
              <input
                type="text"
                value={override.override_reason || ''}
                onChange={(e) =>
                  onOverrideChange({
                    ...override,
                    override_reason: e.target.value || null,
                  })
                }
                placeholder="Reason for override"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

