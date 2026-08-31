import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import React from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { ProjectProvider } from '../context/ProjectContext'
import ProtectedRoute from '../components/ProtectedRoute'
import { authService } from '../services/authService'
import { AUTH_TOKEN_KEY } from '../services/api'
import type { UserProfile } from '../types'

vi.mock('../services/authService', () => ({
  authService: {
    getCurrentUser: vi.fn(),
  },
}))

const mockProfile: UserProfile = {
  id: 'user-123',
  username: 'leader_alice',
  email: 'alice@greensynth.edu',
  full_name: 'Dr. Alice',
  department: 'Materials Science',
  phone: '1234567890',
  roll_number: 'ROLL-01',
  role: 'RESEARCHER',
  is_active: true,
  created_at: '2026-08-30T00:00:00Z',
  memberships: [
    {
      group_id: 'group-123',
      group_name: 'Solar Nanotech Lab',
      is_leader: true,
      status: 'ACTIVE',
      project_id: 'proj-123',
      project_code: 'P7',
      joined_at: '2026-08-30T00:00:00Z',
    },
  ],
}

describe('ProtectedRoute Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('redirects unauthenticated user to /login', async () => {
    render(
      <MemoryRouter initialEntries={['/protected-research']}>
        <AuthProvider>
          <ProjectProvider>
            <Routes>
              <Route path="/login" element={<div>LOGIN_PAGE_VIEW</div>} />
              <Route element={<ProtectedRoute />}>
                <Route path="/protected-research" element={<div>SECRET_RESEARCH_CONTENT</div>} />
              </Route>
            </Routes>
          </ProjectProvider>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('LOGIN_PAGE_VIEW')).toBeDefined()
      expect(screen.queryByText('SECRET_RESEARCH_CONTENT')).toBeNull()
    })
  })

  it('renders protected content when user is authenticated', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'valid_token')
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockProfile)

    render(
      <MemoryRouter initialEntries={['/protected-research']}>
        <AuthProvider>
          <ProjectProvider>
            <Routes>
              <Route path="/login" element={<div>LOGIN_PAGE_VIEW</div>} />
              <Route element={<ProtectedRoute />}>
                <Route path="/protected-research" element={<div>SECRET_RESEARCH_CONTENT</div>} />
              </Route>
            </Routes>
          </ProjectProvider>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('SECRET_RESEARCH_CONTENT')).toBeDefined()
      expect(screen.queryByText('LOGIN_PAGE_VIEW')).toBeNull()
    })
  })
})
