/**
 * GreenSynth Analytics — Research & Student Dashboard Page
 *
 * Displays real-time, project-scoped statistics for authenticated researchers and students.
 * All values come directly from the database — no fabricated data.
 */

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertCircle,
  BarChart3,
  Dna,
  FlaskConical,
  FolderKanban,
  RotateCw,
  ShieldCheck,
  TestTube2,
  Users,
  Zap,
} from 'lucide-react'
import type { DashboardStats, ExperimentStatus } from '@/types'
import { dashboardService } from '@/services/dashboardService'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { StatusBadge } from '@/components/StatusBadge'
import { PageHeader } from '@/components/PageHeader'
import { useAuth } from '@/context/AuthContext'
import { useProjectContext } from '@/context/ProjectContext'

const STATUS_ORDER: ExperimentStatus[] = [
  'PLANNED',
  'IN_PROGRESS',
  'COMPLETED',
  'FAILED',
]

export default function Dashboard() {
  const { user, isAdmin } = useAuth()
  const {
    project,
    projectCode,
    projectName,
    groupName,
    isGroupLeader,
    hasGroupMembership,
    isLoading: projectLoading,
  } = useProjectContext()

  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await dashboardService.getStats()
      setStats(data)
    } catch (err: unknown) {
      setError(
        (err as { message?: string })?.message ??
          'Failed to load dashboard statistics.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  if (loading || projectLoading) {
    return <LoadingSpinner message="Loading research dashboard…" />
  }

  // ── Handling Student without active group membership ──────────────────────
  if (user && !isAdmin && !hasGroupMembership && !projectCode) {
    return (
      <div style={{ maxWidth: '640px', margin: '60px auto', padding: '0 16px', textAlign: 'center' }}>
        <div className="card" style={{ padding: '36px 28px', borderRadius: '12px', boxShadow: '0 4px 16px rgba(0,0,0,0.05)' }}>
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: '50%',
              background: '#fef3c7',
              color: '#d97706',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto',
            }}
          >
            <AlertCircle size={30} />
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1e293b', marginBottom: '8px' }}>
            Welcome to GreenSynth
          </h2>
          <p style={{ color: '#475569', fontSize: '0.9375rem', lineHeight: 1.6, marginBottom: '16px' }}>
            Your account is active, but no active research group or project has been assigned to your account yet.
          </p>
          <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px', fontSize: '0.875rem', color: '#64748b', textAlign: 'left', marginBottom: '20px' }}>
            <div><strong>Authenticated User:</strong> {user?.full_name} ({user?.email})</div>
            <div><strong>Account Type:</strong> {user?.account_type || 'STUDENT'}</div>
            <div><strong>Department:</strong> {user?.department || 'N/A'}</div>
          </div>
          <p style={{ color: '#94a3b8', fontSize: '0.8125rem' }}>
            Please contact your research group leader or system administrator to assign your research scope.
          </p>
        </div>
      </div>
    )
  }

  if (error) return <ErrorMessage error={error} onRetry={fetchStats} />

  const s = stats!

  return (
    <div>
      <PageHeader
        title="Research Dashboard"
        subtitle="Overview of research operations and assigned experimental workspace"
        actions={
          <button className="btn btn-secondary btn-sm" onClick={fetchStats}>
            <RotateCw size={14} style={{ marginRight: 6 }} /> Refresh
          </button>
        }
      />

      {/* ── Assigned Workspace Scope Banner ────────────────── */}
      {projectCode && (
        <div
          style={{
            padding: '16px 20px',
            background: '#f0fdf4',
            border: '1px solid #bbf7d0',
            borderRadius: '10px',
            marginBottom: 'var(--space-6)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
              borderBottom: project ? '1px solid #dcfce7' : 'none',
              paddingBottom: project ? '12px' : 0,
              marginBottom: project ? '12px' : 0,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 36,
                  height: 36,
                  borderRadius: '50%',
                  background: '#dcfce7',
                  color: '#16a34a',
                }}
              >
                <ShieldCheck size={20} />
              </div>
              <div>
                <div
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    color: '#166534',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  Authorized Research Scope
                </div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: '#1e3a5f' }}>
                  {projectCode} — {projectName || projectCode}
                </div>
              </div>
            </div>
            <div style={{ textAlign: 'right', fontSize: '0.8125rem', color: '#475569' }}>
              <div>
                Group: <strong style={{ color: '#0f766e' }}>{groupName || 'Assigned Group'}</strong>
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                Role: {isGroupLeader ? 'Group Leader' : 'Researcher'}
              </div>
            </div>
          </div>

          {/* Project Synthesis Identity Breakdown */}
          {project && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '10px',
                fontSize: '0.8125rem',
                color: '#166534',
              }}
            >
              <div>Material: <strong>{project.material || 'CuO'}</strong></div>
              <div>Biological Extract: <strong>{project.extract || 'Mulberry Extract'}</strong></div>
              <div>Solvent: <strong>{project.solvent || 'Ethanol'}</strong></div>
              <div>Synthesis Method: <strong>{project.synthesis_method || 'Spray Pyrolysis'}</strong></div>
            </div>
          )}
        </div>
      )}

      {/* ── Summary cards ────────────────────────────────── */}
      <div
        className="stat-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--space-5)',
          marginBottom: 'var(--space-8)',
        }}
      >
        <div className="stat-card">
          <div className="stat-icon blue"><FolderKanban size={24} /></div>
          <div>
            <div className="stat-value">{s.total_projects}</div>
            <div className="stat-label">Active Projects</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green"><FlaskConical size={24} /></div>
          <div>
            <div className="stat-value">{s.total_experiments}</div>
            <div className="stat-label">Experiments</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon amber"><TestTube2 size={24} /></div>
          <div>
            <div className="stat-value">{s.total_samples}</div>
            <div className="stat-label">Samples</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple"><BarChart3 size={24} /></div>
          <div>
            <div className="stat-value">
              {s.experiments_by_status['COMPLETED'] ?? 0}
            </div>
            <div className="stat-label">Completed Experiments</div>
          </div>
        </div>
      </div>

      {/* ── Two-column: status breakdown + recent experiments ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 'var(--space-6)' }}>
        {/* Experiment status breakdown */}
        <div className="card">
          <div className="card-header">
            <h2>Experiments by Status</h2>
          </div>
          <div className="card-body">
            {STATUS_ORDER.map((status) => {
              const count = s.experiments_by_status[status] ?? 0
              const total = s.total_experiments || 1
              const pct = Math.round((count / total) * 100)
              return (
                <div key={status} style={{ marginBottom: 'var(--space-4)' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: 'var(--space-1)',
                    }}
                  >
                    <StatusBadge status={status} />
                    <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>
                      {count}
                    </span>
                  </div>
                  <div
                    style={{
                      height: 6,
                      background: 'var(--color-border)',
                      borderRadius: 3,
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${pct}%`,
                        background: statusToColor(status),
                        borderRadius: 3,
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Recent experiments */}
        <div className="card">
          <div className="card-header">
            <h2>Recent Experiments</h2>
            <Link to="/experiments" className="btn btn-sm btn-secondary">
              View all
            </Link>
          </div>
          <div className="table-container">
            {s.recent_experiments.length === 0 ? (
              <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                <p>No experiments recorded for this project yet.</p>
                <Link to="/experiments" className="btn btn-primary btn-sm" style={{ marginTop: 12 }}>
                  Create Experiment
                </Link>
              </div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th>Researcher</th>
                  </tr>
                </thead>
                <tbody>
                  {s.recent_experiments.map((exp) => (
                    <tr key={exp.id}>
                      <td>
                        <Link to={`/experiments/${exp.id}`} className="table-link text-mono">
                          {exp.experiment_code}
                        </Link>
                      </td>
                      <td className="truncate" style={{ maxWidth: 200 }}>{exp.title}</td>
                      <td><StatusBadge status={exp.status} /></td>
                      <td style={{ color: 'var(--color-text-secondary)' }}>
                        {exp.experiment_date
                          ? new Date(exp.experiment_date).toLocaleDateString()
                          : '—'}
                      </td>
                      <td style={{ color: 'var(--color-text-secondary)' }}>
                        {exp.researcher ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      {/* ── Quick links ───────────────────────────────────── */}
      <div style={{ marginTop: 'var(--space-6)' }}>
        <div className="card">
          <div className="card-header">
            <h2>Quick Actions</h2>
          </div>
          <div className="card-body" style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
            <Link to="/projects" className="btn btn-primary">
              Browse Projects
            </Link>
            <Link to="/experiments" className="btn btn-secondary">
              View Experiments
            </Link>
            <Link to="/samples" className="btn btn-secondary">
              View Samples
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

function statusToColor(status: ExperimentStatus): string {
  const map: Record<ExperimentStatus, string> = {
    PLANNED: 'var(--color-info)',
    IN_PROGRESS: 'var(--color-warning)',
    COMPLETED: 'var(--color-success)',
    FAILED: 'var(--color-danger)',
    ARCHIVED: 'var(--color-text-muted)',
  }
  return map[status] ?? 'var(--color-border)'
}
