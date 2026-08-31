/**
 * GreenSynth Analytics — Research Group & Member Types
 */

export interface MemberInvitationInput {
  full_name: string
  department: string
  phone: string
  roll_number: string
  email: string
}

export interface LeaderRegisterInput {
  full_name: string
  department: string
  phone: string
  roll_number: string
  email: string
  password: string
  confirm_password?: string
}

export interface GroupMetadataInput {
  name: string
  project_id: string
}

export interface GroupRegistrationPayload {
  leader: LeaderRegisterInput
  group: GroupMetadataInput
  members: MemberInvitationInput[]
}

export interface InvitationSummary {
  id: string
  email: string
  full_name: string
  department: string
  phone: string
  roll_number: string
  status: 'PENDING' | 'ACCEPTED' | 'EXPIRED' | 'CANCELLED'
  expires_at: string
  created_at: string
  accepted_at: string | null
}

export interface GroupRegistrationResponse {
  group_id: string
  group_name: string
  project_id: string
  project_code: string
  leader_id: string
  leader_name: string
  leader_email: string
  invitations: InvitationSummary[]
  access_token: string
  token_type: string
  expires_in: number
}

export interface GroupDetail {
  group_id: string
  group_name: string
  project_id: string
  project_code: string
  project_name: string
  leader_id: string
  leader_name: string
  leader_email: string
  member_count: number
  max_members: number
  user_is_leader: boolean
  created_at: string
}

export interface GroupMember {
  user_id: string
  full_name: string
  department: string
  roll_number: string
  email: string
  is_leader: boolean
  status: string
  joined_at: string
}

export interface InvitationValidationResponse {
  valid: boolean
  group_name: string
  project_id: string
  project_code: string
  project_name: string
  invited_name: string
  invited_email: string
  department: string
  roll_number: string
  leader_name: string
  expires_at: string
}

export interface AcceptInvitationPayload {
  token: string
  password: string
  confirm_password?: string
}
