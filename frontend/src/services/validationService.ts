/**
 * GreenSynth Analytics — Validation Service Client
 */

import apiClient from './api'
import { MLModel } from './mlService'

export interface ValidationCriterion {
  id: string
  property_name: string
  metric: string
  threshold: number
  unit: string
  comparison_operator: string
  description?: string
  created_at: string
}

export interface ValidationCriterionCreatePayload {
  property_name: string
  metric: string
  threshold: number
  unit: string
  comparison_operator?: string
  description?: string
}

export interface HoldoutValidation {
  id: string
  model_id: string
  model_version: string
  dataset_id: string
  experiment_id: string
  sample_id: string
  target_property: string
  predicted_value: number
  actual_value: number
  unit: string
  error: number
  absolute_error: number
  relative_error?: number
  status: string
  researcher?: string
  notes?: string
  created_at: string
}

export interface ProspectiveExperiment {
  id: string
  model_id: string
  model_version: string
  prediction_id: string
  project_id: string
  proposed_conditions: Record<string, number>
  researcher?: string
  approval_status: string
  laboratory_experiment_id?: string
  sample_id?: string
  actual_result?: number
  actual_unit?: string
  measurement_uncertainty?: number
  validation_status: string
  notes?: string
  created_at: string
}

export interface ValidationResult {
  id: string
  prediction_id?: string
  experiment_id: string
  sample_id: string
  model_id: string
  model_version: string
  target_property: string
  predicted_value: number
  prediction_lower_bound?: number
  prediction_upper_bound?: number
  actual_value: number
  actual_measurement_uncertainty?: number
  unit: string
  error: number
  absolute_error: number
  relative_error?: number
  is_within_prediction_interval?: boolean
  criterion_id?: string
  criterion_result?: string
  validation_type: string
  validation_status: string
  is_synthetic: boolean
  researcher?: string
  notes?: string
  timestamp: string
}

export interface ModelPerformanceHistory {
  model_id: string
  model_name: string
  model_version: string
  target_property: string
  statistical_metrics: Record<string, any>
  n_experimental_validations: number
  experimental_mae?: number
  experimental_rmse?: number
  interval_coverage_rate?: number
  small_sample_warning: boolean
  warnings: string[]
}

export const validationService = {
  createCriterion: async (payload: ValidationCriterionCreatePayload): Promise<ValidationCriterion> => {
    const res = await apiClient.post<ValidationCriterion>('/validation/criteria', payload)
    return res.data
  },

  getCriteria: async (propertyName?: string): Promise<ValidationCriterion[]> => {
    const url = propertyName ? `/validation/criteria?property_name=${propertyName}` : '/validation/criteria'
    const res = await apiClient.get<ValidationCriterion[]>(url)
    return res.data
  },

  executeHoldout: async (payload: {
    model_id: string
    experiment_id: string
    sample_id: string
    criterion_id?: string
    researcher?: string
    notes?: string
  }): Promise<HoldoutValidation> => {
    const res = await apiClient.post<HoldoutValidation>('/validation/holdout', payload)
    return res.data
  },

  createProspective: async (payload: {
    prediction_id: string
    project_id: string
    researcher?: string
    notes?: string
  }): Promise<ProspectiveExperiment> => {
    const res = await apiClient.post<ProspectiveExperiment>('/validation/prospective', payload)
    return res.data
  },

  createProspectiveExperiment: async (payload: {
    prediction_id: string
    project_id: string
    researcher?: string
    notes?: string
  }): Promise<ProspectiveExperiment> => {
    return validationService.createProspective(payload)
  },

  linkProspectiveResult: async (
    prospectiveId: string,
    labExperimentId: string,
    sampleId: string,
    criterionId?: string,
    measurementUncertainty?: number,
    notes?: string
  ): Promise<ValidationResult> => {
    const params = new URLSearchParams({
      laboratory_experiment_id: labExperimentId,
      sample_id: sampleId,
    })
    if (criterionId) params.append('criterion_id', criterionId)
    if (measurementUncertainty !== undefined) params.append('measurement_uncertainty', measurementUncertainty.toString())
    if (notes) params.append('notes', notes)

    const res = await apiClient.post<ValidationResult>(
      `/validation/prospective/${prospectiveId}/link-result?${params.toString()}`
    )
    return res.data
  },

  getValidationResults: async (modelId?: string): Promise<ValidationResult[]> => {
    const url = modelId ? `/validation/results?model_id=${modelId}` : '/validation/results'
    const res = await apiClient.get<ValidationResult[]>(url)
    return res.data
  },

  getPerformanceHistory: async (modelId: string): Promise<ModelPerformanceHistory> => {
    const res = await apiClient.get<ModelPerformanceHistory>(`/models/${modelId}/performance-history`)
    return res.data
  },

  retrainModel: async (modelId: string, notes?: string): Promise<MLModel[]> => {
    const res = await apiClient.post<MLModel[]>(`/models/${modelId}/retrain`, { notes })
    return res.data
  },
}
