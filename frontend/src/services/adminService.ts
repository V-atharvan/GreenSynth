/**
 * GreenSynth Analytics — Administrator API Service
 *
 * Provides typed client calls to backend Administrator endpoints (/api/v1/admin/*).
 * All endpoints require Bearer JWT authentication and ADMIN account authorization.
 */

import apiClient from './api'
import type {
  Experiment,
  GroupDetail,
  Project,
  Sample,
  User,
} from '@/types'

export interface AdminOverviewStats {
  total_projects: number
  total_groups: number
  total_students: number
  total_experiments: number
  total_samples: number
  total_characterizations: number
  total_ml_models: number
  total_recommendations: number
  total_optimization_runs: number
}

export const adminService = {
  /**
   * Retrieves system-wide aggregate metrics for Platform Administrators.
   */
  async getOverview(): Promise<AdminOverviewStats> {
    const response = await apiClient.get<{
      data: AdminOverviewStats
      message: string
    }>('/admin/overview')
    return response.data.data
  },

  /**
   * Retrieves all active synthesis projects (P1–P8).
   */
  async getProjects(): Promise<Project[]> {
    const response = await apiClient.get<{
      data: Project[]
      message: string
    }>('/admin/projects')
    return response.data.data
  },

  /**
   * Retrieves all registered research groups across all projects.
   */
  async getGroups(): Promise<GroupDetail[]> {
    const response = await apiClient.get<{
      data: GroupDetail[]
      message: string
    }>('/admin/groups')
    return response.data.data
  },

  /**
   * Retrieves all registered student/researcher accounts.
   */
  async getUsers(): Promise<User[]> {
    const response = await apiClient.get<{
      data: User[]
      message: string
    }>('/admin/users')
    return response.data.data
  },

  /**
   * Retrieves experiments system-wide with optional project filtering.
   */
  async getExperiments(projectId?: string): Promise<Experiment[]> {
    const response = await apiClient.get<{
      data: Experiment[]
      message: string
    }>('/admin/experiments', {
      params: projectId ? { project_id: projectId } : undefined,
    })
    return response.data.data
  },

  /**
   * Retrieves synthesized samples system-wide with optional experiment filtering.
   */
  async getSamples(experimentId?: string): Promise<Sample[]> {
    const response = await apiClient.get<{
      data: Sample[]
      message: string
    }>('/admin/samples', {
      params: experimentId ? { experiment_id: experimentId } : undefined,
    })
    return response.data.data
  },

  /**
   * Updates user account active status (Admin only).
   */
  async updateUserStatus(userId: string, isActive: boolean): Promise<User> {
    const response = await apiClient.patch<{
      data: User
      message: string
    }>(`/admin/users/${userId}/status`, { is_active: isActive })
    return response.data.data
  },
}

export default adminService

