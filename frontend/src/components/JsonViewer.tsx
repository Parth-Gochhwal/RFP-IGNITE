import { useState } from 'react';
import { RfpPipelineResult } from '../types/rfp';

interface JsonViewerProps {
  data: RfpPipelineResult | null;
}

export function JsonViewer({ data }: JsonViewerProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!data) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-12 border border-slate-200 dark:border-slate-700 text-center">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors rounded-t-xl"
      >
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Raw JSON Response</h2>
        <svg
          className={`w-5 h-5 text-slate-600 dark:text-slate-300 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isOpen && (
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700">
          <pre className="text-xs bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

