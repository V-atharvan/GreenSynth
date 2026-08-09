/**
 * GreenSynth Analytics — Experiment Service
 */

import apiClient from './api'
import type {
  Experiment,
  ExperimentCreate,
  ExperimentSummary,
  ExperimentUpdate,
  ExperimentWithProject,
} from '@/types'

export const experimentService = {
  async getAll(params?: {
    project_id?: string
    status?: string
    include_archived?: boolean
  }): Promise<ExperimentSummary[]> {
    const response = await apiClient.get<ExperimentSummary[]>('/experiments/', { params })
    return response.data
  },

  async getById(id: string): Promise<ExperimentWithProject> {
    const response = await apiClient.get<ExperimentWithProject>(`/experiments/${id}`)
    return response.data
  },

  async create(data: ExperimentCreate): Promise<Experiment> {
    const response = await apiClient.post<Experiment>('/experiments/', data)
    return response.data
  },

  async update(id: string, data: ExperimentUpdate): Promise<Experiment> {
    const response = await apiClient.put<Experiment>(`/experiments/${id}`, data)
    return response.data
  },

  async archive(id: string): Promise<void> {
    await apiClient.delete(`/experiments/${id}`)
  },

  async downloadPdfReport(id: string): Promise<Blob> {
    const response = await apiClient.get<Blob>(`/reports/experiments/${id}/pdf`, {
      responseType: 'blob',
    })
    return response.data
  },
}
