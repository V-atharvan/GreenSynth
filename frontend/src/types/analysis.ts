/**
 * GreenSynth Analytics — XRD Analysis TypeScript Types (Phase 4)
 */

export interface XRDPeak {
  id: string
  analysis_run_id: string
  peak_position: number // 2θ in degrees
  intensity: number
  fwhm: number | null // FWHM in degrees
  prominence: number | null
  width: number | null
  created_at: string
}

export interface CalculatedProperty {
  id: string
  sample_id: string
  analysis_run_id: string
  property_name: string
  value: number
  unit: string
  calculation_method: string
  formula: string | null
  assumptions: Record<string, any> | null
  input_values: Record<string, any> | null
  created_at: string
}

export type TransitionType = 'DIRECT_ALLOWED' | 'INDIRECT_ALLOWED'

export interface PreprocessingConfig {
  baseline_subtraction: boolean
  baseline_window: number
  smoothing: boolean
  savgol_window: number
  savgol_polyorder: number
}

export interface PeakDetectionConfig {
  prominence?: number | null
  min_height?: number | null
  min_distance: number
}

export interface ScherrerConfig {
  calculate_crystallite_size: boolean
  wavelength_nm: number
  shape_factor_k: number
}

export interface XRDAnalysisInput {
  preprocessing: PreprocessingConfig
  peak_detection: PeakDetectionConfig
  scherrer: ScherrerConfig
  notes?: string
}

export interface UVVisPreprocessingConfig {
  baseline_subtraction: boolean
  smoothing: boolean
  savgol_window: number
  savgol_polyorder: number
}

export interface TaucConfig {
  transition_type: TransitionType
  sample_thickness_cm?: number | null
  fit_energy_min_ev?: number | null
  fit_energy_max_ev?: number | null
}

export interface UVVisAnalysisInput {
  preprocessing: UVVisPreprocessingConfig
  tauc: TaucConfig
  notes?: string
}

export interface TaucDataPoint {
  wavelength_nm: number
  absorbance: number
  photon_energy_ev: number
  tauc_y: number
}

export interface TaucFitLinePoint {
  photon_energy_ev: number
  fit_y: number
}

export interface TaucProcessedResponse {
  analysis_run_id: string
  transition_type: string
  using_alpha: boolean
  thickness_cm?: number | null
  warning_msg?: string | null
  data_points: TaucDataPoint[]
  fit_line: TaucFitLinePoint[]
  band_gap_ev?: number | null
  r_squared?: number | null
  total_points: number
}

export type VoltageUnit = 'V' | 'mV'
export type CurrentUnit = 'A' | 'mA' | 'uA' | 'nA'
export type ResistanceUnit = 'Ohm' | 'kOhm' | 'MOhm'
export type LengthUnit = 'm' | 'cm' | 'mm' | 'um'
export type GeometryType = 'RECTANGULAR_BAR' | 'THIN_FILM' | 'TWO_PROBE_BAR'

export interface ElectricalUnitsConfig {
  voltage_unit: VoltageUnit
  current_unit: CurrentUnit
  resistance_unit: ResistanceUnit
  length_unit: LengthUnit
}

export interface SampleGeometryConfig {
  geometry_type: GeometryType
  length?: number | null
  width?: number | null
  thickness?: number | null
}

export interface ElectricalAnalysisInput {
  units: ElectricalUnitsConfig
  geometry: SampleGeometryConfig
  fit_voltage_min?: number | null
  fit_voltage_max?: number | null
  notes?: string
}

export interface IVDataPoint {
  voltage_v: number
  current_a: number
}

export interface IVFitLinePoint {
  current_a: number
  fit_voltage_v: number
}

export interface ElectricalProcessedResponse {
  analysis_run_id: string
  voltage_unit: string
  current_unit: string
  resistance_ohms?: number | null
  r_squared?: number | null
  resistivity_ohm_cm?: number | null
  conductivity_s_cm?: number | null
  warning_msg?: string | null
  data_points: IVDataPoint[]
  fit_line: IVFitLinePoint[]
  total_points: number
}

// ── FTIR Types ──────────────────────────────────────────────
export interface FTIRPreprocessingConfig {
  smoothing: boolean
  savgol_window: number
  savgol_polyorder: number
}

export interface FTIRPeakDetectionConfig {
  prominence?: number | null
  min_distance: number
}

export interface FTIRAnalysisInput {
  preprocessing: FTIRPreprocessingConfig
  peak_detection: FTIRPeakDetectionConfig
  notes?: string
}

export interface FTIRPeakItem {
  wavenumber_cm1: number
  signal_value: number
  prominence: number
  width_cm1: number
}

export interface FTIRDataPoint {
  wavenumber_cm1: number
  signal_value: number
}

export interface FTIRProcessedResponse {
  analysis_run_id: string
  signal_type: string
  data_points: FTIRDataPoint[]
  detected_peaks: FTIRPeakItem[]
  total_points: number
}

export interface FTIRAnnotationCreate {
  wavenumber_cm1: number
  label: string
  interpretation?: string | null
  confidence?: string | null
  notes?: string | null
}

export interface FTIRAnnotationResponse {
  id: string
  analysis_run_id: string
  wavenumber_cm1: number
  label: string
  interpretation?: string | null
  confidence?: string | null
  created_by?: string | null
  notes?: string | null
  created_at: string
}

