/**
 * GreenSynth Analytics — Sample Service
 */

import apiClient from './api'
import type { Sample, SampleCreate, SampleSummary, SampleUpdate } from '@/types'

export const sampleService = {
  async getAll(params?: {
    experiment_id?: string
    status?: string
    include_archived?: boolean
  }): Promise<SampleSummary[]> {
    const response = await apiClient.get<SampleSummary[]>('/samples/', { params })
    return response.data
  },

  async getById(id: string): Promise<Sample> {
    const response = await apiClient.get<Sample>(`/samples/${id}`)
    return response.data
  },

  async create(data: SampleCreate): Promise<Sample> {
    const response = await apiClient.post<Sample>('/samples/', data)
    return response.data
  },

  async update(id: string, data: SampleUpdate): Promise<Sample> {
    const response = await apiClient.put<Sample>(`/samples/${id}`, data)
    return response.data
  },

  async archive(id: string): Promise<void> {
    await apiClient.delete(`/samples/${id}`)
  },
}
