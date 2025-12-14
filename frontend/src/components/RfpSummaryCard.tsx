import { RfpPipelineResult } from '../types/rfp';

interface RfpSummaryCardProps {
  data: RfpPipelineResult;
}

export function RfpSummaryCard({ data }: RfpSummaryCardProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-12 border border-slate-200 dark:border-slate-700 text-center">
      <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">RFP Summary</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">RFP ID</p>
          <p className="text-base font-medium text-slate-800 dark:text-slate-100">{data.rfp_id}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">Buyer</p>
          <p className="text-base font-medium text-slate-800 dark:text-slate-100">{data.buyer}</p>
        </div>
        <div className="md:col-span-2">
          <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">Title</p>
          <p className="text-base font-medium text-slate-800 dark:text-slate-100">{data.title}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">Submission Due Date</p>
          <p className="text-base font-medium text-slate-800 dark:text-slate-100">{data.submission_due_date}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">Currency</p>
          <p className="text-base font-medium text-slate-800 dark:text-slate-100">{data.currency}</p>
        </div>
      </div>
    </div>
  );
}

