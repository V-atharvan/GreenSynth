import { apiClient } from '@/services/api';

export interface DatasetVersionResponse {
  id: string;
  dataset_id: string;
  project_id: string;
  name: string;
  version: string;
  description?: string;
  included_sample_ids: string[];
  included_experiment_ids: string[];
  included_doe_run_ids?: string[];
  included_factors: string[];
  included_responses: string[];
  filtering_rules?: Record<string, any>;
  exclusion_rules?: Record<string, any>;
  summary_json: Record<string, any>;
  status: string;
  created_by?: string;
  created_at: string;
}

export interface DescriptiveStatsItem {
  variable: string;
  sample_size_n: number;
  unit?: string;
  mean?: number;
  median?: number;
  std_dev?: number;
  variance?: number;
  min_val?: number;
  max_val?: number;
  val_range?: number;
  q1?: number;
  q3?: number;
  iqr?: number;
  cv?: number;
  missing_count: number;
}

export interface CorrelationMatrixResponse {
  method: string;
  variables: string[];
  matrix: Record<string, Record<string, number>>;
  p_values?: Record<string, Record<string, number>>;
  sample_size_n: number;
  warnings: string[];
}

export interface RegressionRequest {
  x_variables: string[];
  y_variable: string;
  model_type?: string; // SIMPLE_LINEAR, MULTIPLE_LINEAR, INTERACTION, QUADRATIC
  include_interaction?: boolean;
  include_quadratic?: boolean;
}

export interface RegressionResponse {
  y_variable: string;
  x_variables: string[];
  model_type: string;
  method: string;
  formula: string;
  coefficients: Record<string, number>;
  intercept: number;
  r_squared: number;
  adjusted_r_squared: number;
  rmse: number;
  mae: number;
  aic?: number;
  bic?: number;
  confidence_interval?: Record<string, number[]>;
  prediction_interval?: Record<string, number[]>;
  sample_size_n: number;
  interpretation: string;
  warnings: string[];
}

export interface ModelDiagnosticsResponse {
  residuals: number[];
  fitted_values: number[];
  qq_sample_quantiles: number[];
  qq_theoretical_quantiles: number[];
  heteroscedasticity_warning: boolean;
  normality_warning: boolean;
  diagnostic_summary: string;
}

export interface DataQualityReportResponse {
  total_samples: number;
  variables_evaluated: string[];
  missing_counts: Record<string, number>;
  duplicate_count: number;
  outlier_count: number;
  unit_consistency: string;
  quality_status: string; // PASS, WARNING, ERROR
  warnings: string[];
}

export interface ReadinessGatesResponse {
  dataset_version_id: string;
  is_ml_ready: boolean;
  ml_ready_criteria: Record<string, boolean>;
  is_optimization_ready: boolean;
  optimization_ready_criteria: Record<string, boolean>;
  disclaimer: string;
}

export interface EvidenceCreateInput {
  dataset_version_id: string;
  statement: string;
  evidence_type: string; // OBSERVATION, ASSOCIATION, STATISTICAL_EFFECT, MODEL_ESTIMATE, VALIDATED_RESULT
  variables: string[];
  sample_size: number;
  statistical_method: string;
  effect_estimate?: number;
  uncertainty?: number;
  confidence_interval?: Record<string, number>;
  prediction_interval?: Record<string, number>;
  limitations?: string[];
}

export interface EvidenceResponse {
  id: string;
  dataset_version_id: string;
  analysis_run_id?: string;
  statement: string;
  evidence_type: string;
  variables: string[];
  sample_size: number;
  statistical_method: string;
  effect_estimate?: number;
  uncertainty?: number;
  confidence_interval?: Record<string, number>;
  prediction_interval?: Record<string, number>;
  evidence_score: number;
  scoring_criteria: Record<string, any>;
  limitations?: string[];
  status: string;
  created_by?: string;
  created_at: string;
}

export const evidenceService = {
  createDatasetVersion: async (datasetId: string, versionLabel: string = 'v1.0'): Promise<DatasetVersionResponse> => {
    const res = await apiClient.post('/statistics/datasets', null, {
      params: { dataset_id: datasetId, version_label: versionLabel },
    });
    return res.data;
  },

  getDatasetVersion: async (versionId: string): Promise<DatasetVersionResponse> => {
    const res = await apiClient.get(`/statistics/datasets/${versionId}`);
    return res.data;
  },

  calculateDescriptive: async (variableName: string, values: number[], unit?: string): Promise<DescriptiveStatsItem> => {
    const res = await apiClient.post('/statistics/descriptive', values, {
      params: { variable_name: variableName, unit },
    });
    return res.data;
  },

  computeCorrelationMatrix: async (variables: string[], dataRows: Record<string, number | null>[], method: string = 'PEARSON'): Promise<CorrelationMatrixResponse> => {
    const res = await apiClient.post('/statistics/correlation', dataRows, {
      params: { variables, method },
    });
    return res.data;
  },

  computeRegression: async (payload: RegressionRequest, dataRows: Record<string, number | null>[]): Promise<RegressionResponse> => {
    const res = await apiClient.post('/statistics/regression', dataRows, {
      params: payload,
    });
    return res.data;
  },

  computeDiagnostics: async (residuals: number[], fittedValues: number[]): Promise<ModelDiagnosticsResponse> => {
    const res = await apiClient.post('/statistics/diagnostics', { residuals, fittedValues });
    return res.data;
  },

  runQualityCheck: async (sampleRecords: Record<string, number | null>[], variables: string[]): Promise<DataQualityReportResponse> => {
    const res = await apiClient.post('/statistics/quality-check', { sample_records: sampleRecords, variables });
    return res.data;
  },

  evaluateReadinessGates: async (versionId: string, sampleSize: number = 10): Promise<ReadinessGatesResponse> => {
    const res = await apiClient.get(`/statistics/readiness-gates/${versionId}`, {
      params: { sample_size: sampleSize },
    });
    return res.data;
  },

  createEvidenceRecord: async (payload: EvidenceCreateInput): Promise<EvidenceResponse> => {
    const res = await apiClient.post('/evidence', payload);
    return res.data;
  },

  listEvidenceRecords: async (datasetVersionId?: string): Promise<EvidenceResponse[]> => {
    const res = await apiClient.get('/evidence', { params: { dataset_version_id: datasetVersionId } });
    return res.data;
  },

  approveEvidenceRecord: async (evidenceId: string): Promise<EvidenceResponse> => {
    const res = await apiClient.post(`/evidence/${evidenceId}/approve`);
    return res.data;
  },

  exportEvidenceReportUrl: (evidenceId: string): string => {
    const baseUrl = apiClient.defaults.baseURL || '/api/v1';
    return `${baseUrl}/evidence/${evidenceId}/report`;
  },
};
