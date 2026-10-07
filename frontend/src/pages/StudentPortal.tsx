/**
 * GreenSynth Analytics - Student Research Portal
 *
 * Displays the student's assigned project, research group, and
 * project-scoped dashboard stats fetched from /api/v1/student/*.
 * Replaces the plain redirect that previously existed at /student.
 */

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  User, Users, FolderKanban, FlaskConical, TestTube2,
  AlertCircle, RefreshCw, BookOpen, CheckCircle2, Clock, XCircle,
} from 'lucide-react'
import { studentService, type StudentProject, type StudentGroup, type StudentDashboardStats } from '@/services/studentService'
import { useAuth } from '@/context/AuthContext'

export default function StudentPortal() {
  const { user } = useAuth()
  const [project, setProject] = useState<StudentProject | null>(null)
  const [group, setGroup] = useState<StudentGroup | null>(null)
  const [stats, setStats] = useState<StudentDashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [projRes, groupRes, statsRes] = await Promise.all([
        studentService.getProject(),
        studentService.getGroup(),
        studentService.getDashboardStats(),
      ])
      setProject(projRes.data)
      setGroup(groupRes.data)
      setStats(statsRes)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load student portal data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const statusColor: Record<string, { bg: string; color: string }> = {
    COMPLETED:   { bg: '#dcfce7', color: '#16a34a' },
    IN_PROGRESS: { bg: '#dbeafe', color: '#1d4ed8' },
    PLANNED:     { bg: '#fef9c3', color: '#a16207' },
    FAILED:      { bg: '#fee2e2', color: '#dc2626' },
    ARCHIVED:    { bg: '#f1f5f9', color: '#64748b' },
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc', padding: '24px 32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BookOpen size={22} color="#0f766e" />
            Student Research Portal
          </h1>
          <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
            Welcome back, {user?.full_name || user?.email} — Your project-scoped research overview
          </p>
        </div>
        <button
          onClick={load}
          style={{ background: '#ffffff', border: '1px solid #cbd5e1', color: '#334155', padding: '8px 12px', borderRadius: '6px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '12px 16px', color: '#991b1b', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#64748b', fontSize: '14px' }}>Loading your research context...</div>
      ) : (
        <div style={{ display: 'grid', gap: '20px' }}>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
            {[
              { label: 'Experiments', value: stats?.total_experiments ?? 0, icon: FlaskConical, color: '#ea580c', bg: '#ffedd5' },
              { label: 'Samples', value: stats?.total_samples ?? 0, icon: TestTube2, color: '#059669', bg: '#d1fae5' },
              { label: 'Completed', value: stats?.experiments_by_status?.COMPLETED ?? 0, icon: CheckCircle2, color: '#16a34a', bg: '#dcfce7' },
              { label: 'In Progress', value: stats?.experiments_by_status?.IN_PROGRESS ?? 0, icon: Clock, color: '#1d4ed8', bg: '#dbeafe' },
              { label: 'Failed', value: stats?.experiments_by_status?.FAILED ?? 0, icon: XCircle, color: '#dc2626', bg: '#fee2e2' },
            ].map((s, i) => {
              const Icon = s.icon
              return (
                <div key={i} style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{s.label}</div>
                    <div style={{ fontSize: '26px', fontWeight: 800, color: '#0f172a', marginTop: '4px' }}>{s.value}</div>
                  </div>
                  <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: s.bg, color: s.color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Icon size={20} />
                  </div>
                </div>
              )
            })}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '22px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <FolderKanban size={18} color="#0f766e" />
                <h2 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', margin: 0 }}>Assigned Project</h2>
              </div>
              {project ? (
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 800, background: '#0f766e', color: '#ffffff', padding: '2px 8px', borderRadius: '6px' }}>{project.project_code}</span>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', marginTop: '10px' }}>{project.name}</div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px', lineHeight: 1.5 }}>{project.description || 'No description provided.'}</div>
                  <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid #f1f5f9', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px', color: '#475569' }}>
                    <div>Material: <strong>{project.material}</strong></div>
                    <div>Method: <strong>{project.synthesis_method}</strong></div>
                    {project.extract && <div>Extract: <strong>{project.extract}</strong></div>}
                    {project.solvent && <div>Solvent: <strong>{project.solvent}</strong></div>}
                  </div>
                  <Link to="/experiments" style={{ display: 'inline-block', marginTop: '14px', fontSize: '12px', fontWeight: 600, color: '#0f766e', textDecoration: 'none' }}>
                    View Experiments
                  </Link>
                </div>
              ) : (
                <div style={{ color: '#94a3b8', fontSize: '13px' }}>No project assigned yet.</div>
              )}
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '22px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Users size={18} color="#2563eb" />
                <h2 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', margin: 0 }}>Research Group</h2>
              </div>
              {group ? (
                <div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>{group.group_name}</div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '6px' }}>
                    Group Leader: <strong style={{ color: '#0f172a' }}>{group.leader_name}</strong>
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>{group.leader_email}</div>
                  <div style={{ marginTop: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px', background: '#f1f5f9', borderRadius: '6px', padding: '4px 10px', fontSize: '12px', color: '#475569' }}>
                    <User size={12} />
                    {group.member_count} / {group.max_members} members
                  </div>
                </div>
              ) : (
                <div style={{ color: '#94a3b8', fontSize: '13px' }}>Not assigned to a group yet.</div>
              )}
            </div>
          </div>

          {stats && stats.recent_experiments.length > 0 && (
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '22px' }}>
              <h2 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FlaskConical size={16} color="#ea580c" />
                Recent Experiments
              </h2>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b' }}>
                    <th style={{ padding: '8px 12px', textAlign: 'left' }}>Code</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left' }}>Title</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left' }}>Status</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left' }}>Date</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_experiments.map((exp) => {
                    const sc = statusColor[exp.status] || { bg: '#f1f5f9', color: '#475569' }
                    return (
                      <tr key={exp.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 700, color: '#0f766e' }}>{exp.experiment_code}</td>
                        <td style={{ padding: '10px 12px', color: '#0f172a' }}>{exp.title}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ background: sc.bg, color: sc.color, padding: '2px 8px', borderRadius: '10px', fontSize: '11px', fontWeight: 600 }}>{exp.status}</span>
                        </td>
                        <td style={{ padding: '10px 12px', color: '#64748b' }}>{new Date(exp.created_at).toLocaleDateString()}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <Link to={`/experiments/${exp.id}`} style={{ fontSize: '12px', fontWeight: 600, color: '#0f766e', textDecoration: 'none' }}>View</Link>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
