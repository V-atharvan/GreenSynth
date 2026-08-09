/**
 * GreenSynth Analytics — Recommendation Engine Service Client
 */

import apiClient from './api'

export interface RecommendationCandidate {
  id: string
  recommendation_id: string
  rank: number
  parameter_set: Record<string, number>
  predicted_properties: {
    property_name: string
    predicted_value: number
    unit: string
  }
  uncertainty: {
    lower_bound?: number
    upper_bound?: number
    width?: number
  }
  applicability_status: string
  evidence_level: string
  evidence_score: number
  objective_score: number
  constraint_status: string
  novelty_score: number
  overall_score: number
  explanation: string
  warning?: string
  status: string
  modified_parameter_set?: Record<string, number>
  modification_reason?: string
  created_experiment_id?: string
}

export interface Recommendation {
  id: string
  project_id: string
  objective_id: string
  model_id: string
  model_version: string
  dataset_id: string
  generated_at: string
  researcher?: string
  status: string
  candidate_count: number
  ranking_method: string
  random_seed?: number
  notes?: string
  candidates: RecommendationCandidate[]
}

export interface RecommendationGeneratePayload {
  project_id: string
  objective_id: string
  model_id: string
  candidate_count?: number
  ranking_method?: string
  random_seed?: number
  max_uncertainty_width?: number
  notes?: string
}

export const recommendationService = {
  generateRecommendations: async (payload: RecommendationGeneratePayload): Promise<Recommendation> => {
    const res = await apiClient.post<Recommendation>('/recommendations/generate', payload)
    return res.data
  },

  getRecommendations: async (projectId?: string): Promise<Recommendation[]> => {
    const url = projectId ? `/recommendations?project_id=${projectId}` : '/recommendations'
    const res = await apiClient.get<Recommendation[]>(url)
    return res.data
  },

  getRecommendation: async (id: string): Promise<Recommendation> => {
    const res = await apiClient.get<Recommendation>(`/recommendations/${id}`)
    return res.data
  },

  approveCandidate: async (candidateId: string): Promise<RecommendationCandidate> => {
    const res = await apiClient.post<RecommendationCandidate>(`/recommendations/candidates/${candidateId}/approve`)
    return res.data
  },

  modifyCandidate: async (
    candidateId: string,
    payload: {
      modified_parameter_set: Record<string, number>
      modification_reason: string
    }
  ): Promise<RecommendationCandidate> => {
    const res = await apiClient.post<RecommendationCandidate>(
      `/recommendations/candidates/${candidateId}/modify`,
      payload
    )
    return res.data
  },

  createExperimentFromCandidate: async (candidateId: string): Promise<{
    message: string
    experiment_id: string
    experiment_code: string
    status: string
  }> => {
    const res = await apiClient.post(`/recommendations/candidates/${candidateId}/create-experiment`)
    return res.data
  },
}
