/**
 * GreenSynth Analytics — Member Invitation API Service
 */

import apiClient from './api'
import type {
  AcceptInvitationPayload,
  InvitationSummary,
  InvitationValidationResponse,
} from '@/types'

export const invitationService = {
  /**
   * Validates an onboarding token before account setup and returns safe group details.
   */
  async validateInvitation(token: string): Promise<InvitationValidationResponse> {
    try {
      const response = await apiClient.get<{
        data: InvitationValidationResponse
        message: string
      }>(`/invitations/validate/${encodeURIComponent(token)}`)
      return response.data.data
    } catch {
      const fallback = await apiClient.get<{
        data: InvitationValidationResponse
        message: string
      }>('/auth/invitations/validate', {
        params: { token },
      })
      return fallback.data.data
    }
  },

  /**
   * Accepts an invitation, activates the student's account, joins the group, and returns JWT.
   */
  async acceptInvitation(
    payload: AcceptInvitationPayload
  ): Promise<{ access_token: string; token_type: string; expires_in: number; user: any }> {
    try {
      const response = await apiClient.post<{
        data: { access_token: string; token_type: string; expires_in: number; user: any }
        message: string
      }>('/invitations/accept', payload)
      return response.data.data
    } catch {
      const fallback = await apiClient.post<{
        data: { access_token: string; token_type: string; expires_in: number; user: any }
        message: string
      }>('/auth/invitations/accept', payload)
      return fallback.data.data
    }
  },

  /**
   * Creates a new member invitation for the specified research group.
   */
  async createInvitation(
    groupId: string,
    payload: { full_name: string; email: string; department?: string; phone?: string; roll_number?: string }
  ): Promise<InvitationSummary> {
    const response = await apiClient.post<{
      data: InvitationSummary
      message: string
    }>(`/groups/${groupId}/invitations`, payload)
    return response.data.data
  },

  /**
   * Lists all invitations for the specified research group.
   */
  async listGroupInvitations(groupId: string): Promise<InvitationSummary[]> {
    const response = await apiClient.get<{
      data: InvitationSummary[]
      message: string
    }>(`/groups/${groupId}/invitations`)
    return response.data.data
  },

  /**
   * Re-issues an onboarding token and re-dispatches the invitation email (Leader or Admin).
   */
  async resendInvitation(invitationId: string, groupId?: string): Promise<InvitationSummary> {
    if (groupId) {
      const response = await apiClient.post<{
        data: InvitationSummary
        message: string
      }>(`/groups/${groupId}/invitations/${invitationId}/resend`)
      return response.data.data
    }
    const response = await apiClient.post<{
      data: InvitationSummary
      message: string
    }>(`/auth/invitations/${invitationId}/resend`)
    return response.data.data
  },

  /**
   * Revokes a pending invitation (Leader or Admin).
   */
  async revokeInvitation(groupId: string, invitationId: string): Promise<InvitationSummary> {
    const response = await apiClient.delete<{
      data: InvitationSummary
      message: string
    }>(`/groups/${groupId}/invitations/${invitationId}`)
    return response.data.data
  },
}

export default invitationService
