/**
 * GreenSynth Analytics — Characterization & RawFile TypeScript Types (Phase 3)
 */

export type TechniqueType = 'XRD' | 'UV_VIS' | 'FTIR' | 'SEM' | 'ELECTRICAL'

export type CharacterizationStatus =
  | 'UPLOADED'
  | 'READY_FOR_ANALYSIS'
  | 'PROCESSING'
  | 'ANALYZED'
  | 'ARCHIVED'

export interface RawFile {
  id: string
  characterization_id: string
  sample_id: string
  original_filename: string
  stored_filename: string
  file_extension: string
  mime_type: string | null
  file_size: number
  checksum: string
  storage_path: string
  uploaded_at: string
  uploaded_by: string | null
  status: string
}

export interface Characterization {
  id: string
  sample_id: string
  technique: TechniqueType
  characterization_date: string | null
  operator: string | null
  instrument_name: string | null
  instrument_model: string | null
  instrument_id: string | null
  notes: string | null
  status: CharacterizationStatus
  raw_files: RawFile[]
  created_at: string
  updated_at: string
}

export interface CharacterizationCreate {
  sample_id: string
  technique: TechniqueType
  characterization_date?: string
  operator?: string
  instrument_name?: string
  instrument_model?: string
  instrument_id?: string
  notes?: string
}

export interface CharacterizationUpdate {
  characterization_date?: string
  operator?: string
  instrument_name?: string
  instrument_model?: string
  instrument_id?: string
  notes?: string
  status?: CharacterizationStatus
}

export const TECHNIQUE_ALLOWED_EXTENSIONS: Record<TechniqueType, string[]> = {
  XRD: ['csv', 'txt', 'xlsx', 'json'],
  UV_VIS: ['csv', 'txt', 'xlsx', 'json'],
  FTIR: ['csv', 'txt', 'xlsx', 'json'],
  ELECTRICAL: ['csv', 'txt', 'xlsx', 'json'],
  SEM: ['png', 'jpg', 'jpeg', 'tiff', 'tif', 'pdf'],
}
