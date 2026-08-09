/**
 * GreenSynth Analytics — Closed-Loop Learning & Validation Service Client
 */

import apiClient from './api'

export interface ResearchLoopSummary {
  total_experiments: number
  total_recommendations: number
  recommendations_tested: number
  validations_completed: number
  predictions_within_interval: number
  supported_recommendations: number
  partially_supported_recommendations: number
  not_supported_recommendations: number
  inconclusive_recommendations: number
  avg_absolute_error?: number | null
  avg_relative_error?: number | null
  sample_count_n: number
  evidence_level: string
  active_model_version: string
  active_dataset_version: string
  stage_counts: {
    experimental_data: number
    dataset: number
    model: string
    recommendation: number
    experiment: number
    actual_result: number
    validation: number
    dataset_candidate: number
    new_dataset: string
    new_model: string
  }
}

export interface DatasetCandidate {
  id: string
  candidate_dataset_id: string
  experiment_id: string
  sample_id: string
  validation_id: string
  proposed_target: string
  data_quality_status: string
  researcher_review_status: 'PENDING_REVIEW' | 'ACCEPTED' | 'REJECTED' | 'FLAGGED_FOR_REVIEW'
  created_at: string
  reviewed_at?: string | null
  reviewer?: string | null
  notes?: string | null
}

export const closedLoopService = {
  getSummary: async (): Promise<ResearchLoopSummary> => {
    const res = await apiClient.get<ResearchLoopSummary>('/closed-loop/summary')
    return res.data
  },

  getPendingQueue: async (projectId?: string): Promise<any[]> => {
    const url = projectId ? `/validation/pending?project_id=${projectId}` : '/validation/pending'
    const res = await apiClient.get<any[]>(url)
    return res.data
  },

  createValidation: async (payload: {
    model_id: string
    experiment_id: string
    sample_id: string
    predicted_value: number
    actual_value: number
    prediction_lower_bound?: number
    prediction_upper_bound?: number
    target_property?: string
    unit?: string
    recommendation_id?: string
    candidate_id?: string
    researcher?: string
    notes?: string
  }): Promise<any> => {
    const res = await apiClient.post<any>('/validation/create', payload)
    return res.data
  },

  listDatasetCandidates: async (status?: string): Promise<DatasetCandidate[]> => {
    const url = status ? `/dataset-candidates?status=${status}` : '/dataset-candidates'
    const res = await apiClient.get<DatasetCandidate[]>(url)
    return res.data
  },

  acceptCandidate: async (id: string, reviewer: string = 'Dr. Dataset Curator', notes?: string): Promise<any> => {
    const params = new URLSearchParams({ reviewer })
    if (notes) params.append('notes', notes)
    const res = await apiClient.post<any>(`/dataset-candidates/${id}/accept?${params.toString()}`)
    return res.data
  },

  rejectCandidate: async (id: string, reviewer: string = 'Dr. Dataset Curator', notes?: string): Promise<any> => {
    const params = new URLSearchParams({ reviewer })
    if (notes) params.append('notes', notes)
    const res = await apiClient.post<any>(`/dataset-candidates/${id}/reject?${params.toString()}`)
    return res.data
  },

  promoteModel: async (id: string, promotedBy: string = 'Dr. Chief Researcher'): Promise<any> => {
    const params = new URLSearchParams({ promoted_by: promotedBy })
    const res = await apiClient.post<any>(`/models/${id}/promote?${params.toString()}`)
    return res.data
  },

  retireModel: async (id: string, retiredBy: string = 'Dr. Chief Researcher'): Promise<any> => {
    const params = new URLSearchParams({ retired_by: retiredBy })
    const res = await apiClient.post<any>(`/models/${id}/retire?${params.toString()}`)
    return res.data
  },
}
