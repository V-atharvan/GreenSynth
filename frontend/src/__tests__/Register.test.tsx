import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import Register from '../pages/Register'
import { AuthProvider } from '../context/AuthContext'
import { projectService } from '../services/projectService'
import { groupService } from '../services/groupService'

vi.mock('../services/projectService', () => ({
  projectService: {
    getAll: vi.fn().mockResolvedValue([
      {
        id: 'proj-p1-uuid',
        project_code: 'P1',
        name: 'Hydrothermal ZnO Synthesis',
        material: 'ZnO',
        synthesis_method: 'Hydrothermal',
        solvent: 'DI Water',
        status: 'ACTIVE',
        created_at: '2026-08-30T00:00:00Z',
      },
    ]),
    getCatalog: vi.fn().mockResolvedValue([
      {
        id: 'proj-p1-uuid',
        project_code: 'P1',
        name: 'Hydrothermal ZnO Synthesis',
        material: 'ZnO',
        synthesis_method: 'Hydrothermal',
        solvent: 'DI Water',
        status: 'ACTIVE',
        created_at: '2026-08-30T00:00:00Z',
      },
      {
        id: 'proj-p7-uuid',
        project_code: 'P7',
        name: 'Phytochemical CuO Sol-Gel Synthesis',
        material: 'CuO',
        synthesis_method: 'Sol-Gel',
        solvent: 'Ethanol',
        status: 'ACTIVE',
        created_at: '2026-08-30T00:00:00Z',
      },
    ]),
  },
}))

vi.mock('../services/groupService', () => ({
  groupService: {
    registerGroupWithMembers: vi.fn(),
  },
}))

describe('Register Page Wizard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders Step 1 with leader account fields and header', async () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Register />
        </AuthProvider>
      </BrowserRouter>
    )

    expect(screen.getByText('Register Your Semiconductor Research Group')).toBeDefined()
    expect(screen.getByText('Step 1: Group Leader Information')).toBeDefined()
    expect(screen.getByPlaceholderText('e.g. Atharva Kulkarni')).toBeDefined()
    expect(screen.getByPlaceholderText('leader@greensynth.edu')).toBeDefined()
  })

  it('shows error if Step 1 is submitted with incomplete details', async () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Register />
        </AuthProvider>
      </BrowserRouter>
    )

    const continueBtn = screen.getByText(/Continue/i)
    fireEvent.click(continueBtn)

    await waitFor(() => {
      expect(screen.getByText(/Please fill in all leader identification details/i)).toBeDefined()
    })
  })
})
