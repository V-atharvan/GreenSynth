import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthContext, AuthContextValue } from '../context/AuthContext'
import { ProjectProvider } from '../context/ProjectContext'
import { DOEDashboard } from '../pages/DOEDashboard'
import MLDashboard from '../pages/MLDashboard'
import Experiments from '../pages/Experiments'
import { doeService } from '../services/doeService'
import { mlService } from '../services/mlService'
import { experimentService } from '../services/experimentService'
import { parameterService } from '../services/parameterService'
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

vi.mock('../services/doeService', () => ({
  doeService: {
    listProjectDOEs: vi.fn().mockResolvedValue([]),
    getDOE: vi.fn(),
    listProposedExperiments: vi.fn().mockResolvedValue([]),
  },
}))

vi.mock('../services/mlService', () => ({
  mlService: {
    getDatasets: vi.fn().mockResolvedValue([]),
    getModels: vi.fn().mockResolvedValue([]),
    getPredictions: vi.fn().mockResolvedValue([]),
  },
}))

vi.mock('../services/experimentService', () => ({
  experimentService: {
    getAll: vi.fn().mockResolvedValue([]),
    create: vi.fn(),
  },
}))

vi.mock('../services/parameterService', () => ({
  parameterService: {
    getProjectParameters: vi.fn().mockResolvedValue([]),
  },
}))

describe('Project Isolation in Studios', () => {
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

  const renderWithProviders = (ui: React.ReactElement) => {
    return render(
      <MemoryRouter>
        <AuthContext.Provider value={authValue}>
          <ProjectProvider>{ui}</ProjectProvider>
        </AuthContext.Provider>
      </MemoryRouter>
    )
  }

  it('DOEDashboard displays assigned project badge and queries with assigned projectId', async () => {
    renderWithProviders(<DOEDashboard />)

    await waitFor(() => {
      expect(doeService.listProjectDOEs).toHaveBeenCalledWith('proj-7')
    })

    expect(screen.getByText(/P7 — CuO Spray Pyrolysis/i)).toBeInTheDocument()
  })

  it('MLDashboard automatically scopes datasets to assigned projectId', async () => {
    renderWithProviders(<MLDashboard />)

    await waitFor(() => {
      expect(mlService.getDatasets).toHaveBeenCalledWith('proj-7')
    })

    expect(screen.getByText(/P7 — CuO Spray Pyrolysis/i)).toBeInTheDocument()
  })

  it('Experiments list automatically scopes to assigned projectId', async () => {
    renderWithProviders(<Experiments />)

    await waitFor(() => {
      expect(experimentService.getAll).toHaveBeenCalledWith({
        project_id: 'proj-7',
        status: undefined,
      })
    })

    expect(screen.getByText(/P7 — CuO Spray Pyrolysis/i)).toBeInTheDocument()
  })
})
