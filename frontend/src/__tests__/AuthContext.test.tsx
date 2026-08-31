import { render, screen, waitFor, act } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import React from 'react'
import { AuthProvider, useAuth } from '../context/AuthContext'
import { authService } from '../services/authService'
import { AUTH_TOKEN_KEY, AUTH_UNAUTHORIZED_EVENT } from '../services/api'
import type { UserProfile, TokenResponse } from '../types'

vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(),
    registerLeader: vi.fn(),
    acceptInvitation: vi.fn(),
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
  },
}))

const mockProfile: UserProfile = {
  id: 'user-123',
  username: 'leader_alice',
  email: 'alice@greensynth.edu',
  full_name: 'Dr. Alice',
  department: 'Materials Science',
  phone: '1234567890',
  roll_number: 'ROLL-01',
  role: 'RESEARCHER',
  is_active: true,
  created_at: '2026-08-30T00:00:00Z',
  memberships: [
    {
      group_id: 'group-123',
      group_name: 'Solar Nanotech Lab',
      is_leader: true,
      status: 'ACTIVE',
      project_id: 'proj-123',
      project_code: 'P7',
      joined_at: '2026-08-30T00:00:00Z',
    },
  ],
}

const mockTokenResponse: TokenResponse = {
  access_token: 'test_mock_jwt_token',
  token_type: 'bearer',
  expires_in: 3600,
  user: {
    id: 'user-123',
    username: 'leader_alice',
    email: 'alice@greensynth.edu',
    full_name: 'Dr. Alice',
    department: 'Materials Science',
    phone: '1234567890',
    roll_number: 'ROLL-01',
    role: 'RESEARCHER',
    is_active: true,
    created_at: '2026-08-30T00:00:00Z',
  },
}

function TestConsumer() {
  const { user, isAuthenticated, isLoading, activeProjectCode, isGroupLeader, login, logout } =
    useAuth()

  if (isLoading) return <div>Loading Auth State...</div>

  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'AUTHENTICATED' : 'ANONYMOUS'}</div>
      <div data-testid="user-name">{user?.full_name ?? 'NO_USER'}</div>
      <div data-testid="project-code">{activeProjectCode ?? 'NO_PROJECT'}</div>
      <div data-testid="is-leader">{isGroupLeader ? 'YES_LEADER' : 'NO_LEADER'}</div>
      <button onClick={() => login({ email: 'alice@greensynth.edu', password: 'password123' })}>
        Trigger Login
      </button>
      <button onClick={logout}>Trigger Logout</button>
    </div>
  )
}

describe('AuthContext & AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('initializes as unauthenticated when localStorage is empty', async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-status').textContent).toBe('ANONYMOUS')
      expect(screen.getByTestId('user-name').textContent).toBe('NO_USER')
    })
  })

  it('restores authenticated session when valid token exists in localStorage', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'existing_valid_token')
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockProfile)

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-status').textContent).toBe('AUTHENTICATED')
      expect(screen.getByTestId('user-name').textContent).toBe('Dr. Alice')
      expect(screen.getByTestId('project-code').textContent).toBe('P7')
      expect(screen.getByTestId('is-leader').textContent).toBe('YES_LEADER')
    })
  })

  it('clears session when stored token is rejected by backend', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'expired_token')
    vi.mocked(authService.getCurrentUser).mockRejectedValue(new Error('Unauthorized'))

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-status').textContent).toBe('ANONYMOUS')
      expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull()
    })
  })

  it('logs in successfully and populates auth state', async () => {
    vi.mocked(authService.login).mockResolvedValue(mockTokenResponse)
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockProfile)

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-status').textContent).toBe('ANONYMOUS')
    })

    const loginBtn = screen.getByText('Trigger Login')
    await act(async () => {
      loginBtn.click()
    })

    await waitFor(() => {
      expect(screen.getByTestId('auth-status').textContent).toBe('AUTHENTICATED')
      expect(screen.getByTestId('user-name').textContent).toBe('Dr. Alice')
      expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBe('test_mock_jwt_token')
    })
  })

  it('clears auth state on logout', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'valid_token')
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockProfile)

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-status').textContent).toBe('AUTHENTICATED')
    })

    const logoutBtn = screen.getByText('Trigger Logout')
    act(() => {
      logoutBtn.click()
    })

    await waitFor(() => {
      expect(screen.getByTestId('auth-status').textContent).toBe('ANONYMOUS')
      expect(screen.getByTestId('user-name').textContent).toBe('NO_USER')
      expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull()
    })
  })

  it('handles 401 unauthorized custom window event', async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'valid_token')
    vi.mocked(authService.getCurrentUser).mockResolvedValue(mockProfile)

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-status').textContent).toBe('AUTHENTICATED')
    })

    act(() => {
      window.dispatchEvent(new CustomEvent(AUTH_UNAUTHORIZED_EVENT))
    })

    await waitFor(() => {
      expect(screen.getByTestId('auth-status').textContent).toBe('ANONYMOUS')
    })
  })
})
