import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from '../pages/Dashboard'
import { dashboardService } from '../services/dashboardService'
import * as authHook from '../context/AuthContext'
import * as projectHook from '../context/ProjectContext'

vi.mock('../services/dashboardService', () => ({
  dashboardService: {
    getStats: vi.fn(),
  },
}))

describe('Student Dashboard Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders student dashboard with assigned project scope, metadata, and stats', async () => {
    vi.spyOn(authHook, 'useAuth').mockReturnValue({
      user: {
        id: 'student-id',
        username: 'rahul_sharma',
        email: 'rahul.sharma@greensynth.edu',
        full_name: 'Rahul Sharma',
        account_type: 'STUDENT',
        role: 'RESEARCHER',
        is_active: true,
        department: 'Chemical Engineering',
        phone: '9876543210',
        roll_number: 'CHE-2026-07',
        created_at: '2026-08-30T00:00:00Z',
        memberships: [
          {
            group_id: 'grp-7',
            group_name: 'Green Materials Research Group',
            is_leader: false,
            status: 'ACTIVE',
            project_id: 'p7-uuid',
            project_code: 'P7',
            project_name: 'CuO Phytochemical Synthesis via Spray Pyrolysis',
            joined_at: '2026-08-30T00:00:00Z',
          },
        ],
      },
      token: 'fake-jwt-token',
      isAuthenticated: true,
      isLoading: false,
      isAdmin: false,
      accountType: 'STUDENT',
      activeMembership: {
        group_id: 'grp-7',
        group_name: 'Green Materials Research Group',
        is_leader: false,
        status: 'ACTIVE',
        project_id: 'p7-uuid',
        project_code: 'P7',
        project_name: 'CuO Phytochemical Synthesis via Spray Pyrolysis',
        joined_at: '2026-08-30T00:00:00Z',
      },
      activeProjectCode: 'P7',
      isGroupLeader: false,
      login: vi.fn(),
      logout: vi.fn(),
      registerLeader: vi.fn(),
      acceptInvitation: vi.fn(),
      setAuthSession: vi.fn(),
      refreshUser: vi.fn(),
    })

    vi.spyOn(projectHook, 'useProjectContext').mockReturnValue({
      project: {
        id: 'p7-uuid',
        project_code: 'P7',
        name: 'CuO Phytochemical Synthesis via Spray Pyrolysis',
        material: 'CuO',
        extract: 'Mulberry Extract',
        solvent: 'Ethanol',
        synthesis_method: 'Spray Pyrolysis',
        status: 'ACTIVE',
        created_at: '2026-08-30T00:00:00Z',
        description: 'Phytochemical synthesis of semiconducting copper oxide',
        updated_at: '2026-08-30T00:00:00Z',
      },
      projectId: 'p7-uuid',
      projectCode: 'P7',
      projectName: 'CuO Phytochemical Synthesis via Spray Pyrolysis',
      group: null,
      groupId: 'grp-7',
      groupName: 'Green Materials Research Group',
      isGroupLeader: false,
      hasGroupMembership: true,
      allProjects: [],
      selectAdminProject: vi.fn(),
      isLoading: false,
      error: null,
      refreshProject: vi.fn(),
    })

    vi.mocked(dashboardService.getStats).mockResolvedValue({
      total_projects: 1,
      total_experiments: 18,
      total_samples: 36,
      experiments_by_status: {
        PLANNED: 2,
        IN_PROGRESS: 4,
        COMPLETED: 12,
        FAILED: 0,
      },
      projects_by_status: { ACTIVE: 1 },
      recent_experiments: [
        {
          id: 'exp-1',
          experiment_code: 'EXP-P7-001',
          title: 'Spray Pyrolysis Temperature Sweep',
          status: 'COMPLETED',
          experiment_date: '2026-08-30T10:00:00Z',
          researcher: 'Rahul Sharma',
          project_id: 'p7-uuid',
          created_at: '2026-08-30T10:00:00Z',
        },
      ],
    })

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Dashboard />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Research Dashboard/i)).toBeDefined()
      expect(screen.getByText(/Authorized Research Scope/i)).toBeDefined()
      expect(screen.getByText(/P7 — CuO Phytochemical Synthesis via Spray Pyrolysis/i)).toBeDefined()
      expect(screen.getByText(/Green Materials Research Group/i)).toBeDefined()
      expect(screen.getByText('18')).toBeDefined()
      expect(screen.getByText('36')).toBeDefined()
      expect(screen.getByText('EXP-P7-001')).toBeDefined()
    })
  })

  it('renders helpful message when Student account has no active group membership', async () => {
    vi.spyOn(authHook, 'useAuth').mockReturnValue({
      user: {
        id: 'student-no-grp',
        username: 'unassigned_user',
        email: 'unassigned@greensynth.edu',
        full_name: 'Unassigned Student',
        account_type: 'STUDENT',
        role: 'RESEARCHER',
        is_active: true,
        department: 'Physics',
        phone: '1234567890',
        roll_number: 'PHY-001',
        created_at: '2026-08-30T00:00:00Z',
        memberships: [],
      },
      token: 'fake-token',
      isAuthenticated: true,
      isLoading: false,
      isAdmin: false,
      accountType: 'STUDENT',
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

    vi.spyOn(projectHook, 'useProjectContext').mockReturnValue({
      project: null,
      projectId: null,
      projectCode: null,
      projectName: null,
      group: null,
      groupId: null,
      groupName: null,
      isGroupLeader: false,
      hasGroupMembership: false,
      allProjects: [],
      selectAdminProject: vi.fn(),
      isLoading: false,
      error: null,
      refreshProject: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Dashboard />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Welcome to GreenSynth/i)).toBeDefined()
      expect(screen.getByText(/no active research group or project has been assigned/i)).toBeDefined()
      expect(screen.getByText(/Unassigned Student/i)).toBeDefined()
    })
  })
})
