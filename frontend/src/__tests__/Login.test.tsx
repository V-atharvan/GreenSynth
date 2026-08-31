import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import React from 'react'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import Login from '../pages/Login'
import { AuthProvider } from '../context/AuthContext'
import { authService } from '../services/authService'

vi.mock('../services/authService', () => ({
  authService: {
    login: vi.fn(),
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
  },
}))

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders login form inputs, branding, and navigation links', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )

    expect(screen.getByText('GreenSynth Analytics')).toBeDefined()
    expect(screen.getByText('Researcher Sign In')).toBeDefined()
    expect(screen.getByLabelText('Institutional Email')).toBeDefined()
    expect(screen.getByLabelText('Password')).toBeDefined()
    expect(screen.getByRole('button', { name: /Sign In to Research Portal/i })).toBeDefined()
    expect(screen.getByText('Register Research Group as Leader')).toBeDefined()
    expect(screen.getByText('Accept Member Invitation / Join Group')).toBeDefined()
  })

  it('validates empty email and password before submit', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )

    const submitBtn = screen.getByRole('button', { name: /Sign In to Research Portal/i })
    await act(async () => {
      fireEvent.click(submitBtn)
    })

    expect(screen.getByText('Please enter your institutional email address.')).toBeDefined()
  })

  it('displays error banner on authentication failure', async () => {
    vi.mocked(authService.login).mockRejectedValue(new Error('Invalid email or password.'))

    render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )

    const emailInput = screen.getByLabelText('Institutional Email')
    const passwordInput = screen.getByLabelText('Password')
    const submitBtn = screen.getByRole('button', { name: /Sign In to Research Portal/i })

    fireEvent.change(emailInput, { target: { value: 'alice@greensynth.edu' } })
    fireEvent.change(passwordInput, { target: { value: 'wrongpass' } })

    await act(async () => {
      fireEvent.click(submitBtn)
    })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeDefined()
      expect(screen.getByText('Invalid email or password.')).toBeDefined()
    })
  })

  it('toggles password visibility with toggle button', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )

    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement
    expect(passwordInput.type).toBe('password')

    const toggleBtn = screen.getByLabelText('Show password')
    fireEvent.click(toggleBtn)

    expect(passwordInput.type).toBe('text')
    expect(screen.getByLabelText('Hide password')).toBeDefined()
  })

  it('contains NO role dropdowns, account type selectors, or separate admin login buttons', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )

    // Ensure strictly unified single login interface
    expect(screen.queryByText(/Admin Login/i)).toBeNull()
    expect(screen.queryByText(/Student Login/i)).toBeNull()
    expect(screen.queryByText(/Login as Admin/i)).toBeNull()
    expect(screen.queryByText(/Login as Student/i)).toBeNull()
    expect(screen.queryByText(/Select Role/i)).toBeNull()
    expect(screen.queryByText(/Account Type/i)).toBeNull()
    expect(screen.queryByRole('combobox')).toBeNull()
  })

  it('redirects Admin user to /admin on successful login', async () => {
    vi.mocked(authService.login).mockResolvedValue({
      access_token: 'admin-fake-jwt',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        id: '11111111-1111-1111-1111-111111111111',
        username: 'admin',
        email: 'v.atharvan@gmail.com',
        full_name: 'Administrator',
        department: 'Central Lab',
        phone: '1234567890',
        roll_number: 'ADM-001',
        role: 'ADMIN',
        account_type: 'ADMIN',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
      },
    })
    vi.mocked(authService.getCurrentUser).mockResolvedValue({
      id: '11111111-1111-1111-1111-111111111111',
      username: 'admin',
      email: 'v.atharvan@gmail.com',
      full_name: 'Administrator',
      department: 'Central Lab',
      phone: '1234567890',
      roll_number: 'ADM-001',
      role: 'ADMIN',
      account_type: 'ADMIN',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
      memberships: [],
    })

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )

    const emailInput = screen.getByLabelText('Institutional Email')
    const passwordInput = screen.getByLabelText('Password')
    const submitBtn = screen.getByRole('button', { name: /Sign In to Research Portal/i })

    fireEvent.change(emailInput, { target: { value: 'v.atharvan@gmail.com' } })
    fireEvent.change(passwordInput, { target: { value: 'aaaaaaaa' } })

    await act(async () => {
      fireEvent.click(submitBtn)
    })

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith({
        email: 'v.atharvan@gmail.com',
        password: 'aaaaaaaa',
      })
    })
  })

  it('redirects Student user to /dashboard on successful login', async () => {
    vi.mocked(authService.login).mockResolvedValue({
      access_token: 'student-fake-jwt',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        id: '22222222-2222-2222-2222-222222222222',
        username: 'student1',
        email: 'student1@greensynth.edu',
        full_name: 'Student One',
        department: 'Chemistry',
        phone: '1234567890',
        roll_number: 'STU-001',
        role: 'RESEARCHER',
        account_type: 'STUDENT',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
      },
    })
    vi.mocked(authService.getCurrentUser).mockResolvedValue({
      id: '22222222-2222-2222-2222-222222222222',
      username: 'student1',
      email: 'student1@greensynth.edu',
      full_name: 'Student One',
      department: 'Chemistry',
      phone: '1234567890',
      roll_number: 'STU-001',
      role: 'RESEARCHER',
      account_type: 'STUDENT',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
      memberships: [],
    })

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )

    const emailInput = screen.getByLabelText('Institutional Email')
    const passwordInput = screen.getByLabelText('Password')
    const submitBtn = screen.getByRole('button', { name: /Sign In to Research Portal/i })

    fireEvent.change(emailInput, { target: { value: 'student1@greensynth.edu' } })
    fireEvent.change(passwordInput, { target: { value: 'secretpass' } })

    await act(async () => {
      fireEvent.click(submitBtn)
    })

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith({
        email: 'student1@greensynth.edu',
        password: 'secretpass',
      })
    })
  })
})
