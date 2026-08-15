/**
 * GreenSynth Analytics — Project Service
 *
 * All API calls for the /projects endpoints.
 * Components must use this service, not call apiClient directly.
 */

import apiClient from './api'
import type { Project, ProjectCreate, ProjectSummary, ProjectUpdate } from '@/types'

export const projectService = {
  /**
   * Fetch all active projects.
   */
  async getAll(includeArchived = false): Promise<ProjectSummary[]> {
    const response = await apiClient.get<ProjectSummary[]>('/projects/', {
      params: { include_archived: includeArchived },
    })
    return response.data
  },

  async getProjects(includeArchived = false): Promise<ProjectSummary[]> {
    return projectService.getAll(includeArchived)
  },

  /**
   * Fetch a single project by ID.
   */
  async getById(id: string): Promise<Project> {
    const response = await apiClient.get<Project>(`/projects/${id}`)
    return response.data
  },

  /**
   * Create a new research project.
   */
  async create(data: ProjectCreate): Promise<Project> {
    const response = await apiClient.post<Project>('/projects/', data)
    return response.data
  },

  /**
   * Update an existing project.
   */
  async update(id: string, data: ProjectUpdate): Promise<Project> {
    const response = await apiClient.put<Project>(`/projects/${id}`, data)
    return response.data
  },

  /**
   * Archive a project (soft delete).
   */
  async archive(id: string): Promise<void> {
    await apiClient.delete(`/projects/${id}`)
  },
}
