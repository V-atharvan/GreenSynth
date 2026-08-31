/**
 * GreenSynth Analytics — Authentication API Service
 *
 * Communicates with backend authentication endpoints:
 *   - POST /auth/login
 *   - POST /auth/register-leader
 *   - POST /auth/accept-invitation
 *   - GET  /auth/me
 */

import apiClient, { AUTH_TOKEN_KEY } from './api'
import type {
  AcceptInvitationRequest,
  ChangePasswordRequest,
  LeaderRegisterRequest,
  LoginRequest,
  ProfileUpdateRequest,
  TokenResponse,
  UserProfile,
} from '@/types'

export const authService = {
  /**
   * Authenticate with email & password and retrieve JWT access token.
   */
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<{
      data: TokenResponse
      message: string
    }>('/auth/login', credentials)
    return response.data.data
  },

  /**
   * Register a new Group Leader, create their Research Group, and receive JWT.
   */
  async registerLeader(data: LeaderRegisterRequest): Promise<TokenResponse> {
    const response = await apiClient.post<{
      data: TokenResponse
      message: string
    }>('/auth/register-leader', data)
    return response.data.data
  },

  /**
   * Accept an invitation token, set password, activate account, and receive JWT.
   */
  async acceptInvitation(data: AcceptInvitationRequest): Promise<TokenResponse> {
    const response = await apiClient.post<{
      data: TokenResponse
      message: string
    }>('/auth/accept-invitation', data)
    return response.data.data
  },

  /**
   * Retrieve the current authenticated user's profile and active research group memberships.
   */
  async getCurrentUser(): Promise<UserProfile> {
    const response = await apiClient.get<{
      data: UserProfile
      message: string
    }>('/auth/me')
    return response.data.data
  },

  /**
   * Update permitted profile fields for the authenticated user.
   */
  async updateProfile(data: ProfileUpdateRequest): Promise<UserProfile> {
    const response = await apiClient.patch<{
      data: UserProfile
      message: string
    }>('/auth/me', data)
    return response.data.data
  },

  /**
   * Change password for the current authenticated user.
   */
  async changePassword(data: ChangePasswordRequest): Promise<{ status: string; message: string }> {
    const response = await apiClient.post<{
      data: { status: string; message: string }
      message: string
    }>('/auth/change-password', data)
    return response.data.data
  },

  /**
   * Terminate current client-side session by removing stored JWT token.
   */
  logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(AUTH_TOKEN_KEY)
    }
  },
}

export default authService
