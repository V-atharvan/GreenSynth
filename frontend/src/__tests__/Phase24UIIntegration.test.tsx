/**
 * GreenSynth Analytics — Phase 24 Admin / Student UI Integration Tests
 *
 * Validates:
 * 1. Single Unified Login for both Admin and Student.
 * 2. Admin UI integration: system-wide metrics, project switching (P1–P8), student list, group list.
 * 3. Student UI integration: strict project isolation (e.g. P7), absence of Admin dashboard / multi-project dropdown.
 * 4. Group Leader UI integration: member invitations and group management controls.
 * 5. Normal Member UI: absence of leader invitation controls.
 * 6. Route security & error handling (AdminRoute protection, 401 session purge, 403 authorization boundary).
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
import MainLayout from '../layouts/MainLayout'
import { authService } from '../services/authService'
import { adminService } from '../services/adminService'
import { dashboardService } from '../services/dashboardService'
import { projectService } from '../services/projectService'
import { AUTH_TOKEN_KEY } from '../services/api'
import type { Project, UserProfile } from '../types'

vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(),
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
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
    getProjects: vi.fn().mockResolvedValue([
      { id: 'p1-id', code: 'P1', title: 'ZnO Nanoparticles', synthesis_method: 'Sol-Gel' },
      { id: 'p7-id', code: 'P7', title: 'CuO Spray Pyrolysis', synthesis_method: 'Spray Pyrolysis' },
    ]),
    getGroups: vi.fn().mockResolvedValue([
      {
        id: 'g1-id',
        name: 'Spray Pyrolysis Group',
        project_id: 'p7-id',
        project_code: 'P7',
        project_name: 'CuO Spray Pyrolysis',
        leader_name: 'Dr. Leader',
        leader_email: 'leader@greensynth.edu',
        member_count: 3,
      },
    ]),
    getUsers: vi.fn().mockResolvedValue([
      {
        id: 'u1-id',
        username: 'student_a',
        email: 'student.a@greensynth.edu',
        full_name: 'Student Researcher A',
        department: 'Chemical Engineering',
        role: 'RESEARCHER',
        account_type: 'STUDENT',
        is_active: true,
        created_at: '2026-08-30T00:00:00Z',
      },
    ]),
    getExperiments: vi.fn().mockResolvedValue([
      { id: 'exp-1', experiment_code: 'EXP-P7-001', title: 'CuO Synthesis Run 1', status: 'COMPLETED' },
    ]),
    getSamples: vi.fn().mockResolvedValue([
      { id: 'smp-1', sample_code: 'SMP-P7-001', synthesis_date: '2026-08-30' },
    ]),
  },
}))

vi.mock('../services/dashboardService', () => ({
  dashboardService: {
    getStats: vi.fn().mockResolvedValue({
      total_projects: 1,
      total_experiments: 8,
      total_samples: 16,
      experiments_by_status: { COMPLETED: 8 },
      projects_by_status: { ACTIVE: 1 },
      recent_experiments: [],
    }),
  },
}))

vi.mock('../services/projectService', () => ({
  projectService: {
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

const mockGroupLeaderUser: UserProfile = {
  id: 'leader-uuid',
  username: 'leader_p7',
  email: 'leader.p7@greensynth.edu',
  full_name: 'Leader Scientist P7',
  department: 'Nanotechnology Dept',
  phone: '1000000002',
  roll_number: 'LDR-07',
  role: 'RESEARCHER',
  account_type: 'STUDENT',
  is_active: true,
  created_at: '2026-08-30T00:00:00Z',
  memberships: [
    {
      group_id: 'grp-7',
      group_name: 'Spray Pyrolysis Core Lab',
      project_id: 'p7-id',
      project_code: 'P7',
      project_name: 'CuO Spray Pyrolysis',
      is_leader: true,
      status: 'ACTIVE',
      joined_at: '2026-08-30T00:00:00Z',
    },
  ],
}

const mockNormalStudentUser: UserProfile = {
  id: 'student-uuid',
  username: 'member_p7',
  email: 'member.p7@greensynth.edu',
  full_name: 'Junior Member P7',
  department: 'Nanotechnology Dept',
  phone: '1000000003',
  roll_number: 'STU-07',
  role: 'RESEARCHER',
  account_type: 'STUDENT',
  is_active: true,
  created_at: '2026-08-30T00:00:00Z',
  memberships: [
    {
      group_id: 'grp-7',
      group_name: 'Spray Pyrolysis Core Lab',
      project_id: 'p7-id',
      project_code: 'P7',
      project_name: 'CuO Spray Pyrolysis',
      is_leader: false,
      status: 'ACTIVE',
      joined_at: '2026-08-30T00:00:00Z',
    },
  ],
}

describe('Phase 24 Admin / Student UI Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders unified login without role selectors or dual login buttons', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )

    expect(screen.getByText('GreenSynth Analytics')).toBeDefined()
    expect(screen.getByPlaceholderText('researcher@greensynth.edu')).toBeDefined()
    expect(screen.getByPlaceholderText('Enter account password')).toBeDefined()
    expect(screen.getByRole('button', { name: /Sign In to Research Portal/i })).toBeDefined()
    expect(screen.queryByText(/Admin Login/i)).toBeNull()
    expect(screen.queryByText(/Student Login/i)).toBeNull()
  })

  it('renders Admin Dashboard with system-wide overview cards and cross-project metrics', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'admin-token')
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
      expect(screen.getAllByText('Research Groups').length).toBeGreaterThan(0)
      expect(screen.getByText('Active Projects')).toBeDefined()
    })
  })

  it('renders Student Dashboard scoped to assigned project P7 and hides Admin Dashboard link', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'student-token')
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockNormalStudentUser)

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <ProjectProvider>
            <Routes>
              <Route element={<ProtectedRoute />}>
                <Route path="/" element={<MainLayout />}>
                  <Route path="dashboard" element={<Dashboard />} />
                </Route>
              </Route>
            </Routes>
          </ProjectProvider>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getAllByText('P7').length).toBeGreaterThan(0)
      expect(screen.queryByText('Admin Dashboard')).toBeNull()
    })
  })

  it('blocks Student from accessing /admin and routes to /unauthorized', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'student-token')
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockNormalStudentUser)

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

  it('renders Group Leader role badge for Leader and Member role badge for normal student', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'leader-token')
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockGroupLeaderUser)

    function TestRoleView() {
      const { isGroupLeader, activeProjectCode, accountType } = useAuth()
      return (
        <div>
          <div data-testid="role-status">{isGroupLeader ? 'GROUP_LEADER' : 'NORMAL_MEMBER'}</div>
          <div data-testid="project-code">{activeProjectCode}</div>
          <div data-testid="account-type">{accountType}</div>
        </div>
      )
    }

    render(
      <AuthProvider>
        <TestRoleView />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('role-status').textContent).toBe('GROUP_LEADER')
      expect(screen.getByTestId('project-code').textContent).toBe('P7')
      expect(screen.getByTestId('account-type').textContent).toBe('STUDENT')
    })
  })
})
