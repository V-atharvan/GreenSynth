import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import Dashboard from '../pages/Dashboard'
import { dashboardService } from '../services/dashboardService'

vi.mock('../services/dashboardService', () => ({
  dashboardService: {
    getStats: vi.fn(),
  },
}))

describe('Dashboard Page', () => {
  it('displays real database values returned from service', async () => {
    vi.mocked(dashboardService.getStats).mockResolvedValueOnce({
      total_projects: 5,
      total_experiments: 12,
      total_samples: 25,
      experiments_by_status: { PLANNED: 4, IN_PROGRESS: 3, COMPLETED: 5 },
      projects_by_status: { ACTIVE: 5 },
      recent_experiments: [
        {
          id: '1234',
          project_id: 'p1',
          experiment_code: 'P7-EXP-999',
          title: 'Test CuO Run',
          status: 'COMPLETED',
          experiment_date: '2026-08-01',
          researcher: 'Dr. Lab',
          created_at: '2026-08-01T00:00:00Z',
        },
      ],
    })

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Research Dashboard')).toBeDefined()
      expect(screen.getByText('12')).toBeDefined()
      expect(screen.getByText('25')).toBeDefined()
      expect(screen.getByText('P7-EXP-999')).toBeDefined()
    })
  })
})
