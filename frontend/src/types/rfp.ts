export interface TopMatch {
  sku: string;
  oem: string;
  score: number;
}

export interface TechnicalRecommendation {
  line_id: string;
  description: string;
  category: string;
  top_matches: TopMatch[];
  best_sku: string;
}

export interface TechnicalRecommendations {
  rfp_id: string;
  recommendations: TechnicalRecommendation[];
}

export interface TestDetail {
  code: string;
  description: string;
  cost: number;
}

export interface PricingLineItem {
  line_id: string;
  description: string;
  category: string;
  best_sku: string;
  quantity: number;
  unit: string;
  unit_price: number;
  material_total: number;
  tests: TestDetail[];
  tests_total: number;
  grand_total: number;
}

export interface PricingTotals {
  material_total: number;
  tests_total: number;
  overall_total: number;
}

export interface PricingOutput {
  rfp_id: string;
  line_items: PricingLineItem[];
  totals: PricingTotals;
}

export interface RfpPipelineResult {
  success: boolean;
  rfp_id: string;
  buyer: string;
  title: string;
  submission_due_date: string;
  currency: string;
  technical_recommendations: TechnicalRecommendations;
  pricing: PricingOutput;
  message?: string;
}

