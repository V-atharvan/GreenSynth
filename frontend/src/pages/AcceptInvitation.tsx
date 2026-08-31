/**
 * GreenSynth Analytics — Member Onboarding / Accept Invitation Page
 *
 * Validates onboarding token, displays assigned research group and project details,
 * and allows the invited student to create their account password.
 */

import React, { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams, Link } from 'react-router-dom'
import {
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  FlaskConical,
  Lock,
  ArrowRight,
  UserCheck,
  Building2,
  Users,
} from 'lucide-react'
import { invitationService } from '@/services/invitationService'
import { useAuth } from '@/context/AuthContext'
import type { InvitationValidationResponse } from '@/types'

export default function AcceptInvitation() {
  const params = useParams<{ token?: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setAuthSession } = useAuth()
  const token = params.token || searchParams.get('token')

  const [loading, setLoading] = useState<boolean>(true)
  const [submitting, setSubmitting] = useState<boolean>(false)
  const [validationInfo, setValidationInfo] = useState<InvitationValidationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<boolean>(false)

  const [password, setPassword] = useState<string>('')
  const [confirmPassword, setConfirmPassword] = useState<string>('')
  const [formError, setFormError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) {
      setError('No invitation token found. Please click the invitation link received in your email.')
      setLoading(false)
      return
    }

    async function validate() {
      try {
        setLoading(true)
        const info = await invitationService.validateInvitation(token!)
        setValidationInfo(info)
        setError(null)
      } catch (err: any) {
        setError(err.message || 'This invitation is invalid or has expired.')
      } finally {
        setLoading(false)
      }
    }

    validate()
  }, [token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)

    if (!password || password.length < 8) {
      setFormError('Password must be at least 8 characters in length.')
      return
    }

    if (password !== confirmPassword) {
      setFormError('Passwords do not match.')
      return
    }

    setSubmitting(true)
    try {
      const response = await invitationService.acceptInvitation({
        token: token!,
        password,
        confirm_password: confirmPassword,
      })

      if (response.access_token) {
        await setAuthSession(response.access_token)
      }

      setSuccess(true)
    } catch (err: any) {
      setFormError(err.message || 'Failed to accept invitation. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="container" style={{ maxWidth: '540px', margin: '80px auto', textAlign: 'center' }}>
        <div style={{ color: '#0f766e', fontWeight: 600, fontSize: '16px' }}>
          Validating research group invitation...
        </div>
      </div>
    )
  }

  if (error || !validationInfo) {
    return (
      <div className="container" style={{ maxWidth: '540px', margin: '80px auto', padding: '0 16px' }}>
        <div style={{ background: '#ffffff', border: '1px solid #fee2e2', borderRadius: '12px', padding: '32px', textAlign: 'center', boxShadow: '0 4px 16px rgba(0,0,0,0.04)' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#fee2e2', color: '#dc2626', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px auto' }}>
            <AlertCircle size={28} />
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>
            Invitation Invalid or Expired
          </h2>
          <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '24px', lineHeight: 1.5 }}>
            {error || 'Unable to validate your invitation.'}
          </p>
          <Link
            to="/register"
            style={{ display: 'inline-block', background: '#0f766e', color: '#ffffff', padding: '10px 20px', borderRadius: '6px', fontSize: '14px', fontWeight: 600, textDecoration: 'none' }}
          >
            Go to Registration
          </Link>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="container" style={{ maxWidth: '540px', margin: '80px auto', padding: '0 16px' }}>
        <div style={{ background: '#ffffff', border: '1px solid #bbf7d0', borderRadius: '12px', padding: '32px', textAlign: 'center', boxShadow: '0 4px 16px rgba(0,0,0,0.04)' }}>
          <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: '#dcfce7', color: '#16a34a', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px auto' }}>
            <CheckCircle2 size={32} />
          </div>
          <h2 style={{ fontSize: '22px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>
            Account Created Successfully
          </h2>
          <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '16px', lineHeight: 1.5 }}>
            Your GreenSynth student account has been activated.
          </p>
          <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '12px', marginBottom: '24px', fontSize: '13px', color: '#334155' }}>
            <div>Email: <strong>{validationInfo.invited_email}</strong></div>
            <div style={{ marginTop: '4px' }}>Group: <strong>{validationInfo.group_name}</strong> ({validationInfo.project_code})</div>
          </div>
          <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '24px' }}>
            You can now sign in using the unified GreenSynth login page.
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <button
              onClick={() => navigate('/login')}
              style={{ background: '#0f766e', color: '#ffffff', border: 'none', padding: '12px 24px', borderRadius: '6px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}
            >
              Go to Login
            </button>
            <button
              onClick={() => navigate('/')}
              style={{ background: '#f1f5f9', color: '#0f172a', border: '1px solid #cbd5e1', padding: '12px 20px', borderRadius: '6px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}
            >
              Enter Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container" style={{ maxWidth: '600px', margin: '40px auto', padding: '0 16px' }}>
      <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '32px', boxShadow: '0 4px 16px rgba(0,0,0,0.03)' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 12px', background: 'rgba(15, 118, 110, 0.1)', borderRadius: '16px', color: '#0f766e', fontSize: '12px', fontWeight: 600, marginBottom: '10px' }}>
            <Users size={14} /> Research Group Invitation
          </div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, color: '#0f172a', margin: '0 0 6px 0' }}>
            Join {validationInfo.group_name}
          </h1>
          <p style={{ color: '#64748b', fontSize: '13px', margin: 0 }}>
            Invited by Group Leader: <strong>{validationInfo.leader_name}</strong>
          </p>
        </div>

        {/* Assigned Project Card */}
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', marginBottom: '24px' }}>
          <div style={{ fontSize: '12px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Assigned Synthesis Project
          </div>
          <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f766e', marginTop: '2px' }}>
            {validationInfo.project_code} — {validationInfo.project_name}
          </div>
          <div style={{ fontSize: '12px', color: '#475569', marginTop: '6px' }}>
            Student: <strong>{validationInfo.invited_name}</strong> ({validationInfo.department}) • Roll: {validationInfo.roll_number}
          </div>
        </div>

        {formError && (
          <div style={{ padding: '10px 14px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', color: '#991b1b', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}>
            <AlertCircle size={16} />
            <span>{formError}</span>
          </div>
        )}

        {/* Password Setup Form */}
        <form onSubmit={handleSubmit}>
          {/* Read-Only Email Field */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#334155', marginBottom: '6px' }}>
              Invited Email Address (Read-Only)
            </label>
            <input
              type="email"
              value={validationInfo.invited_email}
              disabled
              readOnly
              style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #e2e8f0', background: '#f1f5f9', color: '#64748b', fontSize: '14px', cursor: 'not-allowed' }}
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#334155', marginBottom: '6px' }}>
              Create Your Password (min 8 chars) *
            </label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
              required
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#334155', marginBottom: '6px' }}>
              Confirm Password *
            </label>
            <input
              type="password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
              required
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', background: '#0f766e', color: '#ffffff', border: 'none', padding: '12px', borderRadius: '6px', fontSize: '14px', fontWeight: 600, cursor: submitting ? 'not-allowed' : 'pointer', opacity: submitting ? 0.7 : 1 }}
          >
            {submitting ? 'Activating Account...' : 'Accept Invitation & Activate Account'} <ArrowRight size={16} />
          </button>
        </form>
      </div>
    </div>
  )
}
