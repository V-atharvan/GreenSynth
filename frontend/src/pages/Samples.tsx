/**
 * GreenSynth Analytics — Samples List Page (Phase 2 Update)
 */

import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { TestTube2, X } from 'lucide-react'
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

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [samps, exps] = await Promise.all([
        sampleService.getAll({
          experiment_id: expFilter || undefined,
          status: statusFilter || undefined,
        }),
        experimentService.getAll(),
      ])
      setSamples(samps)
      setExperiments(exps)
    } catch (e: unknown) {
      setError((e as ApiError)?.message ?? 'Failed to load samples.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [expFilter, statusFilter])

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
        subtitle={`${samples.length} sample${samples.length !== 1 ? 's' : ''}`}
        actions={
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            + New Sample
          </button>
        }
      />

      {/* Filter bar */}
      <div className="filter-bar">
        <input
          type="text"
          className="form-control search-input"
          placeholder="Search samples…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search samples"
          id="sample-search"
        />
        <select
          className="form-control"
          style={{ width: 220 }}
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
          <option value="">All Experiments</option>
          {experiments.map((e) => (
            <option key={e.id} value={e.id}>{e.experiment_code} — {e.title.slice(0, 35)}</option>
          ))}
        </select>
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
            description="Create a new physical sample associated with an experiment."
            action={
              <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
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
                  <th>Sample Code</th>
                  <th>Name</th>
                  <th>Material</th>
                  <th>Status</th>
                  <th>Experiment</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <Link to={`/samples/${s.id}`} className="table-link text-mono">
                        {s.sample_code}
                      </Link>
                    </td>
                    <td>
                      <Link to={`/samples/${s.id}`} className="table-link">
                        {s.name}
                      </Link>
                    </td>
                    <td>{s.material ?? '—'}</td>
                    <td><StatusBadge status={s.status} /></td>
                    <td>
                      <Link to={`/experiments/${s.experiment_id}`} className="table-link text-mono">
                        {s.experiment_id.slice(0, 8)}…
                      </Link>
                    </td>
                    <td style={{ color: 'var(--color-text-secondary)' }}>
                      {new Date(s.created_at).toLocaleDateString()}
                    </td>
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

      {/* Create Sample Modal */}
      {showCreate && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 540 }}>
            <div className="modal-header">
              <h2 className="modal-title">Create Physical Sample</h2>
              <button className="modal-close" onClick={() => setShowCreate(false)} aria-label="Close"><X size={18} /></button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                {formError && <ErrorMessage error={formError} />}
                <div className="form-grid">
                  <div className="form-group span-2">
                    <label className="form-label required" htmlFor="samp-exp">Parent Experiment</label>
                    <select
                      id="samp-exp"
                      className="form-control"
                      value={form.experiment_id}
                      onChange={(e) => setForm({ ...form, experiment_id: e.target.value })}
                      required
                    >
                      <option value="">— Select experiment —</option>
                      {experiments.map((e) => (
                        <option key={e.id} value={e.id}>
                          {e.experiment_code} — {e.title.slice(0, 45)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label required" htmlFor="samp-code">Sample Code</label>
                    <input
                      id="samp-code"
                      className="form-control"
                      placeholder="e.g. P7-EXP-001-S1"
                      value={form.sample_code}
                      onChange={(e) => setForm({ ...form, sample_code: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label required" htmlFor="samp-name">Sample Name</label>
                    <input
                      id="samp-name"
                      className="form-control"
                      placeholder="e.g. Sample A"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="samp-material">Material</label>
                    <input
                      id="samp-material"
                      className="form-control"
                      placeholder="e.g. CuO"
                      value={form.material ?? ''}
                      onChange={(e) => setForm({ ...form, material: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="samp-status">Status</label>
                    <select
                      id="samp-status"
                      className="form-control"
                      value={form.status}
                      onChange={(e) => setForm({ ...form, status: e.target.value as SampleStatus })}
                    >
                      <option value="PREPARED">Prepared</option>
                      <option value="READY_FOR_CHARACTERIZATION">Ready for Characterization</option>
                      <option value="UNDER_ANALYSIS">Under Analysis</option>
                      <option value="COMPLETED">Completed</option>
                    </select>
                  </div>
                  <div className="form-group span-2">
                    <label className="form-label" htmlFor="samp-desc">Description</label>
                    <textarea
                      id="samp-desc"
                      className="form-control"
                      rows={3}
                      placeholder="Substrate details, film appearance, film thickness notes, etc."
                      value={form.description ?? ''}
                      onChange={(e) => setForm({ ...form, description: e.target.value })}
                    />
                  </div>
                </div>
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
