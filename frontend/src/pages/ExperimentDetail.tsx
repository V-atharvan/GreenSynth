/**
 * GreenSynth Analytics — Experiment Detail Page (Phase 2 Update)
 *
 * Displays:
 *  A. Experiment Information
 *  B. Synthesis Parameters (Recorded values table + dynamic edit form)
 *  C. Samples (Associated physical specimens)
 *  D. Future Characterization (Empty state placeholder for Phase 5+)
 */

import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { X } from 'lucide-react'
import type {
  ExperimentParameter,
  ExperimentStatus,
  ExperimentUpdate,
  ExperimentWithProject,
  ParameterDefinition,
  SampleCreate,
  SampleStatus,
  SampleSummary,
} from '@/types'
import { experimentService } from '@/services/experimentService'
import { sampleService } from '@/services/sampleService'
import { parameterService } from '@/services/parameterService'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { StatusBadge } from '@/components/StatusBadge'
import { PageHeader } from '@/components/PageHeader'
import { ParameterDisplay } from '@/components/ParameterDisplay'
import { DynamicParameterForm } from '@/components/DynamicParameterForm'
import { DeleteExperimentModal } from '@/components/DeleteExperimentModal'
import type { ApiError } from '@/types'

const STATUSES: ExperimentStatus[] = [
  'PLANNED',
  'IN_PROGRESS',
  'COMPLETED',
  'FAILED',
]

const SAMPLE_STATUS_OPTIONS: { value: SampleStatus; label: string }[] = [
  { value: 'PREPARED', label: 'Prepared' },
  { value: 'READY_FOR_CHARACTERIZATION', label: 'Ready for Characterization' },
  { value: 'UNDER_ANALYSIS', label: 'Under Analysis' },
  { value: 'COMPLETED', label: 'Completed' },
]

