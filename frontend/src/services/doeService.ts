import { apiClient } from '@/services/api';

export interface Objective {
  id: string;
  project_id: string;
  name: string;
  version: string;
  description?: string;
  target_property: string;
  direction: string;
  target_value?: number;
  min_value?: number;
  max_value?: number;
  unit?: string;
  weight: number;
  synthesis_method?: string;
  solvent?: string;
  constraints?: any[];
  status: string;
  created_by?: string;
  created_at: string;
}

export interface FactorDefinition {
  parameter_code: string;
  name: string;
  factor_type: string; // CONTINUOUS, CATEGORICAL, DISCRETE, ORDINAL
  role?: string; // CONTROLLABLE, BLOCK, COVARIATE
  lower_bound?: number;
  upper_bound?: number;
  center_value?: number;
  unit?: string;
  levels?: number | (number | string)[];
}

export interface ResponseDefinition {
  property_name: string;
  unit?: string;
  direction: string; // MAXIMIZE, MINIMIZE, TARGET, RANGE
  target?: number;
  lower_limit?: number;
  upper_limit?: number;
  preferred_value?: number;
  weight?: number;
}

export interface DOEConstraint {
  parameter_code: string;
  operator: string;
  value: number | string | (number | string)[];
  unit?: string;
}

export interface DOECreateInput {
  project_id: string;
  objective_id?: string;
  name: string;
  description?: string;
  research_question?: string;
  design_method: string; // FULL_FACTORIAL, FRACTIONAL_FACTORIAL, CENTRAL_COMPOSITE, BOX_BEHNKEN, RANDOMIZED_CANDIDATE
  factors: FactorDefinition[];
  responses?: ResponseDefinition[];
  constraints?: DOEConstraint[];
  requested_runs?: number;
  replicates?: number;
  center_points?: number;
  random_seed?: number;
  randomize_run_order?: boolean;
}

export interface DOEWorkloadPreview {
  design_method: string;
  factors_count: number;
  base_runs: number;
  replicates: number;
  center_points: number;
  total_runs: number;
  design_resolution?: string;
  confounding_warning?: string;
  requires_workload_warning: boolean;
  warning_message?: string;
}

export interface DOEResponse {
  id: string;
  project_id: string;
  objective_id?: string;
  name: string;
  description?: string;
  research_question?: string;
  version: string;
  design_method: string;
  factors: FactorDefinition[];
  responses?: ResponseDefinition[];
  constraints?: DOEConstraint[];
  requested_runs: number;
  replicates: number;
  center_points: number;
  alpha_value?: number;
  design_resolution?: string;
  random_seed?: number;
  randomize_run_order: boolean;
  status: string;
  notes?: string;
  created_by?: string;
  created_at: string;
  updated_at?: string;
}

export interface ProposedExperiment {
  id: string;
  doe_id: string;
  design_condition_id: string;
  design_order: number;
  run_order: number;
  replicate_number: number;
  is_center_point?: boolean;
  block?: string;
  factor_values: Record<string, number | string>;
  measured_responses?: Record<string, number>;
  parameter_deviations?: Record<string, { proposed: number; actual: number; deviation: number; percentage_deviation: number }>;
  status: string;
  converted_experiment_id?: string;
  created_by?: string;
  created_at: string;
}

export interface FactorCoverageItem {
  parameter_code: string;
  name: string;
  factor_type: string;
  min_generated?: string;
  max_generated?: string;
  unique_levels: number;
}

export interface DOEQualityReport {
  total_proposed_runs: number;
  valid_runs: number;
  invalid_runs: number;
  intentional_replicates: number;
  factor_coverage: FactorCoverageItem[];
  warnings: string[];
}

export interface DOEAnalysisResponse {
  id: string;
  doe_id: string;
  doe_version: string;
  response_property: string;
  sample_count: number;
  main_effects: Record<string, { estimated_main_effect: number; level_means: Record<string, number>; level_counts: Record<string, number>; n_observations: number }>;
  interaction_effects?: Record<string, number>;
  regression_model?: {
    n_observations: number;
    coefficients?: number[];
    fit_metrics?: { r2?: number; adjusted_r2?: number; rmse?: number; mae?: number };
    status?: string;
  };
  fit_metrics: { r2?: number; adjusted_r2?: number; rmse?: number; mae?: number };
  residual_diagnostics?: { residuals?: number[]; fitted_values?: number[] };
  created_at: string;
}

export const doeService = {
  listObjectives: async (projectId: string): Promise<Objective[]> => {
    const res = await apiClient.get('/objectives', { params: { project_id: projectId } });
    return res.data;
  },

  previewWorkload: async (payload: DOECreateInput): Promise<DOEWorkloadPreview> => {
    const res = await apiClient.post('/doe/preview', payload);
    return res.data;
  },

  createDOEAndGenerate: async (payload: DOECreateInput): Promise<{ doe: DOEResponse; quality_report: DOEQualityReport }> => {
    const res = await apiClient.post('/doe', payload);
    return res.data;
  },

  listProjectDOEs: async (projectId: string): Promise<DOEResponse[]> => {
    const res = await apiClient.get('/doe', { params: { project_id: projectId } });
    return res.data;
  },

  getDOE: async (id: string): Promise<DOEResponse> => {
    const res = await apiClient.get(`/doe/${id}`);
    return res.data;
  },

  listProposedExperiments: async (doeId: string): Promise<ProposedExperiment[]> => {
    const res = await apiClient.get(`/doe/${doeId}/proposed-experiments`);
    return res.data;
  },

  approveDOEStudy: async (id: string): Promise<DOEResponse> => {
    const res = await apiClient.post(`/doe/${id}/approve`);
    return res.data;
  },

  regenerateDOEVersion: async (id: string, payload: DOECreateInput): Promise<{ doe: DOEResponse; quality_report: DOEQualityReport }> => {
    const res = await apiClient.post(`/doe/${id}/regenerate`, payload);
    return res.data;
  },

  convertRunToPlannedExperiment: async (proposedId: string): Promise<any> => {
    const res = await apiClient.post(`/doe/proposed-experiments/${proposedId}/convert`);
    return res.data;
  },

  analyzeDOE: async (doeId: string, responseProperty: string = 'Electrical Conductivity'): Promise<DOEAnalysisResponse> => {
    const res = await apiClient.get(`/doe/${doeId}/analysis`, {
      params: { response_property: responseProperty },
    });
    return res.data;
  },

  exportDOECSVUrl: (doeId: string): string => {
    const baseUrl = apiClient.defaults.baseURL || '/api/v1';
    return `${baseUrl}/doe/${doeId}/export`;
  },
};
