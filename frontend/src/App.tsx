// frontend/src/App.tsx
import { Routes, Route, useNavigate } from "react-router-dom";

import { useRfpPipeline } from "./hooks/useRfpPipeline";
import { Header } from "./components/Header";
import { ControlsPanel } from "./components/ControlsPanel";
import { RfpSummaryCard } from "./components/RfpSummaryCard";
import { AgentTimeline } from "./components/AgentTimeline";
import { TechnicalTable } from "./components/TechnicalTable";
import { PricingTable } from "./components/PricingTable";
import { JsonViewer } from "./components/JsonViewer";
import { ReviewPage } from "./review/ReviewPage";

/**
 * Dashboard - main landing page view
 *
 * Important: the outermost wrapper controls page background & base text color
 * so the `dark` class on <html> (or <documentElement>) flips the entire app.
 */
function Dashboard() {
  const { data, loading, error, runPipeline } = useRfpPipeline();
  const navigate = useNavigate();

  return (
    // root wrapper: sets light/dark page background + base text color
    <div className="min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-900 dark:text-slate-100 transition-colors duration-200">
      <Header />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Controls Panel */}
        <ControlsPanel onRun={runPipeline} loading={loading} />

        {/* Error Banner */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
            <div className="flex items-center gap-2">
              <svg
                className="w-5 h-5 text-red-600 dark:text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-red-800 dark:text-red-200 font-medium">Error: {error}</p>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!data && !loading && !error && (
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-12 border border-slate-200 dark:border-slate-700 text-center">
            <svg
              className="w-16 h-16 text-slate-400 dark:text-slate-300 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="text-xl font-semibold text-slate-800 dark:text-slate-50 mb-2">
              Ready to Process RFP
            </h3>
            <p className="text-slate-600 dark:text-slate-300">
              Run the demo to see how agents collaborate on a real RFP.
            </p>
          </div>
        )}

        {/* RFP Summary and Agent Timeline */}
        {data && (
          <>
            {/* Review CTA Card */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-900 rounded-xl shadow-md p-6 border border-blue-200 dark:border-slate-700">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-50 mb-2">
                    Admin Review Required
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-300">
                    Review and override SKU recommendations, adjust pricing parameters, and approve the final response.
                  </p>
                </div>
                <button
                  onClick={() => navigate(`/review/rfp/${data.rfp_id}`)}
                  className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Open Review Console
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RfpSummaryCard data={data} />
              <AgentTimeline completed={true} />
            </div>

            {/* Technical Recommendations */}
            <TechnicalTable data={data.technical_recommendations} />

            {/* Pricing */}
            <PricingTable data={data.pricing} currency={data.currency} />

            {/* JSON Viewer */}
            <JsonViewer data={data} />
          </>
        )}
      </main>
    </div>
  );
}

/** App routes */
function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/review/rfp/:id" element={<ReviewPage />} />
    </Routes>
  );
}

export default App;
