import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8000/api/v1'

export interface ProjectMatrixRow {
  project_code: string
  project_name: string
  material: string
  biomass?: string
  extract: string
  solvent: string
  synthesis_method: string
  experiment_count: number
  sample_count: number
  characterization_count: number
  dataset_status: string
  model_status: string
  optimization_status: string
}

export interface ProjectConfiguration {
  project_id: string
  project_code: string
  name: string
  material_system: string
  material: string
  biomass?: string
  extract: string
  solvent: string
  synthesis_method: string
  current_version: string
  characterization_capabilities: Record<string, boolean>
  analysis_capabilities: Record<string, boolean>
  optimization_capabilities: Record<string, boolean>
}

export interface PropertyComparabilityResult {
  comparability_status: 'COMPARABLE' | 'COMPARABLE_WITH_WARNING' | 'NOT_COMPARABLE'
  source_material: string
  target_material: string
  source_method: string
  target_method: string
  is_same_material_system: boolean
  is_same_synthesis_method: boolean
  is_same_solvent: boolean
  reason: string
}

export interface CatalogItem {
  id: string
  code: string
  name: string
  description?: string
  status: string
}

export const projectConfigService = {
  getMatrix: async (): Promise<ProjectMatrixRow[]> => {
    const res = await axios.get(`${API_BASE}/projects/matrix`)
    return res.data
  },

  getConfiguration: async (projectId: string): Promise<ProjectConfiguration> => {
    const res = await axios.get(`${API_BASE}/projects/${projectId}/configuration`)
    return res.data
  },

  compareProperties: async (
    sourceProjectCode: string,
    targetProjectCode: string,
    sourceProperty: string,
    targetProperty: string
  ): Promise<PropertyComparabilityResult> => {
    const res = await axios.post(`${API_BASE}/projects/compare`, {
      source_project_code: sourceProjectCode,
      target_project_code: targetProjectCode,
      source_property: sourceProperty,
      target_property: targetProperty,
    })
    return res.data
  },

  getMaterialsCatalog: async (): Promise<CatalogItem[]> => {
    const res = await axios.get(`${API_BASE}/catalogs/materials`)
    return res.data
  },

  getSolventsCatalog: async (): Promise<CatalogItem[]> => {
    const res = await axios.get(`${API_BASE}/catalogs/solvents`)
    return res.data
  },

  getExtractsCatalog: async (): Promise<CatalogItem[]> => {
    const res = await axios.get(`${API_BASE}/catalogs/extracts`)
    return res.data
  },

  getBiomassCatalog: async (): Promise<CatalogItem[]> => {
    const res = await axios.get(`${API_BASE}/catalogs/biomass`)
    return res.data
  },

  getSynthesisMethodsCatalog: async (): Promise<CatalogItem[]> => {
    const res = await axios.get(`${API_BASE}/catalogs/synthesis-methods`)
    return res.data
  },
}
