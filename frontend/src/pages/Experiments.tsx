/**
 * GreenSynth Analytics — Experiments List Page (Phase 2 Update)
 *
 * Scoped to the authenticated user's assigned research project (P1–P8).
 */

import React, { useEffect, useState, useCallback } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { FlaskConical, Check, X, FolderKanban } from 'lucide-react'
import type {
  ExperimentCreate,
  ExperimentStatus,
  ExperimentSummary,
  ParameterDefinition,
} from '@/types'
import { experimentService } from '@/services/experimentService'
import { parameterService } from '@/services/parameterService'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { EmptyState } from '@/components/EmptyState'
import { StatusBadge } from '@/components/StatusBadge'
import { PageHeader } from '@/components/PageHeader'
import { DynamicParameterForm } from '@/components/DynamicParameterForm'
import { useProjectContext } from '@/context/ProjectContext'
import type { ApiError } from '@/types'

const STATUSES: { value: ExperimentStatus | ''; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'PLANNED', label: 'Planned' },
  { value: 'IN_PROGRESS', label: 'In Progress' },
  { value: 'COMPLETED', label: 'Completed' },
  { value: 'FAILED', label: 'Failed' },
]

const EMPTY_FORM: ExperimentCreate = {
  project_id: '',
  experiment_code: '',
  title: '',
  status: 'PLANNED',
  researcher: '',
  notes: '',
}

