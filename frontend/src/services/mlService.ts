/**
 * GreenSynth Analytics — Machine Learning Service Client
 */

import apiClient from './api'

export interface MLDatasetFeatureSpec {
  feature_name: string
  source_parameter: string
  unit: string
  data_type?: string
}

export interface MLDatasetCreatePayload {
  project_id: string
  name: string
  description?: string
  target_property: string
  target_type?: string
  target_unit: string
  features: MLDatasetFeatureSpec[]
  filters?: Record<string, any>
  experiment_ids?: string[]
}

export interface MLDataset {
  id: string
  project_id: string
  name: string
  version: string
  description?: string
  target_property: string
  target_type: string
  target_unit: string
  features: Array<{ feature_name: string; source_parameter: string; unit: string; data_type: string }>
  filters?: Record<string, any>
  preprocessing_config?: Record<string, any>
  status: string
  is_synthetic: boolean
  eligible_count: number
  excluded_count: number
  exclusion_summary?: Record<string, number>
  created_at: string
}

export interface MLDatasetRecord {
  id: string
  dataset_id: string
  experiment_id: string
  sample_id: string
  analysis_run_id?: string
  feature_values: Record<string, number>
  target_value?: number
  target_unit?: string
  is_eligible: boolean
  exclusion_reason?: string
  provenance_details?: Record<string, any>
}

export interface MLTrainingRunCreatePayload {
  dataset_id: string
  model_types: string[]
  scaling?: string
  cv_folds?: number
  random_seed?: number
  hyperparameters?: Record<string, any>
}

export interface MLModel {
  id: string
  training_run_id: string
  dataset_id: string
  dataset_version: string
  name: string
  model_type: string
  version: string
  target_property: string
  target_type: string
  target_unit: string
  feature_names: string[]
  feature_specs: any[]
  preprocessing_config: Record<string, any>
  hyperparameters: Record<string, any>
  metrics: {
    train_mae: number
    train_rmse: number
    train_r2: number
    cv_mae: number
    cv_rmse: number
    cv_r2: number
    n_samples: number
    overfitting_warning: boolean
    low_data_warning: boolean
    diagnostics?: {
      actual_vs_predicted: Array<{ sample_id: string; actual: number; predicted: number }>
      residuals: Array<{ sample_id: string; actual: number; residual: number }>
      feature_importance: Record<string, number>
      mean_residual: number
      residual_std: number
    }
  }
  feature_importance?: Record<string, number>
  library_versions: Record<string, string>
  status: string
  approval_notes?: string
  approved_by?: string
  approved_at?: string
  created_at: string
}

export interface MLPredictPayload {
  input_parameters: Record<string, number>
  notes?: string
}

export interface MLPrediction {
  id: string
  model_id: string
  model_version: string
  dataset_id: string
  input_parameters: Record<string, number>
  predicted_property: string
  predicted_value: number
  unit: string
  uncertainty_lower?: number
  uncertainty_upper?: number
  uncertainty_method?: string
  applicability_status: string
  applicability_details?: Record<string, any>
  warnings?: string[]
  created_at: string
}

export const mlService = {
  createDataset: async (payload: MLDatasetCreatePayload): Promise<MLDataset> => {
    const res = await apiClient.post<MLDataset>('/ml/datasets', payload)
    return res.data
  },

  getDatasets: async (projectId: string): Promise<MLDataset[]> => {
    const res = await apiClient.get<MLDataset[]>(`/ml/datasets?project_id=${projectId}`)
    return res.data
  },

  getDataset: async (datasetId: string): Promise<MLDataset> => {
    const res = await apiClient.get<MLDataset>(`/ml/datasets/${datasetId}`)
    return res.data
  },

  getDatasetRecords: async (datasetId: string): Promise<MLDatasetRecord[]> => {
    const res = await apiClient.get<MLDatasetRecord[]>(`/ml/datasets/${datasetId}/records`)
    return res.data
  },

  trainModels: async (payload: MLTrainingRunCreatePayload): Promise<MLModel[]> => {
    const res = await apiClient.post<MLModel[]>('/ml/training-runs', payload)
    return res.data
  },

  getModels: async (datasetId?: string, status?: string): Promise<MLModel[]> => {
    let url = '/ml/models'
    const params = new URLSearchParams()
    if (datasetId) params.append('dataset_id', datasetId)
    if (status) params.append('status', status)
    if (params.toString()) url += `?${params.toString()}`
    const res = await apiClient.get<MLModel[]>(url)
    return res.data
  },

  listModels: async (datasetId?: string, status?: string): Promise<MLModel[]> => {
    return mlService.getModels(datasetId, status)
  },

  getModel: async (modelId: string): Promise<MLModel> => {
    const res = await apiClient.get<MLModel>(`/ml/models/${modelId}`)
    return res.data
  },

  approveModel: async (modelId: string, notes?: string): Promise<MLModel> => {
    const res = await apiClient.post<MLModel>(`/ml/models/${modelId}/approve`, { notes })
    return res.data
  },

  rejectModel: async (modelId: string, notes?: string): Promise<MLModel> => {
    const res = await apiClient.post<MLModel>(`/ml/models/${modelId}/reject`, { notes })
    return res.data
  },

  generatePrediction: async (modelId: string, payload: MLPredictPayload): Promise<MLPrediction> => {
    const res = await apiClient.post<MLPrediction>(`/ml/models/${modelId}/predict`, payload)
    return res.data
  },

  getPredictions: async (modelId?: string): Promise<MLPrediction[]> => {
    const url = modelId ? `/ml/predictions?model_id=${modelId}` : '/ml/predictions'
    const res = await apiClient.get<MLPrediction[]>(url)
    return res.data
  },

  validatePrediction: async (
    predictionId: string,
    actualValue: number,
    experimentId?: string,
    actualTargetProperty?: string,
    actualUnit?: string,
    actualSynthesisParams?: Record<string, number>
  ): Promise<any> => {
    const params = new URLSearchParams({ actual_value: String(actualValue) })
    if (experimentId) params.append('experiment_id', experimentId)
    if (actualTargetProperty) params.append('actual_target_property', actualTargetProperty)
    if (actualUnit) params.append('actual_unit', actualUnit)
    if (actualSynthesisParams) params.append('actual_synthesis_params', JSON.stringify(actualSynthesisParams))
    const res = await apiClient.post(`/ml/predictions/${predictionId}/validate?${params.toString()}`)
    return res.data
  },

  getModelPerformance: async (modelId: string): Promise<any> => {
    const res = await apiClient.get(`/ml/models/${modelId}/performance`)
    return res.data
  },

  getModelHealth: async (modelId: string): Promise<any> => {
    const res = await apiClient.get(`/ml/models/${modelId}/health`)
    return res.data
  },

  submitModelReview: async (modelId: string, reviewStatus: string, reviewer?: string, notes?: string): Promise<any> => {
    const params = new URLSearchParams({ review_status: reviewStatus })
    if (reviewer) params.append('reviewer', reviewer)
    if (notes) params.append('notes', notes)
    const res = await apiClient.post(`/ml/models/${modelId}/review?${params.toString()}`)
    return res.data
  },

  retireModel: async (modelId: string, notes?: string): Promise<any> => {
    const params = new URLSearchParams()
    if (notes) params.append('notes', notes)
    const res = await apiClient.post(`/ml/models/${modelId}/retire?${params.toString()}`)
    return res.data
  },

  getModelReportUrl: (modelId: string): string => {
    const baseUrl = apiClient.defaults.baseURL || '/api/v1'
    return `${baseUrl}/ml/reports/${modelId}`
  },
}
