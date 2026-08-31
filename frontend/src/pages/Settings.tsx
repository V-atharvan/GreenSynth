/**
 * GreenSynth Analytics — Settings Module Page
 *
 * Provides a unified settings interface for both Students and Administrators.
 * Contains:
 *   - Account: Profile editing, Password change
 *   - Research: Active group and project assignment
 *   - Administration (Admin only): Users, Groups, and Projects
 *   - System: About & Platform specifications
 */

import React, { useEffect, useState } from 'react'
import {
  User as UserIcon,
  Lock,
  FlaskConical,
  Users,
  Building2,
  FolderKanban,
  Info,
  CheckCircle2,
  AlertCircle,
  Shield,
  Save,
  KeyRound,
  RefreshCw,
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { authService } from '@/services/authService'
import { adminService } from '@/services/adminService'
import { groupService } from '@/services/groupService'
import { projectService } from '@/services/projectService'
import type { UserProfile, User, GroupDetail, GroupMember, Project, ProjectSummary } from '@/types'

type SettingsTab =
  | 'profile'
  | 'password'
  | 'research'
  | 'admin-users'
  | 'admin-groups'
  | 'admin-projects'
  | 'about'

export default function Settings() {
  const { user: authUser, isAdmin, refreshUser } = useAuth()
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile')

  // Profile State
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [profileLoading, setProfileLoading] = useState<boolean>(true)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null)
  const [savingProfile, setSavingProfile] = useState<boolean>(false)
  const [fullName, setFullName] = useState<string>('')
  const [department, setDepartment] = useState<string>('')
  const [phone, setPhone] = useState<string>('')
  const [rollNumber, setRollNumber] = useState<string>('')

  // Password Change State
  const [currentPassword, setCurrentPassword] = useState<string>('')
  const [newPassword, setNewPassword] = useState<string>('')
  const [confirmPassword, setConfirmPassword] = useState<string>('')
  const [passwordLoading, setPasswordLoading] = useState<boolean>(false)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null)

  // Research State (Student)
  const [groupDetails, setGroupDetails] = useState<GroupDetail | null>(null)
  const [groupMembers, setGroupMembers] = useState<GroupMember[]>([])
  const [assignedProject, setAssignedProject] = useState<ProjectSummary | null>(null)
  const [researchLoading, setResearchLoading] = useState<boolean>(false)

  // Admin Data State
  const [adminUsers, setAdminUsers] = useState<User[]>([])
  const [adminGroups, setAdminGroups] = useState<GroupDetail[]>([])
  const [adminProjects, setAdminProjects] = useState<Project[]>([])
  const [adminDataLoading, setAdminDataLoading] = useState<boolean>(false)
  const [adminError, setAdminError] = useState<string | null>(null)
  const [adminSuccess, setAdminSuccess] = useState<string | null>(null)

  // Load current user profile on mount
  useEffect(() => {
    loadUserProfile()
  }, [])

  const loadUserProfile = async () => {
    setProfileLoading(true)
    setProfileError(null)
    try {
      const data = await authService.getCurrentUser()
      setProfile(data)
      setFullName(data.full_name || '')
      setDepartment(data.department || '')
      setPhone(data.phone || '')
      setRollNumber(data.roll_number || '')

      // If student has membership, load group & project details
      if (data.memberships && data.memberships.length > 0) {
        loadStudentResearchInfo(data.memberships[0].project_id)
      }
    } catch (err: any) {
      setProfileError(err?.message || 'Unable to load profile information.')
    } finally {
      setProfileLoading(false)
    }
  }

  const loadStudentResearchInfo = async (projectId: string) => {
    setResearchLoading(true)
    try {
      const [gData, gMembers, pList] = await Promise.all([
        groupService.getMyGroup().catch(() => null),
        groupService.getMyGroupMembers().catch(() => []),
        projectService.getCatalog().catch(() => []),
      ])
      if (gData) setGroupDetails(gData)
      if (gMembers) setGroupMembers(gMembers)
      const matchedProj = (pList as ProjectSummary[]).find((p) => p.id === projectId)
      if (matchedProj) setAssignedProject(matchedProj)
    } catch (err) {
      console.error('Failed to load research information:', err)
    } finally {
      setResearchLoading(false)
    }
  }

  // Load Admin Data when Admin tabs are activated
  useEffect(() => {
    if (!isAdmin) return

    if (activeTab === 'admin-users') {
      loadAdminUsers()
    } else if (activeTab === 'admin-groups') {
      loadAdminGroups()
    } else if (activeTab === 'admin-projects') {
      loadAdminProjects()
    }
  }, [activeTab, isAdmin])

  const loadAdminUsers = async () => {
    setAdminDataLoading(true)
    setAdminError(null)
    try {
      const data = await adminService.getUsers()
      setAdminUsers(data)
    } catch (err: any) {
      setAdminError(err?.message || 'Failed to load user accounts.')
    } finally {
      setAdminDataLoading(false)
    }
  }

  const loadAdminGroups = async () => {
    setAdminDataLoading(true)
    setAdminError(null)
    try {
      const data = await adminService.getGroups()
      setAdminGroups(data)
    } catch (err: any) {
      setAdminError(err?.message || 'Failed to load research groups.')
    } finally {
      setAdminDataLoading(false)
    }
  }

  const loadAdminProjects = async () => {
    setAdminDataLoading(true)
    setAdminError(null)
    try {
      const data = await adminService.getProjects()
      setAdminProjects(data)
    } catch (err: any) {
      setAdminError(err?.message || 'Failed to load project definitions.')
    } finally {
      setAdminDataLoading(false)
    }
  }

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingProfile(true)
    setProfileError(null)
    setProfileSuccess(null)

    try {
      const updated = await authService.updateProfile({
        full_name: fullName.trim(),
        department: department.trim() || undefined,
        phone: phone.trim() || undefined,
        roll_number: rollNumber.trim() || undefined,
      })
      setProfile(updated)
      setProfileSuccess('Profile updated successfully.')
      if (refreshUser) {
        refreshUser()
      }
      setTimeout(() => setProfileSuccess(null), 4000)
    } catch (err: any) {
      setProfileError(err?.message || 'Failed to update profile.')
    } finally {
      setSavingProfile(false)
    }
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError(null)
    setPasswordSuccess(null)

    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters long.')
      return
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('New password and confirmation do not match.')
      return
    }

    if (newPassword === currentPassword) {
      setPasswordError('New password must be different from current password.')
      return
    }

    setPasswordLoading(true)
    try {
      await authService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      })
      setPasswordSuccess('Password changed successfully.')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setTimeout(() => setPasswordSuccess(null), 4000)
    } catch (err: any) {
      setPasswordError(err?.message || 'Failed to change password. Please check your current password.')
    } finally {
      setPasswordLoading(false)
    }
  }

  const handleToggleUserStatus = async (userId: string, currentStatus: boolean) => {
    setAdminError(null)
    setAdminSuccess(null)
    try {
      await adminService.updateUserStatus(userId, !currentStatus)
      setAdminUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, is_active: !currentStatus } : u))
      )
      setAdminSuccess(`User account status updated to ${!currentStatus ? 'Active' : 'Inactive'}.`)
      setTimeout(() => setAdminSuccess(null), 3000)
    } catch (err: any) {
      setAdminError(err?.message || 'Failed to update user status.')
    }
  }

  return (
    <div className="gs-page" id="settings-page">
      {/* Page Header */}
      <div className="gs-page-header">
        <div>
          <div className="gs-page-title">
            <div className="gs-page-title-icon indigo">
              <Shield size={20} />
            </div>
            Settings
          </div>
          <p className="gs-page-subtitle">
            Manage your account credentials, research affiliations, and platform configurations.
          </p>
        </div>
      </div>

      {/* Two-Column Settings Layout */}
      <div className="gs-settings-layout">
        {/* Left Navigation Tabs */}
        <aside className="gs-settings-nav">
          <div className="gs-settings-nav-section">Account</div>
          <button
            type="button"
            className={`gs-settings-nav-item ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            <UserIcon size={16} />
            <span>Profile</span>
          </button>
          <button
            type="button"
            className={`gs-settings-nav-item ${activeTab === 'password' ? 'active' : ''}`}
            onClick={() => setActiveTab('password')}
          >
            <Lock size={16} />
            <span>Change Password</span>
          </button>

          <div className="gs-settings-nav-section">Research</div>
          <button
            type="button"
            className={`gs-settings-nav-item ${activeTab === 'research' ? 'active' : ''}`}
            onClick={() => setActiveTab('research')}
          >
            <FlaskConical size={16} />
            <span>Research Information</span>
          </button>

          {/* Admin Only Tabs */}
          {isAdmin && (
            <>
              <div className="gs-settings-nav-section">Administration</div>
              <button
                type="button"
                className={`gs-settings-nav-item ${activeTab === 'admin-users' ? 'active' : ''}`}
                onClick={() => setActiveTab('admin-users')}
              >
                <Users size={16} />
                <span>Users</span>
              </button>
              <button
                type="button"
                className={`gs-settings-nav-item ${activeTab === 'admin-groups' ? 'active' : ''}`}
                onClick={() => setActiveTab('admin-groups')}
              >
                <Building2 size={16} />
                <span>Research Groups</span>
              </button>
              <button
                type="button"
                className={`gs-settings-nav-item ${activeTab === 'admin-projects' ? 'active' : ''}`}
                onClick={() => setActiveTab('admin-projects')}
              >
                <FolderKanban size={16} />
                <span>Projects</span>
              </button>
            </>
          )}

          <div className="gs-settings-nav-section">System</div>
          <button
            type="button"
            className={`gs-settings-nav-item ${activeTab === 'about' ? 'active' : ''}`}
            onClick={() => setActiveTab('about')}
          >
            <Info size={16} />
            <span>About</span>
          </button>
        </aside>

        {/* Right Content Area */}
        <main className="gs-settings-content">
          {/* ── 1. Profile Section ─────────────────────────────────── */}
          {activeTab === 'profile' && (
            <div className="gs-panel">
              <div className="gs-panel-header">
                <span className="gs-panel-title">Profile Settings</span>
                <span className="gs-badge indigo">
                  {profile?.account_type || authUser?.account_type || 'STUDENT'}
                </span>
              </div>
              <div className="gs-panel-body">
                {profileLoading ? (
                  <div className="gs-loading-placeholder">Loading profile information...</div>
                ) : (
                  <form onSubmit={handleProfileSubmit}>
                    {profileSuccess && (
                      <div className="gs-alert success" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                        <CheckCircle2 size={16} /> {profileSuccess}
                      </div>
                    )}
                    {profileError && (
                      <div className="gs-alert error" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                        <AlertCircle size={16} /> {profileError}
                      </div>
                    )}

                    <div className="gs-form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                      <div className="gs-field">
                        <label className="gs-label">Full Name</label>
                        <input
                          type="text"
                          className="gs-input"
                          value={fullName}
                          onChange={(e) => setFullName(e.target.value)}
                          required
                          placeholder="Your full name"
                        />
                      </div>

                      <div className="gs-field">
                        <label className="gs-label">
                          Email Address <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>(Read-Only)</span>
                        </label>
                        <input
                          type="email"
                          className="gs-input"
                          value={profile?.email || authUser?.email || ''}
                          disabled
                          readOnly
                          style={{ background: 'var(--color-bg)', cursor: 'not-allowed' }}
                        />
                      </div>

                      <div className="gs-field">
                        <label className="gs-label">
                          Account Type <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>(Read-Only)</span>
                        </label>
                        <input
                          type="text"
                          className="gs-input"
                          value={profile?.account_type || authUser?.account_type || 'STUDENT'}
                          disabled
                          readOnly
                          style={{ background: 'var(--color-bg)', cursor: 'not-allowed', fontWeight: 600 }}
                        />
                      </div>

                      <div className="gs-field">
                        <label className="gs-label">
                          Account Status <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>(Read-Only)</span>
                        </label>
                        <input
                          type="text"
                          className="gs-input"
                          value={profile?.is_active ? 'Active' : 'Inactive'}
                          disabled
                          readOnly
                          style={{ background: 'var(--color-bg)', cursor: 'not-allowed' }}
                        />
                      </div>

                      <div className="gs-field">
                        <label className="gs-label">Academic Department</label>
                        <input
                          type="text"
                          className="gs-input"
                          value={department}
                          onChange={(e) => setDepartment(e.target.value)}
                          placeholder="e.g. Chemical Engineering, Materials Science"
                        />
                      </div>

                      <div className="gs-field">
                        <label className="gs-label">Contact Phone</label>
                        <input
                          type="tel"
                          className="gs-input"
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                          placeholder="+91 9876543210"
                        />
                      </div>

                      <div className="gs-field">
                        <label className="gs-label">Roll / Institutional Number</label>
                        <input
                          type="text"
                          className="gs-input"
                          value={rollNumber}
                          onChange={(e) => setRollNumber(e.target.value)}
                          placeholder="e.g. ME2024-88"
                        />
                      </div>

                      <div className="gs-field">
                        <label className="gs-label">Member Since</label>
                        <input
                          type="text"
                          className="gs-input"
                          value={profile?.created_at ? new Date(profile.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }) : '—'}
                          disabled
                          readOnly
                          style={{ background: 'var(--color-bg)', cursor: 'not-allowed' }}
                        />
                      </div>
                    </div>

                    <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end' }}>
                      <button
                        type="submit"
                        disabled={savingProfile}
                        className="gs-btn gs-btn-teal"
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                      >
                        <Save size={16} />
                        {savingProfile ? 'Saving Changes...' : 'Save Profile Changes'}
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          )}

          {/* ── 2. Change Password Section ─────────────────────────── */}
          {activeTab === 'password' && (
            <div className="gs-panel">
              <div className="gs-panel-header">
                <span className="gs-panel-title">Change Account Password</span>
              </div>
              <div className="gs-panel-body" style={{ maxWidth: 520 }}>
                {passwordSuccess && (
                  <div className="gs-alert success" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <CheckCircle2 size={16} /> {passwordSuccess}
                  </div>
                )}
                {passwordError && (
                  <div className="gs-alert error" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <AlertCircle size={16} /> {passwordError}
                  </div>
                )}

                <form onSubmit={handlePasswordSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div className="gs-field">
                    <label className="gs-label">Current Password</label>
                    <input
                      type="password"
                      className="gs-input"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      required
                      placeholder="Enter your current password"
                      autoComplete="current-password"
                    />
                  </div>

                  <div className="gs-field">
                    <label className="gs-label">New Password (Min 8 Characters)</label>
                    <input
                      type="password"
                      className="gs-input"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                      minLength={8}
                      placeholder="Enter new password"
                      autoComplete="new-password"
                    />
                  </div>

                  <div className="gs-field">
                    <label className="gs-label">Confirm New Password</label>
                    <input
                      type="password"
                      className="gs-input"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      minLength={8}
                      placeholder="Re-enter new password"
                      autoComplete="new-password"
                    />
                  </div>

                  <div style={{ marginTop: 8, display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                      type="submit"
                      disabled={passwordLoading}
                      className="gs-btn gs-btn-indigo"
                      style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                    >
                      <KeyRound size={16} />
                      {passwordLoading ? 'Updating Password...' : 'Change Password'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* ── 3. Research Information Section ────────────────────── */}
          {activeTab === 'research' && (
            <div className="gs-panel">
              <div className="gs-panel-header">
                <span className="gs-panel-title">Research Affiliation &amp; Scope</span>
                <span className="gs-badge green">
                  {isAdmin ? 'SYSTEM-WIDE' : 'GROUP-SCOPED'}
                </span>
              </div>
              <div className="gs-panel-body">
                {isAdmin ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <div style={{ padding: 16, background: 'var(--color-bg)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--color-border)' }}>
                      <h4 style={{ margin: '0 0 6px 0', fontSize: '1rem', color: 'var(--color-text)' }}>
                        Administrator Global Scope
                      </h4>
                      <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                        Your administrator account has system-wide access to all synthesis projects (P1 through P8),
                        research groups, characterization logs, and machine learning pipelines.
                      </p>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
                      <div className="gs-card" style={{ padding: 16 }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                          Account Scope
                        </div>
                        <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: 4 }}>System Administrator</div>
                      </div>
                      <div className="gs-card" style={{ padding: 16 }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                          Project Catalog
                        </div>
                        <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: 4 }}>All Active (P1–P8)</div>
                      </div>
                    </div>
                  </div>
                ) : researchLoading ? (
                  <div className="gs-loading-placeholder">Loading research information...</div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                    {/* Assigned Project Card */}
                    <div className="gs-card" style={{ padding: 20 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                        <span className="gs-badge teal">
                          Assigned Project: {profile?.memberships?.[0]?.project_code || 'None'}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                          Immutable Research Assignment
                        </span>
                      </div>
                      <h3 style={{ margin: '0 0 6px 0', fontSize: '1.125rem', color: 'var(--color-text)' }}>
                        {assignedProject?.name || profile?.memberships?.[0]?.project_name || 'No project assigned.'}
                      </h3>
                      {assignedProject?.description && (
                        <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                          {assignedProject.description}
                        </p>
                      )}
                      {assignedProject && (
                        <div style={{ display: 'flex', gap: 12, marginTop: 14, flexWrap: 'wrap' }}>
                          <span className="gs-chip teal" style={{ background: '#d1fae5', color: '#065f46' }}>
                            Material: {assignedProject.material}
                          </span>
                          <span className="gs-chip blue" style={{ background: '#dbeafe', color: '#1e40af' }}>
                            Method: {assignedProject.synthesis_method}
                          </span>
                          {assignedProject.extract && (
                            <span className="gs-chip emerald" style={{ background: '#ecfdf5', color: '#065f46' }}>
                              Extract: {assignedProject.extract}
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Research Group Details */}
                    <div className="gs-card" style={{ padding: 20 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                        <span className="gs-badge indigo">
                          Research Group: {groupDetails?.group_name || profile?.memberships?.[0]?.group_name || 'Unassigned'}
                        </span>
                        <span className="gs-badge green">
                          Role: {profile?.memberships?.[0]?.is_leader ? 'Group Leader' : 'Group Member'}
                        </span>
                      </div>

                      {groupMembers.length > 0 ? (
                        <div>
                          <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 8, textTransform: 'uppercase' }}>
                            Enrolled Group Members ({groupMembers.length})
                          </div>
                          <div className="gs-table-wrap">
                            <table className="gs-table">
                              <thead>
                                <tr>
                                  <th>Member Name</th>
                                  <th>Email</th>
                                  <th>Role</th>
                                  <th>Status</th>
                                </tr>
                              </thead>
                              <tbody>
                                {groupMembers.map((m) => (
                                  <tr key={m.user_id}>
                                    <td>
                                      <strong>{m.full_name || m.user_id.slice(0, 8)}</strong>
                                    </td>
                                    <td>{m.email || '—'}</td>
                                    <td>
                                      <span className={`gs-badge ${m.is_leader ? 'indigo' : 'slate'}`}>
                                        {m.is_leader ? 'Leader' : 'Member'}
                                      </span>
                                    </td>
                                    <td>
                                      <span className="gs-badge green">{m.status}</span>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      ) : (
                        <div className="gs-empty-placeholder" style={{ padding: 20 }}>
                          No additional group members enrolled yet.
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── 4. Admin Users Management Section ──────────────────── */}
          {isAdmin && activeTab === 'admin-users' && (
            <div className="gs-panel">
              <div className="gs-panel-header">
                <span className="gs-panel-title">User Account Management ({adminUsers.length})</span>
                <button
                  type="button"
                  onClick={loadAdminUsers}
                  className="gs-btn gs-btn-outline"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 12px' }}
                >
                  <RefreshCw size={14} /> Refresh
                </button>
              </div>
              <div className="gs-panel-body">
                {adminSuccess && (
                  <div className="gs-alert success" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <CheckCircle2 size={16} /> {adminSuccess}
                  </div>
                )}
                {adminError && (
                  <div className="gs-alert error" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <AlertCircle size={16} /> {adminError}
                  </div>
                )}

                {adminDataLoading ? (
                  <div className="gs-loading-placeholder">Loading user accounts...</div>
                ) : (
                  <div className="gs-table-wrap">
                    <table className="gs-table">
                      <thead>
                        <tr>
                          <th>User</th>
                          <th>Email</th>
                          <th>Account Type</th>
                          <th>Status</th>
                          <th>Created</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminUsers.map((u) => (
                          <tr key={u.id}>
                            <td>
                              <strong>{u.full_name}</strong>
                              {u.department && (
                                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                                  {u.department}
                                </div>
                              )}
                            </td>
                            <td>{u.email}</td>
                            <td>
                              <span className={`gs-badge ${u.account_type === 'ADMIN' ? 'indigo' : 'teal'}`}>
                                {u.account_type || 'STUDENT'}
                              </span>
                            </td>
                            <td>
                              <span className={`gs-badge ${u.is_active ? 'green' : 'rose'}`}>
                                {u.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td>
                              {new Date(u.created_at).toLocaleDateString()}
                            </td>
                            <td>
                              {u.account_type !== 'ADMIN' ? (
                                <button
                                  type="button"
                                  onClick={() => handleToggleUserStatus(u.id, u.is_active)}
                                  className={`gs-btn ${u.is_active ? 'gs-btn-outline' : 'gs-btn-teal'}`}
                                  style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                                >
                                  {u.is_active ? 'Deactivate' : 'Activate'}
                                </button>
                              ) : (
                                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                                  Protected Admin
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── 5. Admin Research Groups Management Section ────────── */}
          {isAdmin && activeTab === 'admin-groups' && (
            <div className="gs-panel">
              <div className="gs-panel-header">
                <span className="gs-panel-title">Research Groups ({adminGroups.length})</span>
                <button
                  type="button"
                  onClick={loadAdminGroups}
                  className="gs-btn gs-btn-outline"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 12px' }}
                >
                  <RefreshCw size={14} /> Refresh
                </button>
              </div>
              <div className="gs-panel-body">
                {adminDataLoading ? (
                  <div className="gs-loading-placeholder">Loading research groups...</div>
                ) : (
                  <div className="gs-table-wrap">
                    <table className="gs-table">
                      <thead>
                        <tr>
                          <th>Group Name</th>
                          <th>Leader</th>
                          <th>Project</th>
                          <th>Members</th>
                          <th>Created</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminGroups.map((g) => (
                          <tr key={g.group_id}>
                            <td>
                              <strong>{g.group_name}</strong>
                              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                                {g.group_id.slice(0, 8)}...
                              </div>
                            </td>
                            <td>{g.leader_name || '—'}</td>
                            <td>
                              <span className="gs-badge teal">{g.project_code}</span>
                            </td>
                            <td>{g.member_count}</td>
                            <td>{new Date(g.created_at).toLocaleDateString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── 6. Admin Project Management Section ────────────────── */}
          {isAdmin && activeTab === 'admin-projects' && (
            <div className="gs-panel">
              <div className="gs-panel-header">
                <span className="gs-panel-title">Synthesis Projects Catalog (P1–P8)</span>
                <button
                  type="button"
                  onClick={loadAdminProjects}
                  className="gs-btn gs-btn-outline"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 12px' }}
                >
                  <RefreshCw size={14} /> Refresh
                </button>
              </div>
              <div className="gs-panel-body">
                {adminDataLoading ? (
                  <div className="gs-loading-placeholder">Loading projects...</div>
                ) : (
                  <div className="gs-table-wrap">
                    <table className="gs-table">
                      <thead>
                        <tr>
                          <th>Code</th>
                          <th>Project Name</th>
                          <th>Material</th>
                          <th>Solvent</th>
                          <th>Extract</th>
                          <th>Method</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminProjects.map((p) => (
                          <tr key={p.id}>
                            <td>
                              <strong style={{ color: '#0f766e' }}>{p.project_code}</strong>
                            </td>
                            <td>{p.name}</td>
                            <td>{p.material}</td>
                            <td>{p.solvent || '—'}</td>
                            <td>{p.extract || '—'}</td>
                            <td>{p.synthesis_method}</td>
                            <td>
                              <span className="gs-badge green">{p.status}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── 7. About Section ───────────────────────────────────── */}
          {activeTab === 'about' && (
            <div className="gs-panel">
              <div className="gs-panel-header">
                <span className="gs-panel-title">About GreenSynth Analytics</span>
                <span className="gs-badge teal">v0.6.0</span>
              </div>
              <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                <div style={{ padding: 18, background: 'var(--color-bg)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--color-border)' }}>
                  <h3 style={{ margin: '0 0 8px 0', fontSize: '1.125rem', color: 'var(--color-text)' }}>
                    GreenSynth Analytics Platform
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                    A Data-Driven Research and Scientific Analytics Platform for the Green Synthesis of Semiconductor Materials.
                    Facilitates multi-project isolation, automated characterization analysis (XRD, UV-Vis, FTIR, SEM, Electrical),
                    closed-loop machine learning predictions, and evidence-based synthesis optimization.
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
                  <div className="gs-card" style={{ padding: 16 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                      Frontend Engine
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 4 }}>React 18 + TypeScript + Vite</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
                      Vanilla CSS Design Tokens
                    </div>
                  </div>

                  <div className="gs-card" style={{ padding: 16 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                      Backend API
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 4 }}>FastAPI + Python 3.12</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
                      Asynchronous REST Services
                    </div>
                  </div>

                  <div className="gs-card" style={{ padding: 16 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                      Scientific Core
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 4 }}>NumPy, SciPy &amp; Scikit-Learn</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
                      Crystallographic &amp; Band Gap Physics
                    </div>
                  </div>

                  <div className="gs-card" style={{ padding: 16 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                      Security Architecture
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 4 }}>JWT Bearer &amp; PBKDF2 Hashing</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
                      Role-Based Multi-Tenant Isolation
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
