/**
 * GreenSynth Analytics — Frontend Method Configuration Registry
 *
 * Provides canonical method-aware parameter mappings, display labels,
 * and project specifications (P1 through P8).
 */

export type SynthesisMethod = 'SOL_GEL' | 'HYDROTHERMAL' | 'SPRAY_PYROLYSIS'

export interface ProjectMethodSpec {
  project_code: string
  name: string
  material_system: 'CuO' | 'SILICA_SILICON'
  material: string
  method: SynthesisMethod
  solvent: 'ETHANOL' | 'ACETONE'
  biomass?: string
  extract: string
}

export const METHOD_DISPLAY_NAMES: Record<SynthesisMethod, string> = {
  SOL_GEL: 'Sol-Gel',
  HYDROTHERMAL: 'Hydrothermal',
  SPRAY_PYROLYSIS: 'Spray Pyrolysis',
}

export const PROJECT_METHOD_MATRIX: Record<string, ProjectMethodSpec> = {
  P1: {
    project_code: 'P1',
    name: 'CuO Phytochemical Synthesis via Sol-Gel using Ethanol',
    material_system: 'CuO',
    material: 'CuO',
    method: 'SOL_GEL',
    solvent: 'ETHANOL',
    extract: 'Mulberry',
  },
  P2: {
    project_code: 'P2',
    name: 'CuO Phytochemical Synthesis via Sol-Gel using Acetone',
    material_system: 'CuO',
    material: 'CuO',
    method: 'SOL_GEL',
    solvent: 'ACETONE',
    extract: 'Mulberry',
  },
  P3: {
    project_code: 'P3',
    name: 'CuO Phytochemical Synthesis via Hydrothermal using Ethanol',
    material_system: 'CuO',
    material: 'CuO',
    method: 'HYDROTHERMAL',
    solvent: 'ETHANOL',
    extract: 'Mulberry',
  },
  P4: {
    project_code: 'P4',
    name: 'CuO Phytochemical Synthesis via Hydrothermal using Acetone',
    material_system: 'CuO',
    material: 'CuO',
    method: 'HYDROTHERMAL',
    solvent: 'ACETONE',
    extract: 'Mulberry',
  },
  P5: {
    project_code: 'P5',
    name: 'Biomass-Derived Silica/Silicon Hydrothermal Synthesis using Ethanol',
    material_system: 'SILICA_SILICON',
    material: 'Silica / Silicon',
    method: 'HYDROTHERMAL',
    solvent: 'ETHANOL',
    biomass: 'Rice husk',
    extract: 'Mulberry',
  },
  P6: {
    project_code: 'P6',
    name: 'Biomass-Derived Silica/Silicon Hydrothermal Synthesis using Acetone',
    material_system: 'SILICA_SILICON',
    material: 'Silica / Silicon',
    method: 'HYDROTHERMAL',
    solvent: 'ACETONE',
    biomass: 'Rice husk',
    extract: 'Mulberry',
  },
  P7: {
    project_code: 'P7',
    name: 'Phytochemical synthesis of semiconducting copper oxide using mulberry extract in ethanol by spray pyrolysis',
    material_system: 'CuO',
    material: 'CuO',
    method: 'SPRAY_PYROLYSIS',
    solvent: 'ETHANOL',
    extract: 'Mulberry',
  },
  P8: {
    project_code: 'P8',
    name: 'CuO Phytochemical Synthesis via Spray Pyrolysis using Acetone',
    material_system: 'CuO',
    material: 'CuO',
    method: 'SPRAY_PYROLYSIS',
    solvent: 'ACETONE',
    extract: 'Mulberry',
  },
}

export function getProjectMethodSpec(projectCode?: string): ProjectMethodSpec {
  if (!projectCode) return PROJECT_METHOD_MATRIX.P7
  const code = projectCode.toUpperCase().trim()
  return PROJECT_METHOD_MATRIX[code] ?? PROJECT_METHOD_MATRIX.P7
}

export function getDynamicParameterLabel(parameterCode: string, projectCode?: string): string {
  const spec = getProjectMethodSpec(projectCode)
  if (parameterCode === 'solvent_volume' || parameterCode === 'ethanol_volume') {
    return spec.solvent === 'ACETONE' ? 'Acetone Volume' : 'Ethanol Volume'
  }
  return ''
}

export const PARAMETER_SECTION_MAP: Record<string, { title: string; icon?: string }> = {
  // A. Precursor & Extract
  copper_precursor_salt: { title: 'A. Precursor & Extract' },
  copper_precursor: { title: 'A. Precursor & Extract' },
  precursor_concentration: { title: 'A. Precursor & Extract' },
  precursor_solution_volume: { title: 'A. Precursor & Extract' },
  precursor_volume: { title: 'A. Precursor & Extract' },
  mulberry_extract_concentration: { title: 'A. Precursor & Extract' },
  extract_concentration: { title: 'A. Precursor & Extract' },
  mulberry_extract_volume: { title: 'A. Precursor & Extract' },
  extract_volume: { title: 'A. Precursor & Extract' },

  // Biomass
  biomass_source_mass_g: { title: 'A. Biomass Preparation' },

  // B. Solvent
  ethanol_volume: { title: 'B. Solvent' },
  solvent_volume: { title: 'B. Solvent' },

  // Deposition / Synthesis Conditions
  substrate_type: { title: 'C. Deposition Conditions' },
  substrate_temperature_c: { title: 'C. Deposition Conditions' },
  substrate_temperature: { title: 'C. Deposition Conditions' },
  spray_duration_min: { title: 'C. Deposition Conditions' },
  nozzle_substrate_distance_cm: { title: 'C. Deposition Conditions' },

  // Sol-Gel specific
  sol_gel_aging_temperature_c: { title: 'C. Sol-Gel Conditions' },
  sol_gel_aging_time_h: { title: 'C. Sol-Gel Conditions' },
  calcination_temperature_c: { title: 'D. Calcination Conditions' },
  calcination_duration_h: { title: 'D. Calcination Conditions' },

  // Hydrothermal specific
  hydrothermal_temperature_c: { title: 'C. Hydrothermal Conditions' },
  hydrothermal_reaction_time_h: { title: 'C. Hydrothermal Conditions' },
  autoclave_fill_factor_pct: { title: 'C. Hydrothermal Conditions' },

  // Spray System
  spray_rate_ml_min: { title: 'D. Spray System' },
  spray_rate: { title: 'D. Spray System' },
  carrier_gas_pressure_kpa: { title: 'D. Spray System' },
  spray_cycles: { title: 'D. Spray System' },

  // Ambient
  ambient_temperature_c: { title: 'E. Ambient Conditions' },
  ambient_relative_humidity: { title: 'E. Ambient Conditions' },
}
