/**
 * GreenSynth Analytics — Authentication State Context & Provider
 *
 * Centralizes user authentication state, session restoration, JWT persistence,
 * and project/group membership resolution.
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react'
import { authService } from '@/services/authService'
import { AUTH_TOKEN_KEY, AUTH_UNAUTHORIZED_EVENT } from '@/services/api'
import type {
  AcceptInvitationRequest,
  LeaderRegisterRequest,
  LoginRequest,
  MembershipRead,
  TokenResponse,
  UserProfile,
} from '@/types'

export interface AuthContextValue {
  user: UserProfile | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  isAdmin: boolean
  accountType: 'ADMIN' | 'STUDENT'
  activeMembership: MembershipRead | null
  activeProjectCode: string | null
  isGroupLeader: boolean
  login: (credentials: LoginRequest) => Promise<UserProfile>
  logout: () => void
  registerLeader: (data: LeaderRegisterRequest) => Promise<TokenResponse>
  acceptInvitation: (data: AcceptInvitationRequest) => Promise<TokenResponse>
  refreshUser: () => Promise<void>
  setAuthSession: (token: string, profile?: UserProfile) => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [token, setToken] = useState<string | null>(() => {
    return typeof window !== 'undefined' ? localStorage.getItem(AUTH_TOKEN_KEY) : null
  })
  const [isLoading, setIsLoading] = useState<boolean>(true)

  // ── Session Restoration on Mount ────────────────────────────
  const refreshUser = useCallback(async () => {
    const storedToken = localStorage.getItem(AUTH_TOKEN_KEY)
    if (!storedToken) {
      setUser(null)
      setToken(null)
      setIsLoading(false)
      return
    }

    try {
      const profile = await authService.getCurrentUser()
      setUser(profile)
      setToken(storedToken)
    } catch {
      // Token is invalid or expired
      localStorage.removeItem(AUTH_TOKEN_KEY)
      setUser(null)
      setToken(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  // ── Listen for 401 Unauthorized Events ──────────────────────
  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null)
      setToken(null)
      setIsLoading(false)
    }

    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized)
    return () => {
      window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized)
    }
  }, [])

  // ── Set Session Helper ──────────────────────────────────────
  const setAuthSession = useCallback(async (accessToken: string, profile?: UserProfile) => {
    localStorage.setItem(AUTH_TOKEN_KEY, accessToken)
    setToken(accessToken)
    if (profile) {
      setUser(profile)
      setIsLoading(false)
    } else {
      try {
        const fetchedProfile = await authService.getCurrentUser()
        setUser(fetchedProfile)
      } catch {
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }
  }, [])

  // ── Authentication Actions ──────────────────────────────────
  const login = useCallback(
    async (credentials: LoginRequest): Promise<UserProfile> => {
      setIsLoading(true)
      try {
        const res = await authService.login(credentials)
        localStorage.setItem(AUTH_TOKEN_KEY, res.access_token)
        setToken(res.access_token)
        const profile = await authService.getCurrentUser()
        setUser(profile)
        setIsLoading(false)
        return profile
      } catch (err) {
        setIsLoading(false)
        throw err
      }
    },
    []
  )

  const registerLeader = useCallback(
    async (data: LeaderRegisterRequest): Promise<TokenResponse> => {
      setIsLoading(true)
      try {
        const res = await authService.registerLeader(data)
        await setAuthSession(res.access_token)
        return res
      } catch (err) {
        setIsLoading(false)
        throw err
      }
    },
    [setAuthSession]
  )

  const acceptInvitation = useCallback(
    async (data: AcceptInvitationRequest): Promise<TokenResponse> => {
      setIsLoading(true)
      try {
        const res = await authService.acceptInvitation(data)
        await setAuthSession(res.access_token)
        return res
      } catch (err) {
        setIsLoading(false)
        throw err
      }
    },
    [setAuthSession]
  )

  const logout = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    authService.logout()
    setUser(null)
    setToken(null)
    setIsLoading(false)
  }, [])

  // ── Computed Group & Project Context ────────────────────────
  const activeMembership = useMemo<MembershipRead | null>(() => {
    if (!user || !user.memberships || user.memberships.length === 0) return null
    return user.memberships.find((m) => m.status === 'ACTIVE') || user.memberships[0]
  }, [user])

  const activeProjectCode = useMemo<string | null>(() => {
    return activeMembership?.project_code ?? null
  }, [activeMembership])

  const isGroupLeader = useMemo<boolean>(() => {
    return activeMembership?.is_leader ?? false
  }, [activeMembership])

  const isAdmin = useMemo<boolean>(() => {
    if (!user) return false
    return user.account_type === 'ADMIN' || user.role === 'ADMIN'
  }, [user])

  const accountType = useMemo<'ADMIN' | 'STUDENT'>(() => {
    return isAdmin ? 'ADMIN' : 'STUDENT'
  }, [isAdmin])

  const isAuthenticated = useMemo<boolean>(() => {
    return !!token && !!user
  }, [token, user])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated,
      isLoading,
      isAdmin,
      accountType,
      activeMembership,
      activeProjectCode,
      isGroupLeader,
      login,
      logout,
      registerLeader,
      acceptInvitation,
      refreshUser,
      setAuthSession,
    }),
    [
      user,
      token,
      isAuthenticated,
      isLoading,
      isAdmin,
      accountType,
      activeMembership,
      activeProjectCode,
      isGroupLeader,
      login,
      logout,
      registerLeader,
      acceptInvitation,
      refreshUser,
      setAuthSession,
    ]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext
