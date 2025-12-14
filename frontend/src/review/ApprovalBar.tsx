import { useState } from 'react';
import { GlobalOverrides, LineOverride } from '../types/review';

interface ApprovalBarProps {
  rfpId: string;
  reviewer: string;
  onReviewerChange: (reviewer: string) => void;
  overrides: LineOverride[];
  globalOverrides: GlobalOverrides;
  onSaveDraft: () => Promise<void>;
  onApprove: () => Promise<{ export_url: string }>;
  draftHistory?: Array<{ saved_at: string; saved_by: string }>;
  approvedAt?: string;
  approvedBy?: string;
}

export function ApprovalBar(props: ApprovalBarProps) {
  const {
    reviewer,
    onReviewerChange,
    onSaveDraft,
    onApprove,
    draftHistory = [],
    approvedAt,
    approvedBy,
  } = props;
  const [saving, setSaving] = useState(false);
  const [approving, setApproving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [approveSuccess, setApproveSuccess] = useState(false);
  const [exportUrl, setExportUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSaveDraft = async () => {
    if (!reviewer.trim()) {
      setError('Reviewer name is required');
      return;
    }
    setSaving(true);
    setError(null);
    setSaveSuccess(false);
    try {
      await onSaveDraft();
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save draft');
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async () => {
    if (!reviewer.trim()) {
      setError('Reviewer name is required');
      return;
    }
    setApproving(true);
    setError(null);
    setApproveSuccess(false);
    try {
      const result = await onApprove();
      setExportUrl(result.export_url);
      setApproveSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve');
    } finally {
      setApproving(false);
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 shadow-lg z-50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex-1">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Reviewer Name *
            </label>
            <input
              type="text"
              value={reviewer}
              onChange={(e) => onReviewerChange(e.target.value)}
              placeholder="Enter your name"
              className="w-full max-w-xs px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500"
            />
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSaveDraft}
              disabled={saving || !reviewer.trim()}
              className="px-6 py-2 bg-slate-600 text-white font-semibold rounded-lg hover:bg-slate-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? 'Saving...' : 'Save Draft'}
            </button>
            <button
              onClick={handleApprove}
              disabled={approving || !reviewer.trim()}
              className="px-6 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed transition-colors"
            >
              {approving ? 'Approving...' : 'Approve Final'}
            </button>
          </div>
        </div>

        {/* Status Messages */}
        {(saveSuccess || approveSuccess || error) && (
          <div className="mt-3">
            {saveSuccess && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-2 text-sm text-green-800 dark:text-green-300">
                Draft saved successfully
              </div>
            )}
            {approveSuccess && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-2 text-sm text-green-800 dark:text-green-300">
                Review approved!{' '}
                {exportUrl && (
                  <a
                    href={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${exportUrl}`}
                    className="underline font-semibold"
                    download
                  >
                    Download Export ZIP
                  </a>
                )}
              </div>
            )}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-2 text-sm text-red-800 dark:text-red-300">
                {error}
              </div>
            )}
          </div>
        )}

        {/* Audit History */}
        {(draftHistory.length > 0 || approvedAt) && (
          <div className="mt-3 pt-3 border-t border-slate-200">
            <p className="text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2">Audit History</p>
            <div className="text-xs text-slate-500 dark:text-slate-400 space-y-1">
              {draftHistory.map((draft, idx) => (
                <div key={idx}>
                  Draft saved by {draft.saved_by} at {new Date(draft.saved_at).toLocaleString()}
                </div>
              ))}
              {approvedAt && approvedBy && (
                <div className="font-semibold text-green-700 dark:text-green-400">
                  ✓ Approved by {approvedBy} at {new Date(approvedAt).toLocaleString()}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

