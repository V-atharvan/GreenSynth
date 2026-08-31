import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import AdminDashboard from '../pages/admin/AdminDashboard'
import { AuthProvider } from '../context/AuthContext'
import { adminService } from '../services/adminService'
import * as authHook from '../context/AuthContext'

vi.mock('../services/adminService', () => ({
  adminService: {
    getOverview: vi.fn(),
    getProjects: vi.fn(),
    getGroups: vi.fn(),
    getUsers: vi.fn(),
    getExperiments: vi.fn(),
    getSamples: vi.fn(),
  },
}))

describe('AdminDashboard Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders Access Denied warning when user is a Student', async () => {
    vi.spyOn(authHook, 'useAuth').mockReturnValue({
      user: {
        id: 'student-id',
        username: 'student_user',
        email: 'student@greensynth.edu',
        full_name: 'Student User',
        account_type: 'STUDENT',
        is_active: true,
        department: 'Chemistry',
        phone: '1234567890',
        roll_number: 'STU-001',
        role: 'RESEARCHER',
        created_at: '2026-08-30T00:00:00Z',
        memberships: [],
      },
      token: 'fake-student-token',
      isAuthenticated: true,
      isLoading: false,
      isAdmin: false,
      accountType: 'STUDENT',
      activeMembership: null,
      activeProjectCode: 'P1',
      isGroupLeader: false,
      login: vi.fn(),
      logout: vi.fn(),
      registerLeader: vi.fn(),
      acceptInvitation: vi.fn(),
      setAuthSession: vi.fn(),
      refreshUser: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminDashboard />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Administrator Access Required/i)).toBeDefined()
      expect(screen.getByText(/Return to Researcher Dashboard/i)).toBeDefined()
    })
  })

  it('renders Admin Portal and system-wide metrics when user is an Admin', async () => {
    vi.spyOn(authHook, 'useAuth').mockReturnValue({
      user: {
        id: 'admin-id',
        username: 'atharvan_admin',
        email: 'v.atharvan@gmail.com',
        full_name: 'Atharvan Admin',
        account_type: 'ADMIN',
        role: 'ADMIN',
        is_active: true,
        department: 'Administration',
        phone: '1000000000',
        roll_number: 'ADM-001',
        created_at: '2026-08-30T00:00:00Z',
        memberships: [],
      },
      token: 'fake-admin-token',
      isAuthenticated: true,
      isLoading: false,
      isAdmin: true,
      accountType: 'ADMIN',
      activeMembership: null,
      activeProjectCode: null,
      isGroupLeader: false,
      login: vi.fn(),
      logout: vi.fn(),
      registerLeader: vi.fn(),
      acceptInvitation: vi.fn(),
      setAuthSession: vi.fn(),
      refreshUser: vi.fn(),
    })

    vi.mocked(adminService.getOverview).mockResolvedValue({
      total_projects: 8,
      total_groups: 4,
      total_students: 12,
      total_experiments: 48,
      total_samples: 96,
      total_characterizations: 140,
      total_ml_models: 6,
      total_recommendations: 15,
      total_optimization_runs: 10,
    })

    vi.mocked(adminService.getProjects).mockResolvedValue([
      {
        id: 'p1-id',
        project_code: 'P1',
        name: 'Sol-Gel CuO Mulberry',
        material: 'CuO',
        extract: 'Mulberry',
        solvent: 'Ethanol',
        synthesis_method: 'Sol-Gel',
        status: 'ACTIVE',
      } as any,
      {
        id: 'p7-id',
        project_code: 'P7',
        name: 'Spray Pyrolysis CuO',
        material: 'CuO',
        extract: 'Mulberry',
        solvent: 'Ethanol',
        synthesis_method: 'Spray Pyrolysis',
        status: 'ACTIVE',
      } as any,
    ])

    vi.mocked(adminService.getGroups).mockResolvedValue([])
    vi.mocked(adminService.getUsers).mockResolvedValue([])
    vi.mocked(adminService.getExperiments).mockResolvedValue([])
    vi.mocked(adminService.getSamples).mockResolvedValue([])

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminDashboard />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/System Overview/i)).toBeDefined()
      expect(screen.getByText(/Active Projects/i)).toBeDefined()
    })

    // Switch to Projects tab
    const projectsTab = screen.getByRole('button', { name: /Projects/i })
    fireEvent.click(projectsTab)

    await waitFor(() => {
      expect(screen.getByText(/Synthesis Project Catalog/i)).toBeDefined()
      expect(screen.getByText('P1')).toBeDefined()
      expect(screen.getByText('P7')).toBeDefined()
    })
  })
})