// ── SEM Types ───────────────────────────────────────────────
export interface SEMMetadataUpdate {
  magnification?: number | null
  accelerating_voltage_kv?: number | null
  working_distance_mm?: number | null
  detector?: string | null
  scale_bar_nm?: number | null
  scale_bar_pixels?: number | null
  notes?: string | null
}

export interface SEMMetadataResponse {
  id: string
  raw_file_id: string
  magnification?: number | null
  accelerating_voltage_kv?: number | null
  working_distance_mm?: number | null
  detector?: string | null
  scale_bar_nm?: number | null
  scale_bar_pixels?: number | null
  nm_per_pixel?: number | null
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface SEMAnnotationCreate {
  annotation_type: string
  coordinates_json: Record<string, unknown>
  label: string
  notes?: string | null
}

export interface SEMAnnotationResponse {
  id: string
  raw_file_id: string
  annotation_type: string
  coordinates_json: Record<string, unknown>
  label: string
  notes?: string | null
  created_by?: string | null
  created_at: string
}

export interface SEMMeasurementCreate {
  pixel_distance: number
  label?: string | null
}

export interface SEMMeasurementResponse {
  id: string
  raw_file_id: string
  pixel_distance: number
  physical_distance_nm?: number | null
  unit: string
  label?: string | null
  calibration_info?: Record<string, unknown> | null
  created_by?: string | null
  created_at: string
}

// ── Phase 8 Analytics Types ────────────────────────────────
export interface DatasetCreateInput {
  project_id: string
  name: string
  description?: string
  sample_ids: string[]
  variables: string[]
  filters?: Record<string, unknown>
}

export interface DatasetResponse {
  id: string
  project_id: string
  name: string
  version: string
  description?: string | null
  sample_ids: string[]
  variables: string[]
  filters?: Record<string, unknown> | null
  created_by?: string | null
  created_at: string
}

export interface ComparisonTableCell {
  variable: string
  value?: number | string | null
  unit?: string | null
  status: string // MEASURED, CALCULATED, DETECTED, MISSING
  source?: string | null
}

export interface ComparisonTableRow {
  sample_id: string
  sample_code: string
  sample_name: string
  experiment_code: string
  synthesis_method?: string | null
  solvent?: string | null
  cells: Record<string, ComparisonTableCell>
}

export interface DataQualityReport {
  total_samples: number
  variables_evaluated: string[]
  missing_counts: Record<string, number>
  unit_consistency: string
  warnings: string[]
  status: string
}

export interface ComparisonTableResponse {
  dataset_id: string
  dataset_name: string
  version: string
  total_samples: number
  variables: string[]
  rows: ComparisonTableRow[]
  quality_report: DataQualityReport
}

export interface DescriptiveStatsItem {
  variable: string
  sample_size_n: number
  mean?: number | null
  median?: number | null
  std_dev?: number | null
  variance?: number | null
  min_val?: number | null
  max_val?: number | null
  val_range?: number | null
  missing_count: number
}

export interface CorrelationResponse {
  x_variable: string
  y_variable: string
  method: string
  pearson_r: number
  p_value?: number | null
  sample_size_n: number
  interpretation: string
  warnings: string[]
}

export interface RegressionResponse {
  x_variable: string
  y_variable: string
  method: string
  slope: number
  intercept: number
  r_squared: number
  mae: number
  rmse: number
  sample_size_n: number
  formula: string
  interpretation: string
  warnings: string[]
}

export interface GroupStatsItem {
  group_value: string
  sample_size_n: number
  mean?: number | null
  median?: number | null
  std_dev?: number | null
  min_val?: number | null
  max_val?: number | null
}

export interface GroupComparisonResponse {
  group_variable: string
  target_variable: string
  groups: GroupStatsItem[]
  interpretation: string
}

export interface OutlierItem {
  sample_id: string
  sample_code: string
  variable: string
  value: number
  method: string
  score: number
}

export interface OutlierReportResponse {
  variable: string
  method: string
  total_inspected: number
  outliers_found: OutlierItem[]
}

export interface StatisticalAnalysisRunInput {
  analysis_type: string // DESCRIPTIVE, CORRELATION, REGRESSION, GROUP_COMPARISON, OUTLIERS
  x_variable?: string
  y_variable?: string
  group_variable?: string
}

export interface StatisticalAnalysisResponse {
  id: string
  dataset_id: string
  analysis_run_id?: string | null
  analysis_type: string
  x_variable?: string | null
  y_variable?: string | null
  group_variable?: string | null
  method: string
  sample_size: number
  results_json: Record<string, unknown>
  assumptions_json?: Record<string, unknown> | null
  warnings_json?: Record<string, unknown> | null
  created_by?: string | null
  created_at: string
}

export interface XRDAnalysisRun {
  id: string
  characterization_id: string
  input_file_id: string
  analysis_type: string
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED'
  software_version: string
  parameters: Record<string, any> | null
  assumptions: Record<string, any> | null
  notes: string | null
  error_message: string | null
  started_at: string
  completed_at: string | null
  peaks: XRDPeak[]
  calculated_properties: CalculatedProperty[]
}

export interface XRDDataPoint {
  two_theta: number
  raw_intensity: number
  processed_intensity: number | null
}

export interface XRDProcessedDataResponse {
  analysis_run_id: string
  data_points: XRDDataPoint[]
  total_points: number
}
