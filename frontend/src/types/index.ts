/**
 * GreenSynth Analytics — TypeScript Type Definitions (Phase 2 Update)
 *
 * Extends types for ParameterDefinition, ExperimentParameter, and updated SampleStatus.
 */

export * from './characterization'
export * from './analysis'

// ── Status Enums ──────────────────────────────────────────

export type ProjectStatus = 'ACTIVE' | 'ARCHIVED'

export type ExperimentStatus =
  | 'PLANNED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'FAILED'
  | 'ARCHIVED'

export type SampleStatus =
  | 'PREPARED'
  | 'READY_FOR_CHARACTERIZATION'
  | 'UNDER_ANALYSIS'
  | 'COMPLETED'
  | 'ARCHIVED'

export type ParameterDataType = 'NUMBER' | 'TEXT' | 'BOOLEAN' | 'ENUM'
export type ParameterStatus = 'ACTIVE' | 'INACTIVE'

// ── Project ───────────────────────────────────────────────

export interface ProjectSummary {
  id: string
  project_code: string
  name: string
  material: string
  synthesis_method: string
  solvent?: string
  status: ProjectStatus
  created_at: string
}

export interface Project extends ProjectSummary {
  description: string | null
  extract: string
  solvent: string
  updated_at: string
}

export interface ProjectCreate {
  project_code: string
  name: string
  description?: string
  material: string
  extract: string
  solvent: string
  synthesis_method: string
  status?: ProjectStatus
}

export interface ProjectUpdate {
  name?: string
  description?: string
  material?: string
  extract?: string
  solvent?: string
  synthesis_method?: string
  status?: ProjectStatus
}

// ── Parameter Definitions ──────────────────────────────────

export interface ParameterDefinition {
  id: string
  project_id: string
  parameter_name: string
  parameter_code: string
  description: string | null
  data_type: ParameterDataType
  unit: string | null
  required: boolean
  minimum_value: number | null
  maximum_value: number | null
  allowed_values: string[] | null
  status: ParameterStatus
  created_at: string
  updated_at: string
}

export interface ParameterDefinitionCreate {
  parameter_name: string
  parameter_code: string
  description?: string
  data_type: ParameterDataType
  unit?: string
  required?: boolean
  minimum_value?: number
  maximum_value?: number
  allowed_values?: string[]
  status?: ParameterStatus
}

export interface ParameterDefinitionUpdate {
  parameter_name?: string
  description?: string
  data_type?: ParameterDataType
  unit?: string
  required?: boolean
  minimum_value?: number
  maximum_value?: number
  allowed_values?: string[]
  status?: ParameterStatus
}

// ── Experiment Parameters ──────────────────────────────────

export interface ExperimentParameter {
  id: string
  experiment_id: string
  parameter_definition_id: string
  value: string | null
  value_numeric: number | null
  unit: string | null
  notes: string | null
  parameter_definition: ParameterDefinition
  created_at: string
  updated_at: string
}

export interface ExperimentParameterCreate {
  parameter_definition_id: string
  value?: string
  unit?: string
  notes?: string
}

// ── Experiment ────────────────────────────────────────────

export interface ExperimentSummary {
  id: string
  project_id: string
  experiment_code: string
  title: string
  status: ExperimentStatus
  experiment_date: string | null
  researcher: string | null
  created_at: string
}

export interface Experiment extends ExperimentSummary {
  notes: string | null
  updated_at: string
}

export interface ExperimentWithProject extends Experiment {
  project: ProjectSummary
}

export interface ExperimentCreate {
  project_id: string
  experiment_code: string
  title: string
  status?: ExperimentStatus
  experiment_date?: string
  researcher?: string
  notes?: string
  parameters?: ExperimentParameterCreate[]
}

export interface ExperimentUpdate {
  title?: string
  status?: ExperimentStatus
  experiment_date?: string
  researcher?: string
  notes?: string
}

// ── Sample ────────────────────────────────────────────────

export interface SampleSummary {
  id: string
  experiment_id: string
  sample_code: string
  name: string
  material: string | null
  status: SampleStatus
  created_at: string
}

export interface Sample extends SampleSummary {
  description: string | null
  notes: string | null
  updated_at: string
}

export interface SampleCreate {
  experiment_id: string
  sample_code: string
  name: string
  material?: string
  description?: string
  notes?: string
  status?: SampleStatus
}

export interface SampleUpdate {
  name?: string
  material?: string
  description?: string
  notes?: string
  status?: SampleStatus
}

// ── Dashboard ─────────────────────────────────────────────

export interface DashboardStats {
  total_projects: number
  total_experiments: number
  total_samples: number
  experiments_by_status: Partial<Record<ExperimentStatus, number>>
  projects_by_status: Partial<Record<ProjectStatus, number>>
  recent_experiments: ExperimentSummary[]
}

// ── API Error ─────────────────────────────────────────────

export interface ApiError {
  error_code: string
  message: string
  field?: string
  suggestion?: string
}
