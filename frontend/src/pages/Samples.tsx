/**
 * GreenSynth Analytics — Samples List Page (Phase 2 Update)
 *
 * Scoped to the authenticated user's assigned research project (P1–P8).
 */

import React, { useEffect, useState, useCallback } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { TestTube2, X, FolderKanban } from 'lucide-react'
import type {
  ExperimentSummary,
  SampleCreate,
  SampleStatus,
  SampleSummary,
} from '@/types'
import { sampleService } from '@/services/sampleService'
import { experimentService } from '@/services/experimentService'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { EmptyState } from '@/components/EmptyState'
import { StatusBadge } from '@/components/StatusBadge'
import { PageHeader } from '@/components/PageHeader'
import { useProjectContext } from '@/context/ProjectContext'
import type { ApiError } from '@/types'

const STATUSES: { value: SampleStatus | ''; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'PREPARED', label: 'Prepared' },
  { value: 'READY_FOR_CHARACTERIZATION', label: 'Ready for Characterization' },
  { value: 'UNDER_ANALYSIS', label: 'Under Analysis' },
  { value: 'COMPLETED', label: 'Completed' },
]

const EMPTY_FORM: SampleCreate = {
  experiment_id: '',
  sample_code: '',
  name: '',
  material: '',
  description: '',
  notes: '',
  status: 'PREPARED',
}

export default function Samples() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { projectId, projectCode, projectName } = useProjectContext()

  const [samples, setSamples] = useState<SampleSummary[]>([])
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [expFilter, setExpFilter] = useState<string>(
    searchParams.get('experiment_id') ?? ''
  )
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState<SampleCreate>({
    ...EMPTY_FORM,
    experiment_id: searchParams.get('experiment_id') ?? '',
  })
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const fetchData = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const [samps, exps] = await Promise.all([
        sampleService.getAll({
          experiment_id: expFilter || undefined,
          status: statusFilter || undefined,
        }),
        experimentService.getAll({ project_id: projectId }),
      ])
      setSamples(samps)
      setExperiments(exps)
    } catch (e: unknown) {
      setError((e as ApiError)?.message ?? 'Failed to load samples.')
    } finally {
      setLoading(false)
    }
  }, [projectId, expFilter, statusFilter])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const filtered = samples.filter((s) =>
    `${s.sample_code} ${s.name} ${s.material ?? ''}`
      .toLowerCase()
      .includes(search.toLowerCase())
  )

  const handleCreate = async (evt: React.FormEvent) => {
    evt.preventDefault()
    setFormError(null)
    setSaving(true)
    try {
      await sampleService.create(form)
      setShowCreate(false)
      setForm({ ...EMPTY_FORM, experiment_id: expFilter })
      await fetchData()
    } catch (e: unknown) {
      setFormError((e as ApiError)?.message ?? 'Failed to create sample.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Physical Samples"
        subtitle={`${samples.length} sample${samples.length !== 1 ? 's' : ''} in assigned project ${projectCode || ''}`}
        actions={
          <button className="btn btn-primary" onClick={() => setShowCreate(true)} disabled={!projectId}>
            + New Sample
          </button>
        }
      />

      {/* Filter bar */}
      <div className="filter-bar">
        <input
          type="text"
          className="form-control search-input"
          placeholder="Search samples in assigned project…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search samples"
          id="sample-search"
        />
        <select
          className="form-control"
          style={{ width: 200 }}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Filter by status"
          id="sample-status-filter"
        >
          {STATUSES.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
        <select
          className="form-control"
          style={{ width: 220 }}
          value={expFilter}
          onChange={(e) => setExpFilter(e.target.value)}
          aria-label="Filter by experiment"
          id="sample-experiment-filter"
        >
          <option value="">All Project Experiments</option>
          {experiments.map((e) => (
            <option key={e.id} value={e.id}>{e.experiment_code} — {e.title.slice(0, 35)}</option>
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
        <LoadingSpinner message="Loading samples…" />
      ) : error ? (
        <ErrorMessage error={error} onRetry={fetchData} />
      ) : filtered.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={<TestTube2 size={32} />}
            title={search || statusFilter || expFilter ? 'No matching samples' : 'No samples yet'}
            description="No samples have been created for this project yet. Create a physical sample associated with an experiment."
            action={
              <button className="btn btn-primary" onClick={() => setShowCreate(true)} disabled={!projectId}>
                Create Sample
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
                  <th>Name</th>
                  <th>Experiment</th>
                  <th>Status</th>
                  <th>Material</th>
                  <th>Characterizations</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <Link to={`/samples/${s.id}`} className="font-mono font-bold">
                        {s.sample_code}
                      </Link>
                    </td>
                    <td>{s.name}</td>
                    <td>
                      <Link to={`/experiments/${s.experiment_id}`} className="font-mono text-sm">
                        {s.experiment_id.slice(0, 8)}...
                      </Link>
                    </td>
                    <td><StatusBadge status={s.status} /></td>
                    <td>{s.material ?? '—'}</td>
                    <td>
                      <span className="badge badge-gray">
                        {(s as any).characterization_count ?? 0}
                      </span>
                    </td>
                    <td>{new Date(s.created_at).toLocaleDateString()}</td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => navigate(`/samples/${s.id}`)}
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

      {/* ── Create Sample Modal ────────────────────────────────────────── */}
      {showCreate && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2 className="modal-title">Create Sample</h2>
              <button className="modal-close" onClick={() => setShowCreate(false)} aria-label="Close">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                {formError && <ErrorMessage error={formError} />}
                <div className="form-grid">
                  <div className="form-group span-2">
                    <label className="form-label required" htmlFor="sample-experiment">
                      Project Experiment
                    </label>
                    <select
                      id="sample-experiment"
                      className="form-control"
                      value={form.experiment_id}
                      onChange={(e) => setForm({ ...form, experiment_id: e.target.value })}
                      required
                    >
                      <option value="">— Select experiment —</option>
                      {experiments.map((e) => (
                        <option key={e.id} value={e.id}>
                          {e.experiment_code} — {e.title}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label required" htmlFor="sample-code">
                      Sample Code
                    </label>
                    <input
                      id="sample-code"
                      className="form-control"
                      placeholder="e.g. P7-SMP-001"
                      value={form.sample_code}
                      onChange={(e) => setForm({ ...form, sample_code: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label required" htmlFor="sample-name">
                      Sample Name
                    </label>
                    <input
                      id="sample-name"
                      className="form-control"
                      placeholder="e.g. CuO Thin Film #1"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="sample-material">Material</label>
                    <input
                      id="sample-material"
                      className="form-control"
                      placeholder="e.g. Copper Oxide (CuO)"
                      value={form.material ?? ''}
                      onChange={(e) => setForm({ ...form, material: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="sample-status">Status</label>
                    <select
                      id="sample-status"
                      className="form-control"
                      value={form.status}
                      onChange={(e) => setForm({ ...form, status: e.target.value as SampleStatus })}
                    >
                      {STATUSES.filter((s) => s.value).map((s) => (
                        <option key={s.value} value={s.value}>{s.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group span-2">
                    <label className="form-label" htmlFor="sample-desc">Description</label>
                    <textarea
                      id="sample-desc"
                      className="form-control"
                      rows={2}
                      placeholder="Optional sample description, preparation conditions, substrate type…"
                      value={form.description ?? ''}
                      onChange={(e) => setForm({ ...form, description: e.target.value })}
                    />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Creating…' : 'Create Sample'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
