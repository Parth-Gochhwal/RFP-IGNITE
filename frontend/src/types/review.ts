/**
 * TypeScript types for review functionality.
 * Mirrors the Pydantic models in review/models.py
 */

export interface LineOverride {
  line_id: string;
  approved_sku?: string | null;
  manual_unit_price?: number | null;
  override_reason?: string | null;
}

export interface GlobalOverrides {
  margin_fraction?: number | null;
  tax_fraction?: number | null;
  test_exclusions?: string[] | null;
}

export interface ReviewSaveRequest {
  rfp_id: string;
  overrides: LineOverride[];
  global_overrides: GlobalOverrides;
  reviewer: string;
  notes?: string | null;
}

export interface ReviewDraft {
  rfp_id: string;
  saved_at: string;
  saved_by: string;
  request: ReviewSaveRequest;
}

export interface DraftResponse {
  pipeline: any; // RfpPipelineResult
  draft: ReviewDraft | null;
}

export interface RecalculateRequest {
  technical_output: any;
  scope_of_supply: any[];
  overrides: LineOverride[];
  global_overrides: GlobalOverrides;
  pricing_input: any;
}

export interface PricingRecalculateResponse {
  rfp_id: string;
  line_items: any[];
  global_tests?: any[];
  totals: {
    material_total: number;
    tests_total: number;
    overall_total: number;
  };
  warnings?: string[];
}

export interface ApproveResponse {
  success: boolean;
  final_response: any;
  export_url: string;
  audit_trail: Array<{
    action: string;
    saved_at?: string;
    saved_by?: string;
    approved_at?: string;
    approved_by?: string;
    notes?: string;
  }>;
}

