import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import AcceptInvitation from '../pages/AcceptInvitation'
import { AuthProvider } from '../context/AuthContext'
import { invitationService } from '../services/invitationService'

vi.mock('../services/invitationService', () => ({
  invitationService: {
    validateInvitation: vi.fn(),
    acceptInvitation: vi.fn(),
  },
}))

describe('AcceptInvitation Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()
  })

  it('renders error message when no token is present in URL', async () => {
    render(
      <MemoryRouter initialEntries={['/accept-invitation']}>
        <AuthProvider>
          <AcceptInvitation />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/No invitation token found/i)).toBeDefined()
    })
  })

  it('validates token and displays read-only email, group and project information', async () => {
    vi.mocked(invitationService.validateInvitation).mockResolvedValue({
      valid: true,
      group_name: 'Solar Nanotech Team',
      project_id: 'proj-123',
      project_code: 'P3',
      project_name: 'Sol-Gel TiO2 Synthesis',
      invited_name: 'Student Tester',
      invited_email: 'student.test@greensynth.edu',
      department: 'Chemical Engineering',
      roll_number: 'CHEM-2026-05',
      leader_name: 'Leader Alpha',
      expires_at: '2026-09-02T12:00:00Z',
    })

    render(
      <MemoryRouter initialEntries={['/accept-invitation?token=valid_test_token']}>
        <AuthProvider>
          <AcceptInvitation />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Join Solar Nanotech Team/i)).toBeDefined()
      expect(screen.getByText(/P3 — Sol-Gel TiO2 Synthesis/i)).toBeDefined()
      expect(screen.getByText(/Student Tester/i)).toBeDefined()
      expect(screen.getByDisplayValue('student.test@greensynth.edu')).toBeDefined()
      expect(screen.getByText(/Accept Invitation & Activate Account/i)).toBeDefined()
    })
  })

  it('shows password mismatch error when passwords do not match', async () => {
    vi.mocked(invitationService.validateInvitation).mockResolvedValue({
      valid: true,
      group_name: 'Solar Nanotech Team',
      project_id: 'proj-123',
      project_code: 'P3',
      project_name: 'Sol-Gel TiO2 Synthesis',
      invited_name: 'Student Tester',
      invited_email: 'student.test@greensynth.edu',
      department: 'Chemical Engineering',
      roll_number: 'CHEM-2026-05',
      leader_name: 'Leader Alpha',
      expires_at: '2026-09-02T12:00:00Z',
    })

    render(
      <MemoryRouter initialEntries={['/accept-invitation?token=valid_test_token']}>
        <AuthProvider>
          <AcceptInvitation />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Join Solar Nanotech Team/i)).toBeDefined()
    })

    const passwordInputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(passwordInputs[0], { target: { value: 'ValidPassword123!' } })
    fireEvent.change(passwordInputs[1], { target: { value: 'MismatchedPassword123!' } })

    fireEvent.click(screen.getByText(/Accept Invitation & Activate Account/i))

    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/i)).toBeDefined()
    })
  })

  it('shows password length validation error when shorter than 8 characters', async () => {
    vi.mocked(invitationService.validateInvitation).mockResolvedValue({
      valid: true,
      group_name: 'Solar Nanotech Team',
      project_id: 'proj-123',
      project_code: 'P3',
      project_name: 'Sol-Gel TiO2 Synthesis',
      invited_name: 'Student Tester',
      invited_email: 'student.test@greensynth.edu',
      department: 'Chemical Engineering',
      roll_number: 'CHEM-2026-05',
      leader_name: 'Leader Alpha',
      expires_at: '2026-09-02T12:00:00Z',
    })

    render(
      <MemoryRouter initialEntries={['/accept-invitation?token=valid_test_token']}>
        <AuthProvider>
          <AcceptInvitation />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Join Solar Nanotech Team/i)).toBeDefined()
    })

    const passwordInputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(passwordInputs[0], { target: { value: 'short' } })
    fireEvent.change(passwordInputs[1], { target: { value: 'short' } })

    fireEvent.click(screen.getByText(/Accept Invitation & Activate Account/i))

    await waitFor(() => {
      expect(screen.getByText(/at least 8 characters/i)).toBeDefined()
    })
  })

  it('submits valid password and displays success screen with Go to Login button', async () => {
    vi.mocked(invitationService.validateInvitation).mockResolvedValue({
      valid: true,
      group_name: 'Solar Nanotech Team',
      project_id: 'proj-123',
      project_code: 'P3',
      project_name: 'Sol-Gel TiO2 Synthesis',
      invited_name: 'Student Tester',
      invited_email: 'student.test@greensynth.edu',
      department: 'Chemical Engineering',
      roll_number: 'CHEM-2026-05',
      leader_name: 'Leader Alpha',
      expires_at: '2026-09-02T12:00:00Z',
    })

    vi.mocked(invitationService.acceptInvitation).mockResolvedValue({
      access_token: 'fake_jwt_token',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        id: 'user-uuid',
        full_name: 'Student Tester',
        email: 'student.test@greensynth.edu',
        account_type: 'STUDENT',
      },
    })

    render(
      <MemoryRouter initialEntries={['/accept-invitation?token=valid_test_token']}>
        <AuthProvider>
          <AcceptInvitation />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Join Solar Nanotech Team/i)).toBeDefined()
    })

    const passwordInputs = screen.getAllByPlaceholderText('••••••••')
    fireEvent.change(passwordInputs[0], { target: { value: 'StrongPass123!' } })
    fireEvent.change(passwordInputs[1], { target: { value: 'StrongPass123!' } })

    fireEvent.click(screen.getByText(/Accept Invitation & Activate Account/i))

    await waitFor(() => {
      expect(screen.getByText(/Account Created Successfully/i)).toBeDefined()
      expect(screen.getByText(/Go to Login/i)).toBeDefined()
    })

    // Token must not be stored in localStorage or sessionStorage
    expect(localStorage.getItem('token')).toBeNull()
    expect(sessionStorage.getItem('token')).toBeNull()
  })
})
