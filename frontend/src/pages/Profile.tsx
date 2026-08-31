/**
 * GreenSynth Analytics — Profile Page
 *
 * Account management page answering:
 *   - Who is the currently authenticated user?
 *   - What account type do they have? (ADMIN / STUDENT)
 *   - What research access do they have?
 *   - Is the account active?
 *   - When was the account created/updated?
 *   - Can they safely logout?
 */

import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  User as UserIcon,
  Lock,
  Shield,
  Save,
  LogOut,
  CheckCircle2,
  AlertCircle,
  Calendar,
  Layers,
  FolderKanban,
  Users,
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { authService } from '@/services/authService'
import { groupService } from '@/services/groupService'
import { projectService } from '@/services/projectService'
import type { UserProfile, GroupDetail, ProjectSummary } from '@/types'

function getInitials(name: string): string {
  if (!name) return 'GS'
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return 'GS'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

function formatDate(dateStr?: string | null): string {
  if (!dateStr) return '—'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return d.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

export default function Profile() {
  const navigate = useNavigate()
  const { user: authUser, isAdmin, logout, refreshUser } = useAuth()

  // Profile data & form state
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [saving, setSaving] = useState<boolean>(false)
  const [fullName, setFullName] = useState<string>('')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Student research data
  const [groupDetails, setGroupDetails] = useState<GroupDetail | null>(null)
  const [assignedProject, setAssignedProject] = useState<ProjectSummary | null>(null)
  const [researchLoading, setResearchLoading] = useState<boolean>(false)

  // Load current user profile
  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    setLoading(true)
    setErrorMsg(null)
    try {
      const data = await authService.getCurrentUser()
      setProfile(data)
      setFullName(data.full_name || '')

      if (!isAdmin && data.memberships && data.memberships.length > 0) {
        loadResearchData(data.memberships[0].project_id)
      }
    } catch (err: any) {
      setErrorMsg(err?.message || 'Unable to load profile information.')
    } finally {
      setLoading(false)
    }
  }

  const loadResearchData = async (projectId: string) => {
    setResearchLoading(true)
    try {
      const [gData, pList] = await Promise.all([
        groupService.getMyGroup().catch(() => null),
        projectService.getCatalog().catch(() => []),
      ])
      if (gData) setGroupDetails(gData)
      const matched = (pList as ProjectSummary[]).find((p) => p.id === projectId)
      if (matched) setAssignedProject(matched)
    } catch (err) {
      console.error('Failed to load research metadata:', err)
    } finally {
      setResearchLoading(false)
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)
    setSuccessMsg(null)

    const trimmed = fullName.trim()
    if (!trimmed) {
      setErrorMsg('Full Name cannot be empty.')
      return
    }

    setSaving(true)
    try {
      const updated = await authService.updateProfile({
        full_name: trimmed,
      })
      setProfile(updated)
      setFullName(updated.full_name)
      setSuccessMsg('Profile updated successfully.')
      if (refreshUser) {
        refreshUser()
      }
      setTimeout(() => setSuccessMsg(null), 4000)
    } catch (err: any) {
      setErrorMsg(err?.message || 'Unable to update profile. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isFormDirty = profile ? fullName.trim() !== (profile.full_name || '').trim() : false
  const accountTypeLabel = (profile?.account_type || authUser?.account_type || (isAdmin ? 'ADMIN' : 'STUDENT')) === 'ADMIN'
    ? 'Administrator'
    : 'Student'

  const isActive = profile ? profile.is_active : (authUser ? authUser.is_active : true)
  const initials = getInitials(profile?.full_name || authUser?.full_name || '')

  return (
    <div className="gs-page" id="profile-page" style={{ maxWidth: 860, margin: '0 auto' }}>
      {/* 1. Page Header */}
      <div className="gs-page-header">
        <div>
          <div className="gs-page-title">
            <div className="gs-page-title-icon indigo">
              <UserIcon size={20} />
            </div>
            Profile
          </div>
          <p className="gs-page-subtitle">
            Manage your personal account information
          </p>
        </div>
      </div>

      {loading ? (
        <div className="gs-panel">
          <div className="gs-loading-placeholder">Loading account profile...</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* 2. Profile Summary Card */}
          <div className="gs-panel">
            <div className="gs-panel-body" style={{ padding: '24px 28px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
                <div
                  style={{
                    width: 64,
                    height: 64,
                    borderRadius: '50%',
                    background: isAdmin ? 'linear-gradient(135deg, #4f46e5 0%, #3730a3 100%)' : 'linear-gradient(135deg, #0f766e 0%, #0d9488 100%)',
                    color: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.375rem',
                    fontWeight: 700,
                    letterSpacing: '0.04em',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
                    flexShrink: 0,
                  }}
                  aria-label={`Avatar for ${profile?.full_name || 'User'}`}
                >
                  {initials}
                </div>

                <div style={{ flex: 1, minWidth: 200 }}>
                  <h2 style={{ margin: '0 0 4px 0', fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-text)' }}>
                    {profile?.full_name || authUser?.full_name || 'GreenSynth User'}
                  </h2>
                  <div style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: 8 }}>
                    {profile?.email || authUser?.email || ''}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6,
                        fontSize: '0.8125rem',
                        fontWeight: 600,
                        color: isActive ? '#059669' : '#e11d48',
                      }}
                    >
                      <span
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          backgroundColor: isActive ? '#10b981' : '#f43f5e',
                          display: 'inline-block',
                        }}
                      />
                      {isActive ? 'Active' : 'Inactive'}
                    </span>
                    <span className={`gs-badge ${isAdmin ? 'indigo' : 'teal'}`}>
                      {accountTypeLabel}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 3. Personal Information Card */}
          <div className="gs-panel">
            <div className="gs-panel-header">
              <span className="gs-panel-title">Personal Information</span>
            </div>
            <div className="gs-panel-body">
              {successMsg && (
                <div className="gs-alert success" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                  <CheckCircle2 size={16} /> {successMsg}
                </div>
              )}
              {errorMsg && (
                <div className="gs-alert error" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                  <AlertCircle size={16} /> {errorMsg}
                </div>
              )}

              <form onSubmit={handleSave}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 18 }}>
                  {/* Full Name (Editable) */}
                  <div className="gs-field">
                    <label className="gs-label" htmlFor="profile-full-name">Full Name</label>
                    <input
                      id="profile-full-name"
                      type="text"
                      className="gs-input"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      required
                      placeholder="Enter your full name"
                    />
                  </div>

                  {/* Email Address (Read-Only) */}
                  <div className="gs-field">
                    <label className="gs-label" htmlFor="profile-email">
                      Email Address
                    </label>
                    <div style={{ position: 'relative' }}>
                      <input
                        id="profile-email"
                        type="email"
                        className="gs-input"
                        value={profile?.email || authUser?.email || ''}
                        disabled
                        readOnly
                        style={{ background: 'var(--color-bg)', cursor: 'not-allowed', paddingRight: 36 }}
                      />
                      <Lock
                        size={14}
                        style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-secondary)' }}
                        aria-hidden="true"
                      />
                    </div>
                  </div>

                  {/* Account Type (Read-Only) */}
                  <div className="gs-field">
                    <label className="gs-label" htmlFor="profile-account-type">
                      Account Type
                    </label>
                    <div style={{ position: 'relative' }}>
                      <input
                        id="profile-account-type"
                        type="text"
                        className="gs-input"
                        value={accountTypeLabel}
                        disabled
                        readOnly
                        style={{ background: 'var(--color-bg)', cursor: 'not-allowed', paddingRight: 36, fontWeight: 600 }}
                      />
                      <Lock
                        size={14}
                        style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-secondary)' }}
                        aria-hidden="true"
                      />
                    </div>
                  </div>

                  {/* Account Status (Read-Only) */}
                  <div className="gs-field">
                    <label className="gs-label" htmlFor="profile-account-status">
                      Account Status
                    </label>
                    <div style={{ position: 'relative' }}>
                      <input
                        id="profile-account-status"
                        type="text"
                        className="gs-input"
                        value={isActive ? 'Active' : 'Inactive'}
                        disabled
                        readOnly
                        style={{ background: 'var(--color-bg)', cursor: 'not-allowed', paddingRight: 36 }}
                      />
                      <Lock
                        size={14}
                        style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-secondary)' }}
                        aria-hidden="true"
                      />
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    type="submit"
                    disabled={!isFormDirty || saving}
                    className="gs-btn gs-btn-teal"
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                  >
                    <Save size={16} />
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* 4. Research Information Card */}
          <div className="gs-panel">
            <div className="gs-panel-header">
              <span className="gs-panel-title">
                {isAdmin ? 'Research Access' : 'Research Information'}
              </span>
              <span className={`gs-badge ${isAdmin ? 'indigo' : 'green'}`}>
                {isAdmin ? 'SYSTEM-WIDE' : 'GROUP-SCOPED'}
              </span>
            </div>
            <div className="gs-panel-body">
              {isAdmin ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
                  <div className="gs-card" style={{ padding: 16 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Shield size={14} className="text-indigo-600" /> Access Level
                    </div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 700, marginTop: 6, color: 'var(--color-text)' }}>
                      System-wide
                    </div>
                  </div>

                  <div className="gs-card" style={{ padding: 16 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Users size={14} className="text-indigo-600" /> Research Groups
                    </div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 700, marginTop: 6, color: 'var(--color-text)' }}>
                      All Groups
                    </div>
                  </div>

                  <div className="gs-card" style={{ padding: 16 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <FolderKanban size={14} className="text-indigo-600" /> Projects
                    </div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 700, marginTop: 6, color: 'var(--color-text)' }}>
                      P1 – P8
                    </div>
                  </div>
                </div>
              ) : researchLoading ? (
                <div className="gs-loading-placeholder">Loading research access details...</div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
                  <div className="gs-card" style={{ padding: 16 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                      Research Group
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 4, color: 'var(--color-text)' }}>
                      {groupDetails?.group_name || profile?.memberships?.[0]?.group_name || 'Not assigned'}
                    </div>
                  </div>

                  <div className="gs-card" style={{ padding: 16 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                      Group Role
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 4, color: 'var(--color-text)' }}>
                      {profile?.memberships && profile.memberships.length > 0
                        ? profile.memberships[0].is_leader ? 'Group Leader' : 'Member'
                        : 'Not assigned'}
                    </div>
                  </div>

                  <div className="gs-card" style={{ padding: 16 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                      Group Leader
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 4, color: 'var(--color-text)' }}>
                      {groupDetails?.leader_name || 'Not available'}
                    </div>
                  </div>

                  <div className="gs-card" style={{ padding: 16 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                      Assigned Project
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 4, color: '#0f766e' }}>
                      {profile?.memberships?.[0]?.project_code || assignedProject?.project_code || 'Not assigned'}
                    </div>
                  </div>

                  <div className="gs-card" style={{ padding: 16, gridColumn: '1 / -1' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                      Project Name
                    </div>
                    <div style={{ fontSize: '0.9375rem', fontWeight: 600, marginTop: 4, color: 'var(--color-text)' }}>
                      {assignedProject?.name || profile?.memberships?.[0]?.project_name || 'Not assigned'}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 5. Account Information Card */}
          <div className="gs-panel">
            <div className="gs-panel-header">
              <span className="gs-panel-title">Account Information</span>
            </div>
            <div className="gs-panel-body">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
                <div className="gs-card" style={{ padding: 16 }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Calendar size={14} /> Account Created
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: 6, color: 'var(--color-text)' }}>
                    {formatDate(profile?.created_at || authUser?.created_at)}
                  </div>
                </div>

                <div className="gs-card" style={{ padding: 16 }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Layers size={14} /> Last Updated
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: 6, color: 'var(--color-text)' }}>
                    {formatDate(profile?.created_at || authUser?.created_at)}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 6. Account Actions Card */}
          <div className="gs-panel">
            <div className="gs-panel-header">
              <span className="gs-panel-title">Account Actions</span>
            </div>
            <div className="gs-panel-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--color-text)', fontSize: '0.9375rem' }}>
                  Sign out of your GreenSynth account
                </div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
                  Terminates your current authenticated session and clears credentials.
                </div>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="gs-btn gs-btn-outline"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  color: '#e11d48',
                  borderColor: '#fecdd3',
                }}
              >
                <LogOut size={16} />
                Logout
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
