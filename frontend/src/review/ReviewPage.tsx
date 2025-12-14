import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { RfpPipelineResult } from '../types/rfp';
import {
  GlobalOverrides,
  LineOverride,
  PricingRecalculateResponse,
  RecalculateRequest,
  ReviewSaveRequest,
} from '../types/review';
import { ReviewLineItemRow } from './ReviewLineItemRow';
import { PricingOverridePanel } from './PricingOverridePanel';
import { ApprovalBar } from './ApprovalBar';
import { RfpSummaryCard } from '../components/RfpSummaryCard';
import { TechnicalTable } from '../components/TechnicalTable';
import { JsonViewer } from '../components/JsonViewer';
import PriceBreakdownChart from '../components/PriceBreakdownChart';
import SpecMatchBarChart from '../components/SpecMatchBarChart';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function ReviewPage() {
  const { id: rfpId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pipeline, setPipeline] = useState<RfpPipelineResult | null>(null);
  const [_draft, setDraft] = useState<any>(null);
  const [scopeOfSupply, setScopeOfSupply] = useState<any[]>([]);
  const [pricingInput, setPricingInput] = useState<any>({});
  const [overrides, setOverrides] = useState<Map<string, LineOverride>>(new Map());
  const [globalOverrides, setGlobalOverrides] = useState<GlobalOverrides>({});
  const [reviewer, setReviewer] = useState('');
  const [recalculatedPricing, setRecalculatedPricing] = useState<any>(null);
  const [draftHistory, setDraftHistory] = useState<Array<{ saved_at: string; saved_by: string }>>([]);
  const [approvedAt, setApprovedAt] = useState<string | undefined>();
  const [approvedBy, setApprovedBy] = useState<string | undefined>();

  useEffect(() => {
    if (!rfpId) {
      setError('RFP ID is required');
      setLoading(false);
      return;
    }

    // Fetch draft data
    fetch(`${API_BASE_URL}/api/rfp/${rfpId}/draft`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to fetch draft: ${res.status}`);
        return res.json();
      })
      .then((data: any) => {
        setPipeline(data.pipeline);
        setScopeOfSupply(data.scope_of_supply || []);
        setPricingInput(data.pricing_input || {});
        if (data.draft) {
          setDraft(data.draft);
          setReviewer(data.draft.saved_by);
          // Load overrides from draft
          const overrideMap = new Map<string, LineOverride>();
          for (const override of data.draft.request.overrides) {
            overrideMap.set(override.line_id, override);
          }
          setOverrides(overrideMap);
          setGlobalOverrides(data.draft.request.global_overrides);
          setDraftHistory([{ saved_at: data.draft.saved_at, saved_by: data.draft.saved_by }]);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [rfpId]);

  const handleOverrideChange = (lineId: string, override: LineOverride) => {
    const newOverrides = new Map(overrides);
    newOverrides.set(lineId, override);
    setOverrides(newOverrides);
  };

  const handleRecalculate = async (globalOverrides: GlobalOverrides): Promise<PricingRecalculateResponse> => {
    if (!pipeline) throw new Error('Pipeline data not available');

    const request: RecalculateRequest = {
      technical_output: pipeline.technical_recommendations,
      scope_of_supply: scopeOfSupply,
      overrides: Array.from(overrides.values()),
      global_overrides: globalOverrides,
      pricing_input: pricingInput,
    };

    const response = await fetch(`${API_BASE_URL}/api/pricing/recalculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const result: PricingRecalculateResponse = await response.json();
    setRecalculatedPricing(result);
    return result;
  };

  const handleSaveDraft = async () => {
    if (!rfpId || !reviewer.trim()) throw new Error('RFP ID and reviewer name required');

    const request: ReviewSaveRequest = {
      rfp_id: rfpId,
      overrides: Array.from(overrides.values()),
      global_overrides: globalOverrides,
      reviewer: reviewer.trim(),
      notes: null,
    };

    const response = await fetch(`${API_BASE_URL}/api/rfp/${rfpId}/review/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    setDraftHistory([...draftHistory, { saved_at: result.draft.saved_at, saved_by: result.draft.saved_by }]);
  };

  const handleApprove = async () => {
    if (!rfpId || !reviewer.trim()) throw new Error('RFP ID and reviewer name required');

    const request: ReviewSaveRequest = {
      rfp_id: rfpId,
      overrides: Array.from(overrides.values()),
      global_overrides: globalOverrides,
      reviewer: reviewer.trim(),
      notes: null,
    };

    const response = await fetch(`${API_BASE_URL}/api/rfp/${rfpId}/review/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    setApprovedAt(new Date().toISOString());
    setApprovedBy(reviewer.trim());
    return { export_url: result.export_url };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 dark:bg-slate-900 dark:text-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-300">Loading review data...</p>
        </div>
      </div>
    );
  }

  if (error || !pipeline) {
    return (
      <div className="min-h-screen bg-slate-100 dark:bg-slate-900 dark:text-slate-100 flex items-center justify-center">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 border border-red-200 dark:border-red-800 max-w-md">
          <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">Error</h2>
          <p className="text-red-600 dark:text-red-300">{error || 'Pipeline data not available'}</p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const displayPricing = recalculatedPricing || pipeline.pricing;
  const matchItems =
    pipeline?.technical_recommendations?.recommendations?.map((r: any) => ({
      line_id: r.line_id,
      description: r.description ?? r.line_description ?? '',
      best_match_score:
        r.top_matches && r.top_matches.length
          ? r.top_matches[0].score
          : r.best_match_score ?? r.spec_match ?? 0,
    })) ?? [];

  const priceTotals =
    displayPricing?.totals ??
    (displayPricing && {
      material_total: displayPricing.material_total ?? 0,
      tests_total: displayPricing.tests_total ?? 0,
      overall_total:
        displayPricing.overall_total ?? displayPricing.totals?.overall_total,
    }) ??
    null;

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 dark:text-slate-100 pb-32">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Review Console - {pipeline.rfp_id}</h1>
            <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">Inspect and override SKU recommendations and pricing</p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700"
          >
            Back to Dashboard
          </button>
        </div>

        {/* RFP Summary */}
        <RfpSummaryCard data={pipeline} />

        {/* Charts row: Spec match + Price breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-2">
          <div className="lg:col-span-2">
            <SpecMatchBarChart items={matchItems} />
          </div>
          <div className="lg:col-span-1">
            <PriceBreakdownChart totals={priceTotals} />
          </div>
        </div>

        {/* Technical Recommendations with Overrides */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 border border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Line Item Overrides</h2>
          <div className="space-y-4">
            {pipeline.technical_recommendations.recommendations.map((rec) => (
              <ReviewLineItemRow
                key={rec.line_id}
                recommendation={rec}
                override={overrides.get(rec.line_id) || null}
                onOverrideChange={(override) => handleOverrideChange(rec.line_id, override)}
              />
            ))}
          </div>
        </div>

        {/* Pricing Override Panel */}
        <PricingOverridePanel
          initialPricing={pipeline.pricing}
          currency={pipeline.currency}
          globalOverrides={globalOverrides}
          onGlobalOverridesChange={setGlobalOverrides}
          onRecalculate={handleRecalculate}
        />

        {/* Technical Table (read-only) */}
        <TechnicalTable data={pipeline.technical_recommendations} />

        {/* JSON Viewer */}
        <JsonViewer data={pipeline} />

        {/* Approval Bar (fixed at bottom) */}
        <ApprovalBar
          rfpId={rfpId!}
          reviewer={reviewer}
          onReviewerChange={setReviewer}
          overrides={Array.from(overrides.values())}
          globalOverrides={globalOverrides}
          onSaveDraft={handleSaveDraft}
          onApprove={handleApprove}
          draftHistory={draftHistory}
          approvedAt={approvedAt}
          approvedBy={approvedBy}
        />
      </div>
    </div>
  );
}

