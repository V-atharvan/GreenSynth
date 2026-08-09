/**
 * GreenSynth Analytics — Dashboard Service
 */

import apiClient from './api'
import type { DashboardStats } from '@/types'

export const dashboardService = {
  async getStats(): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>('/dashboard/stats')
    return response.data
  },
}
