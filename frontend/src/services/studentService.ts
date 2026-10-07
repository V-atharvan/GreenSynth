/**
 * GreenSynth Analytics - Student Portal Service
 *
 * Connects to the /api/v1/student/* endpoints.
 */

import apiClient from './api'

export interface StudentProfile {
  id: string
  email: string
  full_name: string
  department?: string | null
  roll_number?: string | null
  account_type: string
  is_active: boolean
  created_at: string
}

export interface StudentProject {
  id: string
  project_code: string
  name: string
  description?: string | null
  material: string
  extract?: string | null
  solvent?: string | null
  synthesis_method: string
  status: string
  created_at: string
}

export interface StudentGroup {
  group_id: string
  group_name: string
  project_code: string
  leader_name: string
  leader_email: string
  member_count: number
  max_members: number
  members?: { id: string; full_name: string; email: string; role: string }[]
  created_at: string
}

export interface StudentDashboardStats {
  total_projects: number
  total_experiments: number
  total_samples: number
  experiments_by_status: Record<string, number>
  projects_by_status: Record<string, number>
  recent_experiments: {
    id: string
    experiment_code: string
    title: string
    status: string
    created_at: string
  }[]
}

export const studentService = {
  async getProfile(): Promise<{ data: StudentProfile; message: string }> {
    const response = await apiClient.get('/student/me')
    return response.data
  },

  async getProject(): Promise<{ data: StudentProject; message: string }> {
    const response = await apiClient.get('/student/project')
    return response.data
  },

  async getGroup(): Promise<{ data: StudentGroup; message: string }> {
    const response = await apiClient.get('/student/group')
    return response.data
  },

  async getDashboardStats(): Promise<StudentDashboardStats> {
    const response = await apiClient.get('/student/dashboard')
    return response.data
  },
}
