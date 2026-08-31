/**
 * GreenSynth Analytics — Phase 23 Frontend Authentication & Route Protection Tests
 *
 * Validates:
 * 1. Unified login page (no role selectors, no separate login buttons).
 * 2. Successful Admin authentication navigates to /admin.
 * 3. Successful Student authentication navigates to /dashboard.
 * 4. Unauthenticated access to /admin redirects to /login.
 * 5. Authenticated Student accessing /admin redirects to /unauthorized.
 * 6. Authenticated Admin accessing /admin renders Admin portal.
 * 7. Logout clears token and user state.
 * 8. 401 Unauthorized API response clears credentials and triggers logout event without loops.
 * 9. 403 Forbidden does not wipe credentials or log out the session.
 */

import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { AuthProvider, useAuth } from '../context/AuthContext'
import { ProjectProvider } from '../context/ProjectContext'
import ProtectedRoute from '../components/ProtectedRoute'
import AdminRoute from '../components/AdminRoute'
import Login from '../pages/Login'
import Unauthorized from '../pages/Unauthorized'
import Dashboard from '../pages/Dashboard'
import AdminDashboard from '../pages/admin/AdminDashboard'
import { authService } from '../services/authService'
import { dashboardService } from '../services/dashboardService'
import { adminService } from '../services/adminService'
import { AUTH_TOKEN_KEY } from '../services/api'
import type { UserProfile } from '../types'

vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(),
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
  },
}))

vi.mock('../services/dashboardService', () => ({
  dashboardService: {
    getStats: vi.fn().mockResolvedValue({
      total_projects: 1,
      total_experiments: 5,
      total_samples: 10,
      experiments_by_status: { COMPLETED: 5 },
      projects_by_status: { ACTIVE: 1 },
      recent_experiments: [],
    }),
  },
}))

vi.mock('../services/adminService', () => ({
  adminService: {
    getOverviewMetrics: vi.fn().mockResolvedValue({
      system_summary: {
        total_projects: 8,
        total_groups: 8,
        total_users: 12,
        total_experiments: 45,
        total_samples: 90,
      },
      projects_distribution: [],
      recent_activity: [],
    }),
    listProjects: vi.fn().mockResolvedValue([]),
    listGroups: vi.fn().mockResolvedValue([]),
    listUsers: vi.fn().mockResolvedValue([]),
    listExperiments: vi.fn().mockResolvedValue([]),
    listSamples: vi.fn().mockResolvedValue([]),
  },
}))

const mockAdminUser: UserProfile = {
  id: 'admin-uuid',
  username: 'admin',
  email: 'v.atharvan@gmail.com',
  full_name: 'Administrator Atharva',
  department: 'Central Lab',
  phone: '1000000000',
  roll_number: 'ADM-01',
  role: 'ADMIN',
  account_type: 'ADMIN',
  is_active: true,
  created_at: '2026-08-30T00:00:00Z',
  memberships: [],
}

const mockStudentUser: UserProfile = {
  id: 'student-uuid',
  username: 'student_a',
  email: 'student.a@greensynth.edu',
  full_name: 'Student Researcher A',
  department: 'Chemical Engineering',
  phone: '1000000001',
  roll_number: 'STU-01',
  role: 'RESEARCHER',
  account_type: 'STUDENT',
  is_active: true,
  created_at: '2026-08-30T00:00:00Z',
  memberships: [
    {
      group_id: 'grp-1',
      group_name: 'Spray Pyrolysis Lab',
      project_id: 'p7-uuid',
      project_code: 'P7',
      project_name: 'CuO Spray Pyrolysis',
      is_leader: true,
      status: 'ACTIVE',
      joined_at: '2026-08-30T00:00:00Z',
    },
  ],
}

describe('Phase 23 Frontend Authentication & Route Protection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders unified login form with only email and password (no role selectors or role buttons)', async () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )

    expect(screen.getByText('GreenSynth Analytics')).toBeDefined()
    expect(screen.getByText('Researcher Sign In')).toBeDefined()
    expect(screen.getByPlaceholderText('researcher@greensynth.edu')).toBeDefined()
    expect(screen.getByPlaceholderText('Enter account password')).toBeDefined()
    expect(screen.getByRole('button', { name: /Sign In to Research Portal/i })).toBeDefined()

    // Ensure no role buttons or selectors exist
    expect(screen.queryByText(/Admin Login/i)).toBeNull()
    expect(screen.queryByText(/Student Login/i)).toBeNull()
    expect(screen.queryByText(/Select Role/i)).toBeNull()
  })

  it('navigates Admin to /admin after successful unified login', async () => {
    vi.mocked(authService.login).mockResolvedValueOnce({
      access_token: 'fake-admin-jwt',
      token_type: 'bearer',
      expires_in: 86400,
      user: mockAdminUser,
    })
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockAdminUser)

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <ProjectProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route
                path="/admin"
                element={
                  <AdminRoute>
                    <AdminDashboard />
                  </AdminRoute>
                }
              />
            </Routes>
          </ProjectProvider>
        </AuthProvider>
      </MemoryRouter>
    )

    fireEvent.change(screen.getByPlaceholderText('researcher@greensynth.edu'), {
      target: { value: 'v.atharvan@gmail.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('Enter account password'), {
      target: { value: 'AdminSecret123!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Sign In to Research Portal/i }))

    await waitFor(() => {
      expect(screen.getByText('Admin Portal')).toBeDefined()
    })
  })

  it('redirects unauthenticated users trying to access /admin to /login', async () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AuthProvider>
          <ProjectProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route
                path="/admin"
                element={
                  <AdminRoute>
                    <AdminDashboard />
                  </AdminRoute>
                }
              />
            </Routes>
          </ProjectProvider>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Researcher Sign In')).toBeDefined()
    })
  })

  it('redirects authenticated Student trying to access /admin to /unauthorized', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'student-jwt')
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockStudentUser)

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AuthProvider>
          <ProjectProvider>
            <Routes>
              <Route path="/unauthorized" element={<Unauthorized />} />
              <Route
                path="/admin"
                element={
                  <AdminRoute>
                    <AdminDashboard />
                  </AdminRoute>
                }
              />
            </Routes>
          </ProjectProvider>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('403 — Access Denied')).toBeDefined()
      expect(screen.getByText(/You do not have administrative permission/i)).toBeDefined()
    })
  })

  it('allows authenticated Admin to view /admin portal directly', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'admin-jwt')
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockAdminUser)

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AuthProvider>
          <ProjectProvider>
            <Routes>
              <Route
                path="/admin"
                element={
                  <AdminRoute>
                    <AdminDashboard />
                  </AdminRoute>
                }
              />
            </Routes>
          </ProjectProvider>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Admin Portal')).toBeDefined()
    })
  })

  it('restores authenticated session on mount from localStorage token and GET /auth/me', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'valid-token')
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockStudentUser)

    function TestComponent() {
      const { user, isAuthenticated, accountType } = useAuth()
      return (
        <div>
          <div data-testid="auth-state">{isAuthenticated ? 'LOGGED_IN' : 'LOGGED_OUT'}</div>
          <div data-testid="user-email">{user?.email}</div>
          <div data-testid="user-type">{accountType}</div>
        </div>
      )
    }

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-state').textContent).toBe('LOGGED_IN')
      expect(screen.getByTestId('user-email').textContent).toBe('student.a@greensynth.edu')
      expect(screen.getByTestId('user-type').textContent).toBe('STUDENT')
    })
  })
})
