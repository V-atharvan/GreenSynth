import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { ProjectProvider, useProjectContext } from '../context/ProjectContext'
import { AuthContext, AuthContextValue } from '../context/AuthContext'
import { projectService } from '../services/projectService'
import type { UserProfile, MembershipRead } from '../types'

vi.mock('../services/projectService', () => ({
  projectService: {
    getById: vi.fn().mockResolvedValue({
      id: 'proj-7',
      project_code: 'P7',
      name: 'CuO Spray Pyrolysis',
      description: 'CuO thin films',
      material: 'Copper Oxide',
      synthesis_method: 'Spray Pyrolysis',
      status: 'ACTIVE',
      created_at: '2026-08-30T00:00:00Z',
      updated_at: '2026-08-30T00:00:00Z',
    }),
  },
}))

const TestComponent = () => {
  const {
    projectId,
    projectCode,
    projectName,
    groupId,
    groupName,
    isGroupLeader,
    hasGroupMembership,
  } = useProjectContext()

  return (
    <div>
      <div data-testid="has-group">{hasGroupMembership ? 'YES' : 'NO'}</div>
      <div data-testid="project-id">{projectId || 'NONE'}</div>
      <div data-testid="project-code">{projectCode || 'NONE'}</div>
      <div data-testid="project-name">{projectName || 'NONE'}</div>
      <div data-testid="group-id">{groupId || 'NONE'}</div>
      <div data-testid="group-name">{groupName || 'NONE'}</div>
      <div data-testid="is-leader">{isGroupLeader ? 'LEADER' : 'MEMBER'}</div>
    </div>
  )
}

describe('ProjectContext', () => {
  it('resolves assigned project and group from authenticated active membership', async () => {
    const mockUser: UserProfile = {
      id: 'usr-123',
      username: 'leader_alice',
      email: 'leader@lab.org',
      full_name: 'Dr. Leader',
      department: 'Materials Science',
      phone: '1234567890',
      roll_number: 'ROLL-01',
      role: 'RESEARCHER',
      is_active: true,
      created_at: new Date().toISOString(),
      memberships: [],
    }

    const mockMembership: MembershipRead = {
      group_id: 'grp-7',
      group_name: 'Nanotech Synthesis Group',
      is_leader: true,
      status: 'ACTIVE',
      project_id: 'proj-7',
      project_code: 'P7',
      project_name: 'CuO Spray Pyrolysis',
      joined_at: new Date().toISOString(),
    }

    const authValue: AuthContextValue = {
      user: mockUser,
      token: 'mock-jwt-token',
      isAdmin: false,
      accountType: 'STUDENT',
      activeMembership: mockMembership,
      activeProjectCode: 'P7',
      isGroupLeader: true,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      registerLeader: vi.fn(),
      acceptInvitation: vi.fn(),
      refreshUser: vi.fn(),
      setAuthSession: vi.fn(),
    }

    render(
      <AuthContext.Provider value={authValue}>
        <ProjectProvider>
          <TestComponent />
        </ProjectProvider>
      </AuthContext.Provider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('has-group').textContent).toBe('YES')
      expect(screen.getByTestId('project-id').textContent).toBe('proj-7')
      expect(screen.getByTestId('project-code').textContent).toBe('P7')
      expect(screen.getByTestId('project-name').textContent).toBe('CuO Spray Pyrolysis')
      expect(screen.getByTestId('group-id').textContent).toBe('grp-7')
      expect(screen.getByTestId('group-name').textContent).toBe('Nanotech Synthesis Group')
      expect(screen.getByTestId('is-leader').textContent).toBe('LEADER')
    })
  })

  it('handles user without group membership gracefully', () => {
    const mockUser: UserProfile = {
      id: 'usr-456',
      username: 'student_bob',
      email: 'newbie@lab.org',
      full_name: 'New Student',
      department: 'Chemistry',
      phone: '1234567890',
      roll_number: 'ROLL-02',
      role: 'STUDENT',
      is_active: true,
      created_at: new Date().toISOString(),
      memberships: [],
    }

    const authValue: AuthContextValue = {
      user: mockUser,
      token: 'mock-jwt-token',
      isAdmin: false,
      accountType: 'STUDENT',
      activeMembership: null,
      activeProjectCode: null,
      isGroupLeader: false,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      registerLeader: vi.fn(),
      acceptInvitation: vi.fn(),
      refreshUser: vi.fn(),
      setAuthSession: vi.fn(),
    }

    render(
      <AuthContext.Provider value={authValue}>
        <ProjectProvider>
          <TestComponent />
        </ProjectProvider>
      </AuthContext.Provider>
    )

    expect(screen.getByTestId('has-group').textContent).toBe('NO')
    expect(screen.getByTestId('project-id').textContent).toBe('NONE')
    expect(screen.getByTestId('project-code').textContent).toBe('NONE')
    expect(screen.getByTestId('is-leader').textContent).toBe('MEMBER')
  })
})
