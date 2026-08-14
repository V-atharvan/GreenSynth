/**
 * GreenSynth Analytics — Experiments List Page (Phase 2 Update)
 *
 * Dynamically loads project parameter definitions when creating a new experiment.
 */

import React, { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import type {
  ExperimentCreate,
  ExperimentStatus,
  ExperimentSummary,
  ParameterDefinition,
  ProjectSummary,
} from '@/types'
import { experimentService } from '@/services/experimentService'
import { projectService } from '@/services/projectService'
import { parameterService } from '@/services/parameterService'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { EmptyState } from '@/components/EmptyState'
import { StatusBadge } from '@/components/StatusBadge'
import { PageHeader } from '@/components/PageHeader'
import { DynamicParameterForm } from '@/components/DynamicParameterForm'
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
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const location = useLocation()

  const [notification, setNotification] = useState<string | null>(
    (location.state as { notification?: string } | null)?.notification ?? null
  )
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([])
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [projectFilter, setProjectFilter] = useState<string>(
    searchParams.get('project_id') ?? ''
  )
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState<ExperimentCreate>({
    ...EMPTY_FORM,
    project_id: searchParams.get('project_id') ?? '',
  })
  const [paramDefs, setParamDefs] = useState<ParameterDefinition[]>([])
  const [paramValues, setParamValues] = useState<Record<string, { value: string; notes?: string }>>({})
  const [loadingParams, setLoadingParams] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [exps, projs] = await Promise.all([
        experimentService.getAll({
          project_id: projectFilter || undefined,
          status: statusFilter || undefined,
        }),
        projectService.getAll(),
      ])
      setExperiments(exps)
      setProjects(projs)

      if (projs.length > 0) {
        if (projectFilter && !projs.some((p) => p.id === projectFilter)) {
          setProjectFilter('')
        }
        if (!form.project_id || !projs.some((p) => p.id === form.project_id)) {
          setForm((prev) => ({ ...prev, project_id: projs[0].id }))
        }
      }
    } catch (e: unknown) {
      setError((e as ApiError)?.message ?? 'Failed to load experiments.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [projectFilter, statusFilter])

  const handleOpenCreate = () => {
    setFormError(null)
    const validProjId = projects.some((p) => p.id === projectFilter)
      ? projectFilter
      : projects[0]?.id ?? ''
    setForm({ ...EMPTY_FORM, project_id: validProjId })
    setShowCreate(true)
  }

  // When project_id changes in creation form, fetch parameter definitions
  useEffect(() => {
    if (!form.project_id) {
      setParamDefs([])
      setParamValues({})
      return
    }

    const loadDefs = async () => {
      setLoadingParams(true)
      try {
        const defs = await parameterService.getProjectParameters(form.project_id)
        setParamDefs(defs)
        // Initialize values object
        const initVal: Record<string, { value: string }> = {}
        defs.forEach((d) => {
          initVal[d.id] = { value: '' }
        })
        setParamValues(initVal)
      } catch {
        setParamDefs([])
      } finally {
        setLoadingParams(false)
      }
    }

    loadDefs()
  }, [form.project_id])

  const filtered = experiments.filter((e) =>
    `${e.experiment_code} ${e.title} ${e.researcher ?? ''}`
      .toLowerCase()
      .includes(search.toLowerCase())
  )

  const handleParamChange = (defId: string, val: string, notes?: string) => {
    setParamValues((prev) => ({
      ...prev,
      [defId]: { value: val, notes },
    }))
  }

  const handleCreate = async (evt: React.FormEvent) => {
    evt.preventDefault()
    setFormError(null)
    setSaving(true)
    try {
      // 1. Create Experiment
      const exp = await experimentService.create(form)

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
      setForm({ ...EMPTY_FORM, project_id: projectFilter })
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
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 500 }}>
            <span>✅</span>
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
            ✕
          </button>
        </div>
      )}

      <PageHeader
        title="Experiments"
        subtitle={`${experiments.length} experiment${experiments.length !== 1 ? 's' : ''}`}
        actions={
          <button className="btn btn-primary" onClick={handleOpenCreate}>
            + New Experiment
          </button>
        }
      />

      {/* Filter bar */}
      <div className="filter-bar">
        <input
          type="text"
          className="form-control search-input"
          placeholder="Search experiments…"
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
        <select
          className="form-control"
          style={{ width: 220 }}
          value={projectFilter}
          onChange={(e) => setProjectFilter(e.target.value)}
          aria-label="Filter by project"
          id="project-filter"
        >
          <option value="">All Projects</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>{p.project_code} — {p.name.slice(0, 40)}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <LoadingSpinner message="Loading experiments…" />
      ) : error ? (
        <ErrorMessage error={error} onRetry={fetchData} />
      ) : filtered.length === 0 ? (
        <div className="card">
          <EmptyState
            icon="🔬"
            title={search || statusFilter || projectFilter ? 'No matching experiments' : 'No experiments yet'}
            description="Create a new experiment to record a laboratory synthesis run."
            action={
              <button className="btn btn-primary" onClick={handleOpenCreate}>
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
                  <th>Project</th>
                  <th>Date</th>
                  <th>Researcher</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((exp) => (
                  <tr key={exp.id}>
                    <td>
                      <Link to={`/experiments/${exp.id}`} className="table-link text-mono">
                        {exp.experiment_code}
                      </Link>
                    </td>
                    <td>
                      <Link to={`/experiments/${exp.id}`} className="table-link">
                        {exp.title}
                      </Link>
                    </td>
                    <td><StatusBadge status={exp.status} /></td>
                    <td>
                      <Link to={`/projects/${exp.project_id}`} className="table-link text-mono">
                        {exp.project_id.slice(0, 8)}…
                      </Link>
                    </td>
                    <td style={{ color: 'var(--color-text-secondary)' }}>
                      {exp.experiment_date
                        ? new Date(exp.experiment_date).toLocaleDateString()
                        : '—'}
                    </td>
                    <td style={{ color: 'var(--color-text-secondary)' }}>
                      {exp.researcher ?? '—'}
                    </td>
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
              <button className="modal-close" onClick={() => setShowCreate(false)} aria-label="Close">✕</button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                {formError && <ErrorMessage error={formError} />}
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label required" htmlFor="exp-project">Project</label>
                    <select
                      id="exp-project"
                      className="form-control"
                      value={form.project_id}
                      onChange={(e) => setForm({ ...form, project_id: e.target.value })}
                      required
                    >
                      <option value="">— Select project —</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.project_code} — {p.name.slice(0, 50)}
                        </option>
                      ))}
                    </select>
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
                      placeholder="Brief descriptive title"
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
                      <option value="PLANNED">Planned</option>
                      <option value="IN_PROGRESS">In Progress</option>
                      <option value="COMPLETED">Completed</option>
                      <option value="FAILED">Failed</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="exp-date">Experiment Date</label>
                    <input
                      id="exp-date"
                      type="date"
                      className="form-control"
                      value={form.experiment_date ?? ''}
                      onChange={(e) => setForm({ ...form, experiment_date: e.target.value || undefined })}
                    />
                  </div>
                  <div className="form-group span-2">
                    <label className="form-label" htmlFor="exp-researcher">Researcher</label>
                    <input
                      id="exp-researcher"
                      className="form-control"
                      placeholder="Name of conducting researcher"
                      value={form.researcher ?? ''}
                      onChange={(e) => setForm({ ...form, researcher: e.target.value })}
                    />
                  </div>
                </div>

                {/* Synthesis Parameters Section */}
                {form.project_id && (
                  <div style={{ marginTop: 24, borderTop: '1px solid var(--color-border)', paddingTop: 16 }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 12 }}>
                      Synthesis Parameters
                    </h3>
                    {loadingParams ? (
                      <LoadingSpinner message="Loading project parameter definitions…" size="sm" />
                    ) : (
                      <DynamicParameterForm
                        definitions={paramDefs}
                        values={paramValues}
                        onChange={handleParamChange}
                      />
                    )}
                  </div>
                )}
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowCreate(false)}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
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
