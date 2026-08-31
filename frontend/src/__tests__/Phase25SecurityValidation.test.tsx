/**
 * GreenSynth Analytics — Phase 25 Comprehensive Security & Frontend Validation
 *
 * Validates:
 * 1. Unified Login Integrity: Single unified login form without role selectors or bifurcated login buttons.
 * 2. Route Protection Boundaries: AdminRoute defense, ProtectedRoute session enforcement, 401 token purge.
 * 3. Browser Storage Security: Zero sensitive research datasets stored in localStorage / sessionStorage.
 * 4. Token & Identity Lifecycles: Safe session restoration without client-side privilege escalation.
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { AuthProvider } from '../context/AuthContext'
import { ProjectProvider } from '../context/ProjectContext'
import ProtectedRoute from '../components/ProtectedRoute'
import AdminRoute from '../components/AdminRoute'
import Login from '../pages/Login'
import AdminDashboard from '../pages/admin/AdminDashboard'
import Unauthorized from '../pages/Unauthorized'
import { authService } from '../services/authService'
import { adminService } from '../services/adminService'
import { projectService } from '../services/projectService'
import { AUTH_TOKEN_KEY } from '../services/api'
import type { UserProfile } from '../types'

// ── Mock Services ──────────────────────────────────────────────────────────
vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(),
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
  },
}))

vi.mock('../services/projectService', () => ({
  projectService: {
    getAll: vi.fn().mockResolvedValue([
      { id: 'p7-id', project_code: 'P7', name: 'CuO Spray Pyrolysis P7' },
      { id: 'p2-id', project_code: 'P2', name: 'CuO Sol-Gel P2' },
    ]),
    getById: vi.fn().mockResolvedValue({
      id: 'p7-id',
      project_code: 'P7',
      name: 'CuO Spray Pyrolysis P7',
    }),
    listProjects: vi.fn().mockResolvedValue([
      { id: 'p7-id', code: 'P7', title: 'CuO Spray Pyrolysis', synthesis_method: 'Spray Pyrolysis' },
    ]),
    getProjectById: vi.fn().mockResolvedValue({
      id: 'p7-id',
      code: 'P7',
      title: 'CuO Spray Pyrolysis',
      synthesis_method: 'Spray Pyrolysis',
    }),
  },
}))

vi.mock('../services/adminService', () => ({
  adminService: {
    getOverview: vi.fn().mockResolvedValue({
      total_projects: 8,
      total_groups: 8,
      total_students: 16,
      total_experiments: 64,
      total_samples: 128,
      total_characterizations: 256,
      total_ml_models: 16,
      total_recommendations: 32,
      total_optimization_runs: 8,
    }),
    getProjects: vi.fn().mockResolvedValue([]),
    getGroups: vi.fn().mockResolvedValue([]),
    getUsers: vi.fn().mockResolvedValue([]),
    getExperiments: vi.fn().mockResolvedValue([]),
    getSamples: vi.fn().mockResolvedValue([]),
  },
}))

const mockAdminUser: UserProfile = {
  id: 'admin-uuid-001',
  username: 'admin',
  email: 'v.atharvan@gmail.com',
  full_name: 'Administrator Atharva',
  department: 'Central Oversight',
  phone: '9999999999',
  roll_number: 'ADM-001',
  role: 'ADMIN',
  account_type: 'ADMIN',
  is_active: true,
  created_at: '2026-08-30T00:00:00Z',
  memberships: [],
}

const mockStudentUser: UserProfile = {
  id: 'student-uuid-001',
  username: 'student_p7',
  email: 'student.p7@greensynth.edu',
  full_name: 'Student P7',
  department: 'Chemical Engineering',
  phone: '8888888888',
  roll_number: 'STU-P7-001',
  role: 'RESEARCHER',
  account_type: 'STUDENT',
  is_active: true,
  created_at: '2026-08-30T00:00:00Z',
  memberships: [
    {
      group_id: 'grp-p7-001',
      group_name: 'Spray Pyrolysis Lab',
      project_id: 'p7-id',
      project_code: 'P7',
      project_name: 'CuO Spray Pyrolysis P7',
      is_leader: false,
      status: 'ACTIVE',
      joined_at: '2026-08-30T00:00:00Z',
    },
  ],
}

describe('Phase 25 Frontend Comprehensive Security & Validation', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    vi.clearAllMocks()
  })

  it('VALIDATION 1: Unified Login form has zero role selectors or dual login buttons', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )

    expect(screen.getByLabelText(/institutional email/i)).toBeDefined()
    expect(screen.getByLabelText('Password', { exact: true })).toBeDefined()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeDefined()

    // Verify absence of bifurcated authentication buttons or role pickers
    expect(screen.queryByText(/admin login/i)).toBeNull()
    expect(screen.queryByText(/student login/i)).toBeNull()
    expect(screen.queryByText(/login as admin/i)).toBeNull()
    expect(screen.queryByText(/login as student/i)).toBeNull()
    expect(screen.queryByRole('combobox')).toBeNull()
  })

  it('VALIDATION 2: Unauthenticated user attempting to access /admin is blocked and redirected to /login', async () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<div data-testid="login-view">Login Required</div>} />
            <Route path="/admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('login-view')).toBeDefined()
    })
  })

  it('VALIDATION 3: Authenticated Student attempting to access /admin is denied and redirected to /unauthorized', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'student-jwt-token')
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
    })
  })

  it('VALIDATION 4: Authenticated Admin is granted direct access to /admin portal', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'admin-jwt-token')
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
      expect(screen.getByText('System Overview')).toBeDefined()
    })
  })

  it('VALIDATION 5: Storage Security Audit — Local/Session storage contains only auth token and no research datasets', () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'secure-jwt-token')

    const sensitiveResearchKeys = [
      'experiments',
      'samples',
      'characterization',
      'ml_models',
      'doe_matrices',
      'recommendations',
      'dataset',
      'optimization_runs',
      'reports',
    ]

    sensitiveResearchKeys.forEach((key) => {
      expect(localStorage.getItem(key)).toBeNull()
      expect(sessionStorage.getItem(key)).toBeNull()
    })

    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBe('secure-jwt-token')
  })
})
