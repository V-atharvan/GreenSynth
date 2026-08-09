import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8000/api/v1/optimization'

export interface OptimizationObjective {
  id?: string
  project_id: string
  name: string
  description?: string
  target_property: string
  direction: 'MAXIMIZE' | 'MINIMIZE' | 'TARGET'
  target_value?: number
  minimum_value?: number
  maximum_value?: number
  weight: number
  unit?: string
  status?: string
}

export interface OptimizationConstraint {
  id?: string
  project_id: string
  constraint_type: 'PARAMETER_RANGE' | 'PROPERTY_RANGE' | 'FIXED_VALUE' | 'CATEGORICAL_ALLOWED_VALUE' | 'MODEL_DOMAIN'
  target_code: string
  operator?: string
  minimum_value?: number
  maximum_value?: number
  fixed_value?: number
  allowed_values?: any[]
  unit?: string
  is_hard_constraint?: boolean
}

export interface OptimizationCandidate {
  id: string
  optimization_run_id: string
  candidate_number: number
  rank: number
  parameter_values: Record<string, number>
  parameter_units: Record<string, string>
  feasibility_status: 'FEASIBLE' | 'INFEASIBLE' | 'WARNING'
  domain_status: 'IN_DOMAIN' | 'NEAR_BOUNDARY' | 'OUT_OF_DOMAIN'
  predictions: Record<string, number>
  uncertainties: Record<string, any>
  objective_score: number
  score_breakdown: Record<string, any>
  evidence_score: number
  novelty_category: 'LOW_DISTANCE' | 'MEDIUM_DISTANCE' | 'HIGH_DISTANCE' | 'ALREADY_TESTED'
  parameter_distance: number
  nearby_experiment_ids: string[]
  candidate_type: 'EXPLOITATION' | 'EXPLORATION'
  status: 'GENERATED' | 'SHORTLISTED' | 'SELECTED' | 'REJECTED' | 'CONVERTED_TO_EXPERIMENT' | 'ARCHIVED'
  created_at: string
}

export interface OptimizationRun {
  id: string
  project_id: string
  objective_id: string
  model_id: string
  model_version: string
  dataset_id: string
  dataset_version: string
  generation_method: 'GRID_SEARCH' | 'RANDOM_SEARCH' | 'MODEL_GUIDED_SEARCH'
  random_seed?: number
  requested_candidate_count: number
  feasible_candidate_count: number
  search_space_definition: Record<string, any>
  constraints_definition: Record<string, any>
  started_at: string
  completed_at?: string
  status: 'PLANNED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
  candidates: OptimizationCandidate[]
}

export interface OptimizationRunCreatePayload {
  project_id: string
  objective_id: string
  model_id: string
  generation_method?: 'GRID_SEARCH' | 'RANDOM_SEARCH' | 'MODEL_GUIDED_SEARCH'
  random_seed?: number
  requested_candidate_count?: number
  allow_out_of_domain?: boolean
  notes?: string
}

export interface OptimizationReport {
  run_id: string
  project_code: string
  project_name: string
  objective_name: string
  target_property: string
  direction: string
  model_name: string
  model_version: string
  dataset_version: string
  model_health_status: string
  generation_method: string
  total_candidates_generated: number
  feasible_candidates_count: number
  top_candidates: OptimizationCandidate[]
  disclaimer: string
  generated_at: string
}

export const optimizationService = {
  createObjective: async (payload: OptimizationObjective): Promise<OptimizationObjective> => {
    const res = await axios.post(`${API_BASE}/objectives`, payload)
    return res.data
  },

  listObjectives: async (projectId?: string): Promise<OptimizationObjective[]> => {
    const res = await axios.get(`${API_BASE}/objectives`, { params: { project_id: projectId } })
    return res.data
  },

  createConstraint: async (payload: OptimizationConstraint): Promise<OptimizationConstraint> => {
    const res = await axios.post(`${API_BASE}/constraints`, payload)
    return res.data
  },

  listConstraints: async (projectId?: string): Promise<OptimizationConstraint[]> => {
    const res = await axios.get(`${API_BASE}/constraints`, { params: { project_id: projectId } })
    return res.data
  },

  validateSearchSpace: async (projectId: string): Promise<any> => {
    const res = await axios.post(`${API_BASE}/search-space/validate`, { project_id: projectId })
    return res.data
  },

  createRun: async (payload: OptimizationRunCreatePayload): Promise<OptimizationRun> => {
    const res = await axios.post(`${API_BASE}/runs`, payload)
    return res.data
  },

  listRuns: async (projectId?: string): Promise<OptimizationRun[]> => {
    const res = await axios.get(`${API_BASE}/runs`, { params: { project_id: projectId } })
    return res.data
  },

  getRun: async (runId: string): Promise<OptimizationRun> => {
    const res = await axios.get(`${API_BASE}/runs/${runId}`)
    return res.data
  },

  selectCandidate: async (candidateId: string, reason?: string): Promise<OptimizationCandidate> => {
    const res = await axios.post(`${API_BASE}/candidates/${candidateId}/select`, { decision: 'SELECTED', reason })
    return res.data
  },

  rejectCandidate: async (candidateId: string, reason?: string): Promise<OptimizationCandidate> => {
    const res = await axios.post(`${API_BASE}/candidates/${candidateId}/reject`, { decision: 'REJECTED', reason })
    return res.data
  },

  createProposedExperiment: async (candidateId: string): Promise<any> => {
    const res = await axios.post(`${API_BASE}/candidates/${candidateId}/create-experiment`)
    return res.data
  },

  getReport: async (runId: string): Promise<OptimizationReport> => {
    const res = await axios.get(`${API_BASE}/runs/${runId}/report`)
    return res.data
  },
}
