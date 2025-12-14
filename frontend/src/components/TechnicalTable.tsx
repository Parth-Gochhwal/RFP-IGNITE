import { TechnicalRecommendations } from '../types/rfp';

interface TechnicalTableProps {
  data: TechnicalRecommendations;
}

export function TechnicalTable({ data }: TechnicalTableProps) {
  if (!data.recommendations || data.recommendations.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-12 border border-slate-200 dark:border-slate-700 text-center">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Technical Recommendations</h2>
        <p className="text-slate-500 dark:text-slate-400">No recommendations available.</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-12 border border-slate-200 dark:border-slate-700 text-center">
      <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Technical Recommendations</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-700">
              <th className="text-left py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Line ID</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Description</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Category</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Best SKU</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-700 dark:text-slate-300">Top Matches</th>
            </tr>
          </thead>
          <tbody>
            {data.recommendations.map((rec, idx) => (
              <tr
                key={rec.line_id}
                className={`border-b border-slate-100 dark:border-slate-700 ${idx % 2 === 0 ? 'bg-slate-50 dark:bg-slate-800/40' : 'bg-white dark:bg-slate-800/60'}`}
              >
                <td className="py-3 px-4 font-mono text-xs text-slate-600 dark:text-slate-300">{rec.line_id}</td>
                <td className="py-3 px-4 text-slate-800 dark:text-slate-100">{rec.description}</td>
                <td className="py-3 px-4">
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 rounded text-xs font-medium">
                    {rec.category}
                  </span>
                </td>
                <td className="py-3 px-4 font-mono text-xs font-semibold text-slate-800 dark:text-slate-100">
                  {rec.best_sku}
                </td>
                <td className="py-3 px-4 text-xs text-slate-600 dark:text-slate-300">
                  {rec.top_matches.map((m, i) => (
                    <span key={m.sku}>
                      {m.sku} ({m.score}%)
                      {i < rec.top_matches.length - 1 && ', '}
                    </span>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

