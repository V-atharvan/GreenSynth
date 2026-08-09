/**
 * GreenSynth Analytics — Characterization & Raw File Service
 */

import apiClient from './api'
import type {
  Characterization,
  CharacterizationCreate,
  RawFile,
} from '@/types'

export const characterizationService = {
  /**
   * Create a new characterization run record for a sample.
   */
  async createCharacterization(
    data: CharacterizationCreate
  ): Promise<Characterization> {
    const response = await apiClient.post<Characterization>(
      '/characterizations',
      data
    )
    return response.data
  },

  /**
   * Get single characterization record by ID with associated raw files.
   */
  async getCharacterization(id: string): Promise<Characterization> {
    const response = await apiClient.get<Characterization>(
      `/characterizations/${id}`
    )
    return response.data
  },

  /**
   * List all characterization runs linked to a sample.
   */
  async listSampleCharacterizations(
    sampleId: string
  ): Promise<Characterization[]> {
    const response = await apiClient.get<Characterization[]>(
      `/samples/${sampleId}/characterizations`
    )
    return response.data
  },

  /**
   * Upload an immutable raw laboratory data file for a characterization run.
   */
  async uploadRawFile(
    characterizationId: string,
    file: File
  ): Promise<RawFile> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<RawFile>(
      `/characterizations/${characterizationId}/files`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  /**
   * Fetch raw file metadata.
   */
  async getFileMetadata(fileId: string): Promise<RawFile> {
    const response = await apiClient.get<RawFile>(`/files/${fileId}`)
    return response.data
  },

  /**
   * Return original file download URL.
   */
  getDownloadUrl(fileId: string): string {
    const baseUrl = apiClient.defaults.baseURL || '/api/v1'
    return `${baseUrl}/files/${fileId}/download`
  },
}
