/**
 * GreenSynth Analytics — Research Group Registration Wizard
 *
 * 4-Step Registration Workflow:
 *   1. Group Leader Account
 *   2. Research Group & Synthesis Project Selection
 *   3. Member Invitations (3 remaining group members)
 *   4. Review & Confirmation
 *   5. Success & Invitation Status Summary
 */

import React, { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Users,
  ShieldCheck,
  FlaskConical,
  Mail,
  UserCheck,
  Send,
  Building2,
  Phone,
  Hash,
  Lock,
  Layers,
} from 'lucide-react'
import { projectService } from '@/services/projectService'
import { groupService } from '@/services/groupService'
import { useAuth } from '@/context/AuthContext'
import type {
  GroupRegistrationPayload,
  GroupRegistrationResponse,
  ProjectSummary,
} from '@/types'

export default function Register() {
  const navigate = useNavigate()
  const { setAuthSession } = useAuth()
  const [step, setStep] = useState<number>(1)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [projectsLoading, setProjectsLoading] = useState<boolean>(true)
  const [projectsError, setProjectsError] = useState<string | null>(null)
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [registrationResult, setRegistrationResult] = useState<GroupRegistrationResponse | null>(null)

  // ── Form State ──────────────────────────────────────────────
  const [formData, setFormData] = useState<GroupRegistrationPayload>({
    leader: {
      full_name: '',
      department: '',
      phone: '',
      roll_number: '',
      email: '',
      password: '',
      confirm_password: '',
    },
    group: {
      name: '',
      project_id: '',
    },
    members: [
      { full_name: '', department: '', phone: '', roll_number: '', email: '' },
      { full_name: '', department: '', phone: '', roll_number: '', email: '' },
      { full_name: '', department: '', phone: '', roll_number: '', email: '' },
    ],
  })

  // Load available projects on mount
  useEffect(() => {
    async function loadProjects() {
      setProjectsLoading(true)
      setProjectsError(null)
      try {
        const data = await projectService.getCatalog()
        setProjects(data)
        if (data.length > 0 && !formData.group.project_id) {
          setFormData((prev) => ({
            ...prev,
            group: { ...prev.group, project_id: data[0].id },
          }))
        }
      } catch (err: any) {
        console.error('Failed to load project catalog', err)
        setProjectsError('Unable to load synthesis projects. Please check connection to the project service.')
      } finally {
        setProjectsLoading(false)
      }
    }
    loadProjects()
  }, [])

  // ── Form Input Handlers ─────────────────────────────────────
  const updateLeader = (field: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      leader: { ...prev.leader, [field]: value },
    }))
    setError(null)
  }

  const updateGroup = (field: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      group: { ...prev.group, [field]: value },
    }))
    setError(null)
  }

  const updateMember = (index: number, field: string, value: string) => {
    setFormData((prev) => {
      const updatedMembers = [...prev.members]
      updatedMembers[index] = { ...updatedMembers[index], [field]: value }
      return { ...prev, members: updatedMembers }
    })
    setError(null)
  }

  // ── Step Validation ─────────────────────────────────────────
  const validateStep1 = (): boolean => {
    const { full_name, department, phone, roll_number, email, password, confirm_password } = formData.leader
    if (!full_name.trim() || !department.trim() || !phone.trim() || !roll_number.trim() || !email.trim()) {
      setError('Please fill in all leader identification details.')
      return false
    }
    if (!email.includes('@')) {
      setError('Please enter a valid email address.')
      return false
    }
    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters in length.')
      return false
    }
    if (password !== confirm_password) {
      setError('Passwords do not match.')
      return false
    }
    return true
  }

  const validateStep2 = (): boolean => {
    if (!formData.group.name.trim()) {
      setError('Please provide a research group name.')
      return false
    }
    if (!formData.group.project_id) {
      setError('Please select a synthesis research project.')
      return false
    }
    return true
  }

  const validateStep3 = (): boolean => {
    const leaderEmail = formData.leader.email.trim().toLowerCase()
    const leaderRoll = formData.leader.roll_number.trim().toUpperCase()
    const emails: string[] = [leaderEmail]
    const rolls: string[] = [leaderRoll]

    for (let i = 0; i < formData.members.length; i++) {
      const m = formData.members[i]
      if (!m.full_name.trim() || !m.department.trim() || !m.phone.trim() || !m.roll_number.trim() || !m.email.trim()) {
        setError(`Please fill in all details for Member ${i + 1}.`)
        return false
      }
      if (!m.email.includes('@')) {
        setError(`Member ${i + 1} email address is invalid.`)
        return false
      }

      const mEmail = m.email.trim().toLowerCase()
      const mRoll = m.roll_number.trim().toUpperCase()

      if (emails.includes(mEmail)) {
        setError(`Duplicate email detected for Member ${i + 1} (${mEmail}). All emails must be unique.`)
        return false
      }
      if (rolls.includes(mRoll)) {
        setError(`Duplicate roll number detected for Member ${i + 1} (${mRoll}). All roll numbers must be unique.`)
        return false
      }

      emails.push(mEmail)
      rolls.push(mRoll)
    }

    return true
  }

  const handleNext = () => {
    setError(null)
    if (step === 1 && !validateStep1()) return
    if (step === 2 && !validateStep2()) return
    if (step === 3 && !validateStep3()) return
    setStep((prev) => prev + 1)
  }

  const handleBack = () => {
    setError(null)
    setStep((prev) => Math.max(1, prev - 1))
  }

  // ── Form Submission ─────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateStep1() || !validateStep2() || !validateStep3()) return

    setLoading(true)
    setError(null)

    try {
      const result = await groupService.registerGroupWithMembers(formData)
      if (result.access_token) {
        await setAuthSession(result.access_token)
      }
      setRegistrationResult(result)
      setStep(5) // Success step
    } catch (err: any) {
      setError(err.message || 'Failed to complete group registration. Please verify your details.')
    } finally {
      setLoading(false)
    }
  }

  const selectedProject = projects.find((p) => p.id === formData.group.project_id)

  return (
    <div className="container" style={{ maxWidth: '900px', margin: '40px auto', padding: '0 16px' }}>
      {/* Header Banner */}
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 14px', background: 'rgba(15, 118, 110, 0.1)', borderRadius: '20px', color: '#0f766e', fontSize: '13px', fontWeight: 600, marginBottom: '12px' }}>
          <Users size={16} /> Research Group Registration
        </div>
        <h1 style={{ fontSize: '28px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>
          Register Your Semiconductor Research Group
        </h1>
        <p style={{ color: '#64748b', fontSize: '14px', maxWidth: '600px', margin: '0 auto' }}>
          Establish your team of 4 students (1 Group Leader + 3 Members) and lock in your assigned green synthesis project.
        </p>
      </div>

      {/* Wizard Progress Indicator (Steps 1 - 4) */}
      {step <= 4 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px', position: 'relative' }}>
          {[
            { num: 1, title: 'Leader Account' },
            { num: 2, title: 'Group & Project' },
            { num: 3, title: 'Member Invites' },
            { num: 4, title: 'Review & Submit' },
          ].map((s) => (
            <div key={s.num} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 2 }}>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '14px',
                  background: step >= s.num ? '#0f766e' : '#e2e8f0',
                  color: step >= s.num ? '#ffffff' : '#64748b',
                  transition: 'all 0.2s ease',
                  boxShadow: step === s.num ? '0 0 0 4px rgba(15, 118, 110, 0.15)' : 'none',
                }}
              >
                {step > s.num ? <CheckCircle2 size={18} /> : s.num}
              </div>
              <span style={{ fontSize: '12px', fontWeight: step === s.num ? 600 : 500, color: step >= s.num ? '#0f172a' : '#94a3b8', marginTop: '6px' }}>
                {s.title}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            color: '#991b1b',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            marginBottom: '24px',
          }}
        >
          <AlertCircle size={18} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      {/* Main Form Container */}
      <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '32px', boxShadow: '0 4px 16px rgba(0,0,0,0.03)' }}>
        {/* ── STEP 1: LEADER ACCOUNT ────────────────────────── */}
        {step === 1 && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
              <ShieldCheck size={20} color="#0f766e" />
              <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#0f172a', margin: 0 }}>
                Step 1: Group Leader Information
              </h2>
            </div>
            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '24px' }}>
              As the Group Leader, you will manage project workflows and group member invitations.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px', marginBottom: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#334155', marginBottom: '6px' }}>
                  Full Name *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Atharva Kulkarni"
                  value={formData.leader.full_name}
                  onChange={(e) => updateLeader('full_name', e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#334155', marginBottom: '6px' }}>
                  Department *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Chemical Engineering"
                  value={formData.leader.department}
                  onChange={(e) => updateLeader('department', e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#334155', marginBottom: '6px' }}>
                  Departmental Roll Number *
                </label>
                <input
                  type="text"
                  placeholder="e.g. CHEM-2026-001"
                  value={formData.leader.roll_number}
                  onChange={(e) => updateLeader('roll_number', e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#334155', marginBottom: '6px' }}>
                  Contact Phone Number *
                </label>
                <input
                  type="tel"
                  placeholder="e.g. 9876543210"
                  value={formData.leader.phone}
                  onChange={(e) => updateLeader('phone', e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                />
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#334155', marginBottom: '6px' }}>
                Email Address (Login Identifier) *
              </label>
              <input
                type="email"
                placeholder="leader@greensynth.edu"
                value={formData.leader.email}
                onChange={(e) => updateLeader('email', e.target.value)}
                style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#334155', marginBottom: '6px' }}>
                  Account Password (min 8 chars) *
                </label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={formData.leader.password}
                  onChange={(e) => updateLeader('password', e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#334155', marginBottom: '6px' }}>
                  Confirm Password *
                </label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={formData.leader.confirm_password}
                  onChange={(e) => updateLeader('confirm_password', e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── STEP 2: GROUP & PROJECT SELECTION ─────────────── */}
        {step === 2 && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
              <FlaskConical size={20} color="#0f766e" />
              <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#0f172a', margin: 0 }}>
                Step 2: Research Group Name & Project Binding
              </h2>
            </div>
            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '24px' }}>
              Select exactly one semiconductor synthesis project for your research group. All group research data is strictly isolated to this project.
            </p>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#334155', marginBottom: '6px' }}>
                Research Group Name *
              </label>
              <input
                type="text"
                placeholder="e.g. Green Innovators Unit A"
                value={formData.group.name}
                onChange={(e) => updateGroup('name', e.target.value)}
                style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
              />
            </div>

            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#0f172a', marginBottom: '12px' }}>
              Select Synthesis Project (P1 – P8) *
            </label>

            {projectsLoading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '32px', color: '#64748b', fontSize: '14px', gap: '8px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <Layers size={18} className="animate-spin" />
                <span>Loading available synthesis projects...</span>
              </div>
            ) : projectsError ? (
              <div style={{ padding: '14px 16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <AlertCircle size={18} style={{ flexShrink: 0 }} />
                <span>{projectsError}</span>
              </div>
            ) : projects.length === 0 ? (
              <div style={{ padding: '20px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', color: '#64748b', fontSize: '14px', textAlign: 'center' }}>
                No active synthesis projects currently available in catalog.
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
                {projects.map((proj) => {
                  const isSelected = formData.group.project_id === proj.id
                  return (
                    <div
                      key={proj.id}
                      onClick={() => updateGroup('project_id', proj.id)}
                      style={{
                        border: isSelected ? '2px solid #0f766e' : '1px solid #e2e8f0',
                        borderRadius: '8px',
                        padding: '16px',
                        cursor: 'pointer',
                        background: isSelected ? 'rgba(15, 118, 110, 0.04)' : '#ffffff',
                        transition: 'all 0.15s ease',
                        position: 'relative',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontWeight: 700, fontSize: '14px', color: isSelected ? '#0f766e' : '#0f172a' }}>
                          {proj.project_code}
                        </span>
                        {isSelected && <CheckCircle2 size={18} color="#0f766e" />}
                      </div>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>
                        {proj.name}
                      </div>
                      <div style={{ fontSize: '12px', color: '#64748b', lineHeight: 1.4 }}>
                        <div>Method: <strong>{proj.synthesis_method}</strong></div>
                        <div>Material: <strong>{proj.material}</strong> {proj.solvent ? `• ${proj.solvent}` : ''}</div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* ── STEP 3: MEMBER INVITATIONS ─────────────────────── */}
        {step === 3 && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
              <Mail size={20} color="#0f766e" />
              <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#0f172a', margin: 0 }}>
                Step 3: Enter Remaining 3 Member Details
              </h2>
            </div>
            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '24px' }}>
              Enter the student details for the remaining 3 group members. They will receive an email invitation to accept and set their own passwords.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {formData.members.map((member, idx) => (
                <div
                  key={idx}
                  style={{
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '20px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                    <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: '#0f766e', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 700 }}>
                      {idx + 2}
                    </div>
                    <span style={{ fontWeight: 600, fontSize: '14px', color: '#0f172a' }}>
                      Member {idx + 1} Information
                    </span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#475569', marginBottom: '4px' }}>
                        Full Name *
                      </label>
                      <input
                        type="text"
                        placeholder="Student Full Name"
                        value={member.full_name}
                        onChange={(e) => updateMember(idx, 'full_name', e.target.value)}
                        style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#475569', marginBottom: '4px' }}>
                        Department *
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. CSE / ENTC"
                        value={member.department}
                        onChange={(e) => updateMember(idx, 'department', e.target.value)}
                        style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#475569', marginBottom: '4px' }}>
                        Roll Number *
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. ME-2026-002"
                        value={member.roll_number}
                        onChange={(e) => updateMember(idx, 'roll_number', e.target.value)}
                        style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#475569', marginBottom: '4px' }}>
                        Phone Number *
                      </label>
                      <input
                        type="tel"
                        placeholder="e.g. 9876543211"
                        value={member.phone}
                        onChange={(e) => updateMember(idx, 'phone', e.target.value)}
                        style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                      />
                    </div>

                    <div style={{ gridColumn: '1 / -1' }}>
                      <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, color: '#475569', marginBottom: '4px' }}>
                        Email Address (Invitation Recipient) *
                      </label>
                      <input
                        type="email"
                        placeholder="member@greensynth.edu"
                        value={member.email}
                        onChange={(e) => updateMember(idx, 'email', e.target.value)}
                        style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── STEP 4: REVIEW & CONFIRMATION ─────────────────── */}
        {step === 4 && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
              <Layers size={20} color="#0f766e" />
              <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#0f172a', margin: 0 }}>
                Step 4: Review Research Group Registration
              </h2>
            </div>
            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '24px' }}>
              Please verify all group details. Once registered, your research group will be bound to this project.
            </p>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px', marginBottom: '20px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Group Name</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', marginTop: '2px' }}>{formData.group.name}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Assigned Project</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#0f766e', marginTop: '2px' }}>
                    {selectedProject?.project_code} — {selectedProject?.name}
                  </div>
                </div>
              </div>

              <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '14px', marginBottom: '14px' }}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#0f172a', marginBottom: '8px' }}>
                  Group Leader (1)
                </div>
                <div style={{ fontSize: '13px', color: '#334155' }}>
                  <strong>{formData.leader.full_name}</strong> ({formData.leader.department}) • Roll: {formData.leader.roll_number} • {formData.leader.email}
                </div>
              </div>

              <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '14px' }}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#0f172a', marginBottom: '8px' }}>
                  Invited Members (3)
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {formData.members.map((m, i) => (
                    <div key={i} style={{ fontSize: '13px', color: '#334155' }}>
                      {i + 1}. <strong>{m.full_name}</strong> ({m.department}) • Roll: {m.roll_number} • {m.email}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '14px 16px', color: '#166534', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ShieldCheck size={18} style={{ flexShrink: 0 }} />
              <span>
                <strong>Project Data Isolation:</strong> Your research data (experiments, samples, spectra, ML predictions, and DOE models) will remain private to this group.
              </span>
            </div>
          </div>
        )}

        {/* ── STEP 5: SUCCESS & INVITATION SUMMARY ───────────── */}
        {step === 5 && registrationResult && (
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: '#dcfce7', color: '#16a34a', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px auto' }}>
              <CheckCircle2 size={32} />
            </div>
            <h2 style={{ fontSize: '22px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>
              Research Group Successfully Created!
            </h2>
            <p style={{ color: '#64748b', fontSize: '14px', maxWidth: '500px', margin: '0 auto 28px auto' }}>
              Group <strong>{registrationResult.group_name}</strong> is now bound to Project <strong>{registrationResult.project_code}</strong>.
            </p>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px', textAlign: 'left', marginBottom: '28px' }}>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a', marginBottom: '12px' }}>
                Member Onboarding Status:
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {registrationResult.invitations.map((inv) => (
                  <div key={inv.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '6px' }}>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: '#0f172a' }}>{inv.full_name}</div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>{inv.email} • Roll: {inv.roll_number}</div>
                    </div>
                    <span style={{ fontSize: '12px', fontWeight: 600, padding: '4px 10px', borderRadius: '12px', background: '#fef3c7', color: '#92400e' }}>
                      {inv.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => navigate('/')}
              style={{
                background: '#0f766e',
                color: '#ffffff',
                border: 'none',
                padding: '12px 28px',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Enter GreenSynth Platform
            </button>
          </div>
        )}

        {/* Wizard Controls */}
        {step <= 4 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '32px', borderTop: '1px solid #e2e8f0', paddingTop: '20px' }}>
            {step > 1 ? (
              <button
                type="button"
                onClick={handleBack}
                style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#ffffff', border: '1px solid #cbd5e1', color: '#334155', padding: '10px 18px', borderRadius: '6px', fontSize: '14px', fontWeight: 500, cursor: 'pointer' }}
              >
                <ArrowLeft size={16} /> Back
              </button>
            ) : (
              <Link to="/login" style={{ fontSize: '13px', color: '#0f766e', textDecoration: 'none', fontWeight: 500 }}>
                Already registered? Sign In
              </Link>
            )}

            {step < 4 ? (
              <button
                type="button"
                onClick={handleNext}
                style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#0f766e', color: '#ffffff', border: 'none', padding: '10px 22px', borderRadius: '6px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}
              >
                Continue <ArrowRight size={16} />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#0f766e', color: '#ffffff', border: 'none', padding: '10px 24px', borderRadius: '6px', fontSize: '14px', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}
              >
                {loading ? 'Creating Group...' : 'Create Research Group'} <Send size={16} />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