export default function Experiments() {
  const navigate = useNavigate()
  const location = useLocation()
  const { projectId, projectCode, projectName } = useProjectContext()

  const [notification, setNotification] = useState<string | null>(
    (location.state as { notification?: string } | null)?.notification ?? null
  )
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState<ExperimentCreate>(EMPTY_FORM)
  const [paramDefs, setParamDefs] = useState<ParameterDefinition[]>([])
  const [paramValues, setParamValues] = useState<Record<string, { value: string; notes?: string }>>({})
  const [loadingParams, setLoadingParams] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const fetchData = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const exps = await experimentService.getAll({
        project_id: projectId,
        status: statusFilter || undefined,
      })
      setExperiments(exps)
    } catch (e: unknown) {
      setError((e as ApiError)?.message ?? 'Failed to load experiments.')
    } finally {
      setLoading(false)
    }
  }, [projectId, statusFilter])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleOpenCreate = () => {
    setFormError(null)
    setForm({
      ...EMPTY_FORM,
      project_id: projectId || '',
      experiment_code: projectCode ? `${projectCode}-EXP-` : '',
    })
    setShowCreate(true)
  }

  // When projectId is active, fetch parameter definitions
  useEffect(() => {
    if (!projectId) {
      setParamDefs([])
      setParamValues({})
      return
    }

    setLoadingParams(true)
    parameterService
      .getProjectParameters(projectId, true)
      .then((defs) => {
        setParamDefs(defs)
        const initial: Record<string, { value: string; notes?: string }> = {}
        defs.forEach((d) => {
          initial[d.id] = { value: '', notes: '' }
        })
        setParamValues(initial)
      })
      .catch((err) => console.error('Failed to load project parameter definitions:', err))
      .finally(() => setLoadingParams(false))
  }, [projectId])

  const filtered = experiments.filter((e) => {
    const q = search.toLowerCase()
    const matchesSearch =
      !search ||
      e.experiment_code.toLowerCase().includes(q) ||
      e.title.toLowerCase().includes(q) ||
      (e.researcher ?? '').toLowerCase().includes(q)
    return matchesSearch
  })

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectId) {
      setFormError('No assigned project available. Please activate your research group.')
      return
    }

    setSaving(true)
    setFormError(null)
    try {
      // 1. Create Experiment
      const exp = await experimentService.create({
        ...form,
        project_id: projectId,
      })

      // 2. Save parameters if any parameter inputs are provided
      const paramList = Object.entries(paramValues)
        .filter(([_, item]) => item.value !== undefined && item.value.trim() !== '')
        .map(([defId, item]) => ({
          parameter_definition_id: defId,
          value: item.value,
          notes: item.notes,
        }))

      if (paramList.length > 0) {
        await parameterService.saveExperimentParameters(exp.id, paramList)
      }

      setShowCreate(false)
      setForm(EMPTY_FORM)
      setParamValues({})
      await fetchData()
      navigate(`/experiments/${exp.id}`)
    } catch (e: unknown) {
      setFormError((e as ApiError)?.message ?? 'Failed to create experiment.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      {notification && (
        <div
          style={{
            backgroundColor: '#ecfdf5',
            borderLeft: '4px solid #10b981',
            color: '#065f46',
            padding: '0.75rem 1rem',
            borderRadius: '6px',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Check size={18} />
            <span>{notification}</span>
          </div>
          <button
            type="button"
            onClick={() => setNotification(null)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: '#065f46',
              fontSize: '1rem',
              lineHeight: 1,
            }}
            aria-label="Dismiss notification"
          >
            <X size={16} />
          </button>
        </div>
      )}

      <PageHeader
        title="Experiments"
        subtitle={`${experiments.length} experiment${experiments.length !== 1 ? 's' : ''} in assigned project ${projectCode || ''}`}
        actions={
          <button className="btn btn-primary" onClick={handleOpenCreate} disabled={!projectId}>
            + New Experiment
          </button>
        }
      />

      {/* Filter bar */}
      <div className="filter-bar">
        <input
          type="text"
          className="form-control search-input"
          placeholder="Search experiments in assigned project…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search experiments"
          id="experiment-search"
        />
        <select
          className="form-control"
          style={{ width: 180 }}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Filter by status"
          id="status-filter"
        >
          {STATUSES.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 14px',
            background: '#f8fafc',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 600,
            color: '#0f766e',
            whiteSpace: 'nowrap',
          }}
        >
          <FolderKanban size={15} />
          <span>Project: {projectCode ? `${projectCode} — ${projectName || projectCode}` : 'Loading...'}</span>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner message="Loading experiments…" />
      ) : error ? (
        <ErrorMessage error={error} onRetry={fetchData} />
      ) : filtered.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={<FlaskConical size={32} />}
            title={search || statusFilter ? 'No matching experiments' : 'No experiments yet'}
            description="No experiments have been created for this project yet. Create an experiment to record a synthesis run."
            action={
              <button className="btn btn-primary" onClick={handleOpenCreate} disabled={!projectId}>
                Create Experiment
              </button>
            }
          />
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Researcher</th>
                  <th>Date</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((exp) => (
                  <tr key={exp.id}>
                    <td>
                      <Link to={`/experiments/${exp.id}`} className="font-mono font-bold">
                        {exp.experiment_code}
                      </Link>
                    </td>
                    <td>{exp.title}</td>
                    <td><StatusBadge status={exp.status} /></td>
                    <td>{exp.researcher ?? '—'}</td>
                    <td>{exp.experiment_date ? new Date(exp.experiment_date).toLocaleDateString() : '—'}</td>
                    <td>{new Date(exp.created_at).toLocaleDateString()}</td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => navigate(`/experiments/${exp.id}`)}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Create Experiment Modal with Dynamic Parameters ──────────────── */}
      {showCreate && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 720 }}>
            <div className="modal-header">
              <h2 className="modal-title">Create Experiment</h2>
              <button className="modal-close" onClick={() => setShowCreate(false)} aria-label="Close"><X size={18} /></button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                {formError && <ErrorMessage error={formError} />}
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label required" htmlFor="exp-project">Assigned Project</label>
                    <div
                      id="exp-project"
                      style={{
                        padding: '10px 12px',
                        background: '#f1f5f9',
                        border: '1px solid #cbd5e1',
                        borderRadius: '6px',
                        fontSize: '14px',
                        fontWeight: 600,
                        color: '#0f766e',
                      }}
                    >
                      {projectCode ? `${projectCode} — ${projectName || projectCode}` : 'Resolving project...'}
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label required" htmlFor="exp-code">Experiment Code</label>
                    <input
                      id="exp-code"
                      className="form-control"
                      placeholder="e.g. P7-EXP-001"
                      value={form.experiment_code}
                      onChange={(e) => setForm({ ...form, experiment_code: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group span-2">
                    <label className="form-label required" htmlFor="exp-title">Title</label>
                    <input
                      id="exp-title"
                      className="form-control"
                      placeholder="e.g. Spray Pyrolysis CuO Synthesis with Mulberry Extract"
                      value={form.title}
                      onChange={(e) => setForm({ ...form, title: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="exp-status">Status</label>
                    <select
                      id="exp-status"
                      className="form-control"
                      value={form.status}
                      onChange={(e) => setForm({ ...form, status: e.target.value as ExperimentStatus })}
                    >
                      {STATUSES.filter((s) => s.value).map((s) => (
                        <option key={s.value} value={s.value}>{s.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="exp-researcher">Researcher</label>
                    <input
                      id="exp-researcher"
                      className="form-control"
                      placeholder="e.g. Atharva Kulkarni"
                      value={form.researcher}
                      onChange={(e) => setForm({ ...form, researcher: e.target.value })}
                    />
                  </div>
                </div>

                {/* Dynamic Parameter Form */}
                <div style={{ marginTop: 24 }}>
                  <DynamicParameterForm
                    definitions={paramDefs}
                    values={paramValues}
                    onChange={(defId, val, notes) =>
                      setParamValues((prev) => ({
                        ...prev,
                        [defId]: { value: val, notes },
                      }))
                    }
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving || !projectId}>
                  {saving ? 'Creating…' : 'Create Experiment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
