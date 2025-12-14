interface ControlsPanelProps {
  onRun: () => void;
  loading: boolean;
}

export function ControlsPanel({ onRun, loading }: ControlsPanelProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-12 border border-slate-200 dark:border-slate-700 text-center">
      <div className="flex items-center gap-4">
        <button
          onClick={onRun}
          disabled={loading}
          className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg
                className="animate-spin h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Running Pipeline...
            </>
          ) : (
            'Run Demo'
          )}
        </button>
        <div className="text-sm text-slate-600 dark:text-slate-300">
          Runs the offline multi-agent pipeline on the latest indexed RFP (selected by Sales Agent).
        </div>
      </div>
    </div>
  );
}

