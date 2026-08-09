import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from '../App'
import { dashboardService } from '../services/dashboardService'

vi.mock('../services/dashboardService', () => ({
  dashboardService: {
    getStats: vi.fn().mockResolvedValue({
      total_projects: 1,
      total_experiments: 2,
      total_samples: 3,
      experiments_by_status: { PLANNED: 1, COMPLETED: 1 },
      projects_by_status: { ACTIVE: 1 },
      recent_experiments: [],
    }),
  },
}))

describe('App Startup & Navigation', () => {
  it('renders without crashing and displays layout brand header', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('GreenSynth')).toBeDefined()
    })
  })
})
