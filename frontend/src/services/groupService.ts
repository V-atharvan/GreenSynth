/**
 * GreenSynth Analytics — Research Group API Service
 */

import apiClient from './api'
import type {
  GroupDetail,
  GroupMember,
  GroupRegistrationPayload,
  GroupRegistrationResponse,
  InvitationSummary,
  MemberInvitationInput,
} from '@/types'

export const groupService = {
  /**
   * Atomically registers a Group Leader, creates their Research Group,
   * assigns the selected Project, and sends invitations to all members.
   */
  async registerGroupWithMembers(
    payload: GroupRegistrationPayload
  ): Promise<GroupRegistrationResponse> {
    const response = await apiClient.post<{ data: GroupRegistrationResponse; message: string }>(
      '/groups/register',
      payload
    )
    return response.data.data
  },

  /**
   * Retrieves the current user's research group metadata and project binding.
   */
  async getMyGroup(): Promise<GroupDetail> {
    const response = await apiClient.get<{ data: GroupDetail; message: string }>('/groups/me')
    return response.data.data
  },

  /**
   * Retrieves all active members of the current user's research group.
   */
  async getMyGroupMembers(): Promise<GroupMember[]> {
    const response = await apiClient.get<{ data: GroupMember[]; message: string }>(
      '/groups/me/members'
    )
    return response.data.data
  },

  /**
   * Retrieves all invitation records for the current user's research group.
   */
  async getMyGroupInvitations(): Promise<InvitationSummary[]> {
    const response = await apiClient.get<{ data: InvitationSummary[]; message: string }>(
      '/groups/me/invitations'
    )
    return response.data.data
  },

  /**
   * Sends an additional member invitation (Leader only, within max capacity).
   */
  async inviteMember(payload: MemberInvitationInput): Promise<InvitationSummary> {
    const response = await apiClient.post<{ data: InvitationSummary; message: string }>(
      '/groups/me/invitations',
      payload
    )
    return response.data.data
  },
}

export default groupService
