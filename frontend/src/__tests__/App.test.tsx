import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import App from '../App'
import { dashboardService } from '../services/dashboardService'
import { authService } from '../services/authService'

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

vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(),
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
  },
}))

describe('App Startup & Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders without crashing and displays brand header', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getAllByText(/GreenSynth/i).length).toBeGreaterThan(0)
    })
  })
})
