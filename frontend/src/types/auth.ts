/**
 * GreenSynth Analytics — Authentication TypeScript Interfaces
 *
 * Strongly typed definitions matching the Phase 3–5 FastAPI backend schemas.
 */

export interface UserRead {
  id: string
  username: string
  email: string
  full_name: string
  department: string
  phone: string
  roll_number: string
  role: string
  account_type?: 'ADMIN' | 'STUDENT' | string
  is_active: boolean
  created_at: string
}

export type User = UserRead

export interface MembershipRead {
  group_id: string
  group_name: string
  is_leader: boolean
  status: string
  project_id: string
  project_code: string
  project_name?: string
  joined_at: string
}

export interface UserProfile extends UserRead {
  memberships: MembershipRead[]
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserRead
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LeaderRegisterRequest {
  full_name: string
  department: string
  phone: string
  password: string
  project_id: string
  roll_number: string
  email: string
  group_name?: string
}

export interface AcceptInvitationRequest {
  token: string
  password: string
}

export interface ProfileUpdateRequest {
  full_name?: string
  department?: string
  phone?: string
  roll_number?: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