export default function ExperimentDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [experiment, setExperiment] = useState<ExperimentWithProject | null>(null)
  const [samples, setSamples] = useState<SampleSummary[]>([])
  const [parameters, setParameters] = useState<ExperimentParameter[]>([])
  const [parameterDefs, setParameterDefs] = useState<ParameterDefinition[]>([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'parameters' | 'samples'>('overview')

  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const handleDeleteExperiment = async () => {
    if (!id) return
    setIsDeleting(true)
    setDeleteError(null)
    try {
      await experimentService.delete(id)
      setShowDeleteModal(false)
      navigate('/experiments', {
        state: { notification: 'Experiment deleted successfully.' },
      })
    } catch (e: unknown) {
      setDeleteError(
        (e as ApiError)?.message ?? 'Unable to delete experiment. Please try again.'
      )
    } finally {
      setIsDeleting(false)
    }
  }

  const [editingExp, setEditingExp] = useState(false)
  const [editExpForm, setEditExpForm] = useState<ExperimentUpdate>({})
  const [savingExp, setSavingExp] = useState(false)
  const [expError, setExpError] = useState<string | null>(null)

  const [editingParams, setEditingParams] = useState(false)
  const [paramValues, setParamValues] = useState<Record<string, { value: string; notes?: string }>>({})
  const [savingParams, setSavingParams] = useState(false)
  const [paramError, setParamError] = useState<string | null>(null)

  const [showAddSample, setShowAddSample] = useState(false)
  const [sampleForm, setSampleForm] = useState<SampleCreate>({
    experiment_id: id ?? '',
    sample_code: '',
    name: '',
    material: '',
    description: '',
    status: 'PREPARED',
  })
  const [sampleError, setSampleError] = useState<string | null>(null)
  const [addingSample, setAddingSample] = useState(false)

  const fetchAll = async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const exp = await experimentService.getById(id)
      setExperiment(exp)

      const [samps, paramsList, defsList] = await Promise.all([
        sampleService.getAll({ experiment_id: id }),
        parameterService.getExperimentParameters(id),
        parameterService.getProjectParameters(exp.project_id),
      ])

      setSamples(samps)
      setParameters(paramsList)
      setParameterDefs(defsList)

      // Initialize parameter form values map
      const initVal: Record<string, { value: string; notes?: string }> = {}
      defsList.forEach((d) => {
        const found = paramsList.find((p) => p.parameter_definition_id === d.id)
        initVal[d.id] = {
          value: found?.value ?? '',
          notes: found?.notes ?? undefined,
        }
      })
      setParamValues(initVal)
    } catch (e: unknown) {
      setError((e as ApiError)?.message ?? 'Failed to load experiment.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchAll() }, [id])

  const handleSaveExp = async () => {
    if (!id) return
    setSavingExp(true)
    setExpError(null)
    try {
      await experimentService.update(id, editExpForm)
      setEditingExp(false)
      await fetchAll()
    } catch (e: unknown) {
      setExpError((e as ApiError)?.message ?? 'Failed to update experiment.')
    } finally {
      setSavingExp(false)
    }
  }

  const handleSaveParams = async () => {
    if (!id) return
    setSavingParams(true)
    setParamError(null)
    try {
      const paramList = Object.entries(paramValues)
        .filter(([_, item]) => item.value !== undefined && item.value.trim() !== '')
        .map(([defId, item]) => ({
          parameter_definition_id: defId,
          value: item.value,
          notes: item.notes,
        }))

      await parameterService.saveExperimentParameters(id, paramList)
      setEditingParams(false)
      await fetchAll()
    } catch (e: unknown) {
      setParamError((e as ApiError)?.message ?? 'Validation failed.')
    } finally {
      setSavingParams(false)
    }
  }

  const handleAddSample = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!id) return
    setAddingSample(true)
    setSampleError(null)
    try {
      await sampleService.create({ ...sampleForm, experiment_id: id })
      setShowAddSample(false)
      setSampleForm({
        experiment_id: id,
        sample_code: '',
        name: '',
        material: experiment?.project.material ?? '',
        description: '',
        status: 'PREPARED',
      })
      await fetchAll()
    } catch (e: unknown) {
      setSampleError((e as ApiError)?.message ?? 'Failed to create sample.')
    } finally {
      setAddingSample(false)
    }
  }

  const [downloadingPdf, setDownloadingPdf] = useState(false)
  const [pdfError, setPdfError] = useState<string | null>(null)

  const handleDownloadPdf = async () => {
    if (!id || !experiment) return
    setDownloadingPdf(true)
    setPdfError(null)
    try {
      const blob = await experimentService.downloadPdfReport(id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `Experiment_Report_${experiment.experiment_code}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (e: unknown) {
      setPdfError((e as ApiError)?.message ?? 'Failed to generate scientific PDF report.')
    } finally {
      setDownloadingPdf(false)
    }
  }

  if (loading) return <LoadingSpinner message="Loading experiment…" />
  if (error) return <ErrorMessage error={error} onRetry={fetchAll} />
  if (!experiment) return null

  return (
    <div>
      {/* Breadcrumb */}
      <div className="breadcrumb">
        <Link to="/projects">Projects</Link>
        <span className="breadcrumb-separator">›</span>
        <Link to={`/projects/${experiment.project.id}`}>{experiment.project.project_code}</Link>
        <span className="breadcrumb-separator">›</span>
        <Link to="/experiments">Experiments</Link>
        <span className="breadcrumb-separator">›</span>
        <span className="breadcrumb-current">{experiment.experiment_code}</span>
      </div>

      {pdfError && <ErrorMessage error={pdfError} />}

      <PageHeader
        title={experiment.title}
        subtitle={`${experiment.experiment_code} · Project ${experiment.project.project_code} (${experiment.project.material})`}
        actions={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
            >
              {downloadingPdf ? 'Generating PDF...' : 'Export PDF Report'}
            </button>
            <StatusBadge status={experiment.status} />
          </div>
        }
      />

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab-button ${activeTab === 'parameters' ? 'active' : ''}`}
          onClick={() => setActiveTab('parameters')}
        >
          Synthesis Parameters ({parameters.length})
        </button>
        <button
          className={`tab-button ${activeTab === 'samples' ? 'active' : ''}`}
          onClick={() => setActiveTab('samples')}
        >
          Samples ({samples.length})
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header">
            <h2>A. Experiment Information</h2>
            {!editingExp && (
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setEditExpForm({
                      title: experiment.title,
                      status: experiment.status,
                      experiment_date: experiment.experiment_date ?? undefined,
                      researcher: experiment.researcher ?? undefined,
                      notes: experiment.notes ?? undefined,
                    })
                    setEditingExp(true)
                  }}
                >
                  Edit Info
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => {
                    setDeleteError(null)
                    setShowDeleteModal(true)
                  }}
                >
                  Delete Experiment
                </button>
              </div>
            )}
          </div>
          <div className="card-body">
            {editingExp ? (
              <>
                {expError && <ErrorMessage error={expError} />}
                <div className="form-grid" style={{ marginBottom: 16 }}>
                  <div className="form-group span-2">
                    <label className="form-label required">Title</label>
                    <input
                      className="form-control"
                      value={editExpForm.title ?? ''}
                      onChange={(e) => setEditExpForm({ ...editExpForm, title: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Status</label>
                    <select
                      className="form-control"
                      value={editExpForm.status}
                      onChange={(e) => setEditExpForm({ ...editExpForm, status: e.target.value as ExperimentStatus })}
                    >
                      {STATUSES.map((st) => (
                        <option key={st} value={st}>{st}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Date Conducted</label>
                    <input
                      type="date"
                      className="form-control"
                      value={editExpForm.experiment_date ?? ''}
                      onChange={(e) => setEditExpForm({ ...editExpForm, experiment_date: e.target.value || undefined })}
                    />
                  </div>
                  <div className="form-group span-2">
                    <label className="form-label">Researcher</label>
                    <input
                      className="form-control"
                      value={editExpForm.researcher ?? ''}
                      onChange={(e) => setEditExpForm({ ...editExpForm, researcher: e.target.value })}
                    />
                  </div>
                  <div className="form-group span-2">
                    <label className="form-label">Notes</label>
                    <textarea
                      className="form-control"
                      rows={3}
                      value={editExpForm.notes ?? ''}
                      onChange={(e) => setEditExpForm({ ...editExpForm, notes: e.target.value })}
                    />
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-primary" onClick={handleSaveExp} disabled={savingExp}>
                    {savingExp ? 'Saving…' : 'Save Changes'}
                  </button>
                  <button className="btn btn-secondary" onClick={() => setEditingExp(false)} disabled={savingExp}>
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Experiment Code</span>
                  <span className="detail-value code">{experiment.experiment_code}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Status</span>
                  <StatusBadge status={experiment.status} />
                </div>
                <div className="detail-item">
                  <span className="detail-label">Parent Project</span>
                  <span className="detail-value">
                    <Link to={`/projects/${experiment.project.id}`} className="table-link">
                      {experiment.project.name} ({experiment.project.project_code})
                    </Link>
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Method & Solvent</span>
                  <span className="detail-value">
                    <span className="badge badge-planned" style={{ marginRight: 6 }}>
                      {experiment.project.synthesis_method}
                    </span>
                    <span className="badge badge-completed">
                      {experiment.project.solvent}
                    </span>
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Date Conducted</span>
                  <span className="detail-value">
                    {experiment.experiment_date
                      ? new Date(experiment.experiment_date).toLocaleDateString()
                      : 'Not specified'}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Researcher</span>
                  <span className="detail-value">{experiment.researcher ?? 'Not specified'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Created At</span>
                  <span className="detail-value">
                    {new Date(experiment.created_at).toLocaleString()}
                  </span>
                </div>
                {experiment.notes && (
                  <div className="detail-item" style={{ gridColumn: '1 / -1' }}>
                    <span className="detail-label">Notes</span>
                    <span className="detail-value" style={{ lineHeight: 1.6 }}>
                      {experiment.notes}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Synthesis Parameters Tab / Section */}
      {(activeTab === 'overview' || activeTab === 'parameters') && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header">
            <h2>B. Synthesis Parameters</h2>
            {!editingParams ? (
              <button className="btn btn-secondary btn-sm" onClick={() => setEditingParams(true)}>
                Edit Parameters
              </button>
            ) : (
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-primary btn-sm" onClick={handleSaveParams} disabled={savingParams}>
                  {savingParams ? 'Saving…' : 'Save Parameters'}
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => setEditingParams(false)} disabled={savingParams}>
                  Cancel
                </button>
              </div>
            )}
          </div>

          <div className="card-body">
            {paramError && <ErrorMessage error={paramError} />}

            {editingParams ? (
              <DynamicParameterForm
                definitions={parameterDefs}
                values={paramValues}
                onChange={(defId, val, notes) => {
                  setParamValues((prev) => ({
                    ...prev,
                    [defId]: { value: val, notes },
                  }))
                }}
                projectCode={experiment?.project?.project_code}
              />
            ) : (
              <ParameterDisplay
                parameters={parameters}
                onEdit={() => setEditingParams(true)}
                projectCode={experiment?.project?.project_code}
              />
            )}
          </div>
        </div>
      )}

      {/* Samples Tab / Section */}
      {(activeTab === 'overview' || activeTab === 'samples') && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header">
            <h2>C. Samples ({samples.length})</h2>
            <button className="btn btn-primary btn-sm" onClick={() => setShowAddSample(true)}>
              + Add Sample
            </button>
          </div>
          <div className="table-container">
            {samples.length === 0 ? (
              <div style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                No samples recorded for this experiment yet.
              </div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Sample Code</th>
                    <th>Name</th>
                    <th>Material</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {samples.map((s) => (
                    <tr key={s.id}>
                      <td>
                        <Link to={`/samples/${s.id}`} className="table-link text-mono">
                          {s.sample_code}
                        </Link>
                      </td>
                      <td>{s.name}</td>
                      <td>{s.material ?? '—'}</td>
                      <td><StatusBadge status={s.status} /></td>
                      <td style={{ color: 'var(--color-text-secondary)' }}>
                        {new Date(s.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <Link to={`/samples/${s.id}`} className="btn btn-secondary btn-sm">
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Future Characterization Section (Empty State placeholder) */}
      <div className="card">
        <div className="card-header">
          <h2>D. Future Characterization Data</h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
            Phase 5+ Placeholder
          </span>
        </div>
        <div className="card-body" style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
          <p style={{ fontStyle: 'italic' }}>
            No characterization data has been uploaded yet.
          </p>
        </div>
      </div>

      {/* Add Sample Modal */}
      {showAddSample && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 540 }}>
            <div className="modal-header">
              <h2 className="modal-title">Add Sample to Experiment</h2>
              <button className="modal-close" onClick={() => setShowAddSample(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleAddSample}>
              <div className="modal-body">
                {sampleError && <ErrorMessage error={sampleError} />}
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label required">Sample Code</label>
                    <input
                      className="form-control"
                      placeholder="e.g. P7-EXP-001-S1"
                      value={sampleForm.sample_code}
                      onChange={(e) => setSampleForm({ ...sampleForm, sample_code: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label required">Sample Name</label>
                    <input
                      className="form-control"
                      placeholder="e.g. Sample A (FTO Glass)"
                      value={sampleForm.name}
                      onChange={(e) => setSampleForm({ ...sampleForm, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Material</label>
                    <input
                      className="form-control"
                      placeholder="e.g. CuO"
                      value={sampleForm.material ?? ''}
                      onChange={(e) => setSampleForm({ ...sampleForm, material: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Status</label>
                    <select
                      className="form-control"
                      value={sampleForm.status}
                      onChange={(e) => setSampleForm({ ...sampleForm, status: e.target.value as SampleStatus })}
                    >
                      {SAMPLE_STATUS_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group span-2">
                    <label className="form-label">Description / Notes</label>
                    <textarea
                      className="form-control"
                      rows={3}
                      placeholder="Substrate, dimensions, film appearance, etc."
                      value={sampleForm.description ?? ''}
                      onChange={(e) => setSampleForm({ ...sampleForm, description: e.target.value })}
                    />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowAddSample(false)}
                  disabled={addingSample}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={addingSample}>
                  {addingSample ? 'Adding…' : 'Add Sample'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Experiment Modal */}
      <DeleteExperimentModal
        isOpen={showDeleteModal}
        experimentCode={experiment.experiment_code}
        experimentTitle={experiment.title}
        isDeleting={isDeleting}
        error={deleteError}
        onConfirm={handleDeleteExperiment}
        onCancel={() => {
          if (!isDeleting) {
            setShowDeleteModal(false)
            setDeleteError(null)
          }
        }}
      />
    </div>
  )
}
