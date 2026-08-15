/**
 * GreenSynth Analytics — Dashboard Page
 *
 * Displays real-time statistics from the backend.
 * All values come from the database — no fabricated data.
 */

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FolderKanban, FlaskConical, TestTube2, BarChart3, RotateCw } from 'lucide-react'
import type { DashboardStats, ExperimentStatus } from '@/types'
import { dashboardService } from '@/services/dashboardService'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { StatusBadge } from '@/components/StatusBadge'
import { PageHeader } from '@/components/PageHeader'

const STATUS_ORDER: ExperimentStatus[] = [
  'PLANNED',
  'IN_PROGRESS',
  'COMPLETED',
  'FAILED',
]

export default function Dashboard() {
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

  if (loading) return <LoadingSpinner message="Loading dashboard…" />
  if (error) return <ErrorMessage error={error} onRetry={fetchStats} />

  const s = stats!

  return (
    <div>
      <PageHeader
        title="Research Dashboard"
        subtitle="Overview of all active research projects and experiments"
        actions={
          <button className="btn btn-secondary btn-sm" onClick={fetchStats}>
            <RotateCw size={14} style={{ marginRight: 6 }} /> Refresh
          </button>
        }
      />

      {/* ── Summary cards ────────────────────────────────── */}
      <div className="stat-grid" style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 'var(--space-5)',
        marginBottom: 'var(--space-8)',
      }}>
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
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 'var(--space-1)',
                  }}>
                    <StatusBadge status={status} />
                    <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>
                      {count}
                    </span>
                  </div>
                  <div style={{
                    height: 6,
                    background: 'var(--color-border)',
                    borderRadius: 3,
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${pct}%`,
                      background: statusToColor(status),
                      borderRadius: 3,
                      transition: 'width 0.5s ease',
                    }} />
                  </div>
                </div>
              )
            })}

            {s.total_experiments === 0 && (
              <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                No experiments yet.{' '}
                <Link to="/experiments">Create your first experiment →</Link>
              </p>
            )}
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
                <p>No experiments yet.</p>
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
    PLANNED:     'var(--color-info)',
    IN_PROGRESS: 'var(--color-warning)',
    COMPLETED:   'var(--color-success)',
    FAILED:      'var(--color-danger)',
    ARCHIVED:    'var(--color-text-muted)',
  }
  return map[status] ?? 'var(--color-border)'
}
