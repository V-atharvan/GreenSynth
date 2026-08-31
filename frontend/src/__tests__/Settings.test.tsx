/**
 * GreenSynth Analytics — Settings Module Frontend Tests
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Settings from '@/pages/Settings'
import { authService } from '@/services/authService'
import { adminService } from '@/services/adminService'
import { groupService } from '@/services/groupService'
import { projectService } from '@/services/projectService'
import * as AuthContextModule from '@/context/AuthContext'
import type { UserProfile, GroupDetail, GroupMember, Project, ProjectSummary } from '@/types'

// Mock services
vi.mock('@/services/authService', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
  },
}))

vi.mock('@/services/adminService', () => ({
  adminService: {
    getUsers: vi.fn(),
    getGroups: vi.fn(),
    getProjects: vi.fn(),
    updateUserStatus: vi.fn(),
  },
}))

vi.mock('@/services/groupService', () => ({
  groupService: {
    getMyGroup: vi.fn(),
    getMyGroupMembers: vi.fn(),
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
      group_name: 'Green Materials Group',
      is_leader: true,
      status: 'ACTIVE',
      project_id: 'proj-7',
      project_code: 'P7',
      project_name: 'Mulberry CuO Thin Films',
      joined_at: '2026-08-15T10:00:00Z',
    },
  ],
}

const mockAdminProfile: UserProfile = {
  id: 'admin-123',
  username: 'admin',
  email: 'v.atharvan@gmail.com',
  full_name: 'System Administrator',
  department: 'Administration',
  phone: '+91 9999999999',
  roll_number: 'ADMIN-01',
  role: 'ADMIN',
  account_type: 'ADMIN',
  is_active: true,
  created_at: '2026-08-01T10:00:00Z',
  memberships: [],
}

const mockGroupDetail: GroupDetail = {
  group_id: 'group-1',
  group_name: 'Green Materials Group',
  project_id: 'proj-7',
  project_code: 'P7',
  project_name: 'Mulberry CuO Thin Films',
  leader_id: 'student-123',
  leader_name: 'Rahul Sharma',
  leader_email: 'rahul@example.com',
  member_count: 2,
  max_members: 6,
  user_is_leader: true,
  created_at: '2026-08-15T10:00:00Z',
}

const mockGroupMembers: GroupMember[] = [
  {
    user_id: 'student-123',
    full_name: 'Rahul Sharma',
    department: 'Chemical Engineering',
    roll_number: 'ME-2024-01',
    email: 'rahul@example.com',
    is_leader: true,
    status: 'ACTIVE',
    joined_at: '2026-08-15T10:00:00Z',
  },
]

const mockProjects: Project[] = [
  {
    id: 'proj-7',
    project_code: 'P7',
    name: 'Mulberry CuO Thin Films',
    material: 'CuO',
    synthesis_method: 'Spray Pyrolysis',
    extract: 'Mulberry',
    solvent: 'Ethanol',
    status: 'ACTIVE',
    description: 'Mulberry synthesized CuO semiconductor thin films',
    created_at: '2026-08-01T00:00:00Z',
    updated_at: '2026-08-01T00:00:00Z',
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
    isGroupLeader: true,
    login: vi.fn(),
    registerLeader: vi.fn(),
    acceptInvitation: vi.fn(),
    logout: vi.fn(),
    refreshUser: vi.fn(),
    setAuthSession: vi.fn(),
    ...overrides,
  }
}

describe('Settings Module', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockStudentProfile)
    vi.mocked(groupService.getMyGroup).mockResolvedValue(mockGroupDetail)
    vi.mocked(groupService.getMyGroupMembers).mockResolvedValue(mockGroupMembers)
    vi.mocked(projectService.getCatalog).mockResolvedValue(mockProjects)
    vi.mocked(adminService.getUsers).mockResolvedValue([mockAdminProfile, mockStudentProfile])
    vi.mocked(adminService.getGroups).mockResolvedValue([mockGroupDetail])
    vi.mocked(adminService.getProjects).mockResolvedValue(mockProjects)
  })

  it('renders Settings page for authenticated student with Profile, Password, and Research tabs', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue(createAuthContextMock())

    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )

    expect(await screen.findByText('Profile Settings')).toBeInTheDocument()
    expect(screen.getByText('Change Password')).toBeInTheDocument()
    expect(screen.getByText('Research Information')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()

    // Student must NOT see admin tabs
    expect(screen.queryByRole('button', { name: /^Users$/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Research Groups$/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Projects$/i })).not.toBeInTheDocument()
  })

  it('renders Administration tabs for authenticated Administrator', async () => {
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
        <Settings />
      </BrowserRouter>
    )

    expect(await screen.findByText('Administration')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Users/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Research Groups/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Projects/i })).toBeInTheDocument()
  })

  it('loads profile from /auth/me and submits allowed profile updates', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue(createAuthContextMock())

    vi.mocked(authService.updateProfile).mockResolvedValue({
      ...mockStudentProfile,
      full_name: 'Rahul V. Sharma',
    })

    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )

    const nameInput = await screen.findByDisplayValue('Rahul Sharma')
    fireEvent.change(nameInput, { target: { value: 'Rahul V. Sharma' } })

    const saveBtn = screen.getByRole('button', { name: /Save Profile Changes/i })
    fireEvent.click(saveBtn)

    await waitFor(() => {
      expect(authService.updateProfile).toHaveBeenCalledWith({
        full_name: 'Rahul V. Sharma',
        department: 'Chemical Engineering',
        phone: '+91 9876543210',
        roll_number: 'ME-2024-01',
      })
    })

    expect(await screen.findByText('Profile updated successfully.')).toBeInTheDocument()
  })

  it('validates password matching on Change Password tab', async () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue(createAuthContextMock())

    render(
      <BrowserRouter>
        <Settings />
      </BrowserRouter>
    )

    // Switch to password tab
    const pwdNavBtn = screen.getAllByRole('button', { name: /Change Password/i })[0]
    fireEvent.click(pwdNavBtn)

    expect(screen.getByText('Change Account Password')).toBeInTheDocument()

    const currentInput = screen.getByPlaceholderText('Enter your current password')
    const newInput = screen.getByPlaceholderText('Enter new password')
    const confirmInput = screen.getByPlaceholderText('Re-enter new password')

    fireEvent.change(currentInput, { target: { value: 'oldpassword123' } })
    fireEvent.change(newInput, { target: { value: 'newpassword123' } })
    fireEvent.change(confirmInput, { target: { value: 'mismatchpassword' } })

    const submitBtn = screen.getAllByRole('button', { name: /Change Password/i })[1]
    fireEvent.click(submitBtn)

    expect(await screen.findByText('New password and confirmation do not match.')).toBeInTheDocument()
    expect(authService.changePassword).not.toHaveBeenCalled()
  })

  it('does NOT render SMTP, Notification, or Appearance settings in UI', async () => {
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
        <Settings />
      </BrowserRouter>
    )

    expect(screen.queryByText(/SMTP Settings/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Email Server/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Notification Settings/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Appearance/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Theme Selector/i)).not.toBeInTheDocument()
  })
})
