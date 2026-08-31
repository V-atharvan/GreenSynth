/**
 * GreenSynth Analytics — Profile Page Frontend Tests
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Profile from '@/pages/Profile'
import { authService } from '@/services/authService'
import { groupService } from '@/services/groupService'
import { projectService } from '@/services/projectService'
import * as AuthContextModule from '@/context/AuthContext'
import type { UserProfile, GroupDetail, ProjectSummary } from '@/types'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('@/services/authService', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    updateProfile: vi.fn(),
  },
}))

vi.mock('@/services/groupService', () => ({
  groupService: {
    getMyGroup: vi.fn(),
  },
}))

vi.mock('@/services/projectService', () => ({
  projectService: {
    getCatalog: vi.fn(),
  },
}))

const mockStudentProfile: UserProfile = {
  id: 'student-123',
  username: 'rahul',
  email: 'rahul@example.com',
  full_name: 'Rahul Sharma',
  department: 'Chemical Engineering',
  phone: '+91 9876543210',
  roll_number: 'ME-2024-01',
  role: 'STUDENT',
  account_type: 'STUDENT',
  is_active: true,
  created_at: '2026-08-15T10:00:00Z',
  memberships: [
    {
      group_id: 'group-1',
      group_name: 'Green Materials Research Group',
      is_leader: false,
      status: 'ACTIVE',
      project_id: 'proj-7',
      project_code: 'P7',
      project_name: 'CuO + Mulberry Extract + Ethanol + Spray Pyrolysis',
      joined_at: '2026-08-15T10:00:00Z',
    },
  ],
}

const mockAdminProfile: UserProfile = {
  id: 'admin-123',
  username: 'admin',
  email: 'v.atharvan@gmail.com',
  full_name: 'Atharva Vaddepalli',
  department: 'Administration',
  phone: '+91 9999999999',
  roll_number: 'ADM-001',
  role: 'ADMIN',
  account_type: 'ADMIN',
  is_active: true,
  created_at: '2026-08-01T10:00:00Z',
  memberships: [],
}

const mockGroupDetail: GroupDetail = {
  group_id: 'group-1',
  group_name: 'Green Materials Research Group',
  project_id: 'proj-7',
  project_code: 'P7',
  project_name: 'CuO + Mulberry Extract + Ethanol + Spray Pyrolysis',
  leader_id: 'leader-99',
  leader_name: 'Atharva Vaddepalli',
  leader_email: 'v.atharvan@gmail.com',
  member_count: 3,
  max_members: 6,
  user_is_leader: false,
  created_at: '2026-08-15T10:00:00Z',
}

const mockProjects: ProjectSummary[] = [
  {
    id: 'proj-7',
    project_code: 'P7',
    name: 'CuO + Mulberry Extract + Ethanol + Spray Pyrolysis',
    material: 'CuO',
    synthesis_method: 'Spray Pyrolysis',
    extract: 'Mulberry Extract',
    solvent: 'Ethanol',
    status: 'ACTIVE',
    created_at: '2026-08-01T00:00:00Z',
  },
]

function createAuthContextMock(overrides: Partial<AuthContextModule.AuthContextValue> = {}): AuthContextModule.AuthContextValue {
  return {
    user: mockStudentProfile,
    token: 'mock-token',
    isAuthenticated: true,
    isLoading: false,
    isAdmin: false,
    accountType: 'STUDENT',
    activeMembership: mockStudentProfile.memberships[0] || null,
    activeProjectCode: 'P7',
    isGroupLeader: false,
    login: vi.fn(),
    registerLeader: vi.fn(),
    acceptInvitation: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
    setAuthSession: vi.fn(),
    ...overrides,
  }
}

describe('Profile Page Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockStudentProfile)
    vi.mocked(groupService.getMyGroup).mockResolvedValue(mockGroupDetail)
    vi.mocked(projectService.getCatalog).mockResolvedValue(mockProjects)
  })

  it('renders student profile with summary avatar, personal info, research details, and account info', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue(createAuthContextMock())

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    )

    // Summary Card
    expect(await screen.findByText('Rahul Sharma')).toBeInTheDocument()
    expect(screen.getByText('rahul@example.com')).toBeInTheDocument()
    expect(screen.getByText('RS')).toBeInTheDocument() // Initials avatar
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getAllByText('Student').length).toBeGreaterThanOrEqual(1)

    // Research Info Card
    expect(screen.getByText('Green Materials Research Group')).toBeInTheDocument()
    expect(screen.getByText('Member')).toBeInTheDocument()
    expect(screen.getByText('Atharva Vaddepalli')).toBeInTheDocument() // Group Leader
    expect(screen.getByText('P7')).toBeInTheDocument()
    expect(screen.getByText('CuO + Mulberry Extract + Ethanol + Spray Pyrolysis')).toBeInTheDocument()

    // Read-only fields
    const emailInput = screen.getByLabelText(/Email Address/i)
    expect(emailInput).toBeDisabled()

    const accountTypeInput = screen.getByLabelText(/Account Type/i)
    expect(accountTypeInput).toBeDisabled()

    const accountStatusInput = screen.getByLabelText(/Account Status/i)
    expect(accountStatusInput).toBeDisabled()
  })

  it('renders admin profile with system-wide research access', async () => {
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockAdminProfile)
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue(
      createAuthContextMock({
        user: mockAdminProfile,
        isAdmin: true,
        accountType: 'ADMIN',
        isGroupLeader: false,
        activeMembership: null,
        activeProjectCode: null,
      })
    )

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    )

    expect(await screen.findByText('Atharva Vaddepalli')).toBeInTheDocument()
    expect(screen.getByText('v.atharvan@gmail.com')).toBeInTheDocument()
    expect(screen.getByText('AV')).toBeInTheDocument() // Initials avatar
    expect(screen.getByText('Administrator')).toBeInTheDocument()

    // Admin Research Access
    expect(screen.getByText('System-wide')).toBeInTheDocument()
    expect(screen.getByText('All Groups')).toBeInTheDocument()
    expect(screen.getByText('P1 – P8')).toBeInTheDocument()

    // Does NOT render fake group assignment
    expect(screen.queryByText('GreenSynth Research Group')).not.toBeInTheDocument()
  })

  it('enables Save Changes button on edit and calls updateProfile with trimmed name', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue(createAuthContextMock())
    vi.mocked(authService.updateProfile).mockResolvedValue({
      ...mockStudentProfile,
      full_name: 'Rahul V. Sharma',
    })

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    )

    const nameInput = await screen.findByLabelText(/Full Name/i)
    const saveBtn = screen.getByRole('button', { name: /Save Changes/i })

    // Button disabled initially
    expect(saveBtn).toBeDisabled()

    // Modify name
    fireEvent.change(nameInput, { target: { value: '   Rahul V. Sharma   ' } })
    expect(saveBtn).not.toBeDisabled()

    fireEvent.click(saveBtn)

    await waitFor(() => {
      expect(authService.updateProfile).toHaveBeenCalledWith({
        full_name: 'Rahul V. Sharma',
      })
    })

    expect(await screen.findByText('Profile updated successfully.')).toBeInTheDocument()
  })

  it('handles logout action by calling AuthContext logout and redirecting to /login', async () => {
    const mockLogout = vi.fn()
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue(
      createAuthContextMock({ logout: mockLogout })
    )

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    )

    const logoutBtn = await screen.findByRole('button', { name: /Logout/i })
    fireEvent.click(logoutBtn)

    expect(mockLogout).toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })

  it('does NOT render password, password hash, SMTP settings, notifications, or appearance controls', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue(createAuthContextMock())

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    )

    expect(await screen.findByText('Rahul Sharma')).toBeInTheDocument()

    expect(screen.queryByText(/Password:/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/password_hash/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/SMTP/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Email Server/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Notification/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Theme/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Appearance/i)).not.toBeInTheDocument()
  })
})
