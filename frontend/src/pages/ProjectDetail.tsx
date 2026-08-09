/**
 * GreenSynth Analytics — Project Detail Page (Phase 2 Update)
 */

import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import type {
  ExperimentSummary,
  ParameterDefinition,
  Project,
  ProjectUpdate,
} from '@/types'
import { projectService } from '@/services/projectService'
import { experimentService } from '@/services/experimentService'
import { parameterService } from '@/services/parameterService'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { StatusBadge } from '@/components/StatusBadge'
import { PageHeader } from '@/components/PageHeader'
import { ParameterManagementModal } from '@/components/ParameterManagementModal'
import type { ApiError } from '@/types'

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [project, setProject] = useState<Project | null>(null)
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([])
  const [parameterDefs, setParameterDefs] = useState<ParameterDefinition[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState<ProjectUpdate>({})
  const [saving, setSaving] = useState(false)
  const [editError, setEditError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'experiments' | 'parameters'>('overview')
  const [showParamModal, setShowParamModal] = useState(false)

  const fetchAll = async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const [p, exps, pdefs] = await Promise.all([
        projectService.getById(id),
        experimentService.getAll({ project_id: id }),
        parameterService.getProjectParameters(id, true),
      ])
      setProject(p)
      setExperiments(exps)
      setParameterDefs(pdefs)
    } catch (e: unknown) {
      setError((e as ApiError)?.message ?? 'Failed to load project details.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchAll() }, [id])

  const startEdit = () => {
    if (!project) return
    setEditForm({
      name: project.name,
      description: project.description ?? '',
      material: project.material,
      extract: project.extract,
      solvent: project.solvent,
      synthesis_method: project.synthesis_method,
    })
    setEditing(true)
  }

  const handleSave = async () => {
    if (!id) return
    setSaving(true)
    setEditError(null)
    try {
      await projectService.update(id, editForm)
      setEditing(false)
      await fetchAll()
    } catch (e: unknown) {
      setEditError((e as ApiError)?.message ?? 'Failed to update project.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <LoadingSpinner message="Loading project…" />
  if (error) return <ErrorMessage error={error} onRetry={fetchAll} />
  if (!project) return null

  const activeDefs = parameterDefs.filter((d) => d.status === 'ACTIVE')

  return (
    <div>
      {/* Breadcrumb */}
      <div className="breadcrumb">
        <Link to="/projects">Projects</Link>
        <span className="breadcrumb-separator">›</span>
        <span className="breadcrumb-current">{project.project_code}</span>
      </div>

      <PageHeader
        title={project.name}
        subtitle={`${project.project_code} · ${project.material} · ${project.synthesis_method}`}
        actions={
          <div style={{ display: 'flex', gap: 8 }}>
            {!editing && (
              <button className="btn btn-secondary" onClick={startEdit}>
                ✏ Edit
              </button>
            )}
            <StatusBadge status={project.status} />
          </div>
        }
      />

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
          id="tab-overview"
        >
          Overview
        </button>
        <button
          className={`tab-button ${activeTab === 'experiments' ? 'active' : ''}`}
          onClick={() => setActiveTab('experiments')}
          id="tab-experiments"
        >
          Experiments ({experiments.length})
        </button>
        <button
          className={`tab-button ${activeTab === 'parameters' ? 'active' : ''}`}
          onClick={() => setActiveTab('parameters')}
          id="tab-parameters"
        >
          Synthesis Parameters ({activeDefs.length})
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="card">
          <div className="card-body">
            {editing ? (
              <>
                {editError && <ErrorMessage error={editError} />}
                <div className="form-grid" style={{ marginBottom: 'var(--space-6)' }}>
                  <div className="form-group span-2">
                    <label className="form-label required">Project Name</label>
                    <input
                      className="form-control"
                      value={editForm.name ?? ''}
                      onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Material</label>
                    <input
                      className="form-control"
                      value={editForm.material ?? ''}
                      onChange={(e) => setEditForm({ ...editForm, material: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Synthesis Method</label>
                    <input
                      className="form-control"
                      value={editForm.synthesis_method ?? ''}
                      onChange={(e) => setEditForm({ ...editForm, synthesis_method: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Extract</label>
                    <input
                      className="form-control"
                      value={editForm.extract ?? ''}
                      onChange={(e) => setEditForm({ ...editForm, extract: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Solvent</label>
                    <input
                      className="form-control"
                      value={editForm.solvent ?? ''}
                      onChange={(e) => setEditForm({ ...editForm, solvent: e.target.value })}
                    />
                  </div>
                  <div className="form-group span-2">
                    <label className="form-label">Description</label>
                    <textarea
                      className="form-control"
                      rows={4}
                      value={editForm.description ?? ''}
                      onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    />
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                    {saving ? 'Saving…' : 'Save Changes'}
                  </button>
                  <button className="btn btn-secondary" onClick={() => setEditing(false)} disabled={saving}>
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Project Code</span>
                  <span className="detail-value code">{project.project_code}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Status</span>
                  <StatusBadge status={project.status} />
                </div>
                <div className="detail-item">
                  <span className="detail-label">Material</span>
                  <span className="detail-value">{project.material}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Synthesis Method</span>
                  <span className="detail-value">{project.synthesis_method}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Extract</span>
                  <span className="detail-value">{project.extract}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Solvent</span>
                  <span className="detail-value">{project.solvent}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Total Experiments</span>
                  <span className="detail-value">{experiments.length}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Configured Parameters</span>
                  <span className="detail-value">{activeDefs.length} active definitions</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Created</span>
                  <span className="detail-value">
                    {new Date(project.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Last Updated</span>
                  <span className="detail-value">
                    {new Date(project.updated_at).toLocaleString()}
                  </span>
                </div>
                {project.description && (
                  <div className="detail-item" style={{ gridColumn: '1 / -1' }}>
                    <span className="detail-label">Description</span>
                    <span className="detail-value" style={{ lineHeight: 1.6 }}>
                      {project.description}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Experiments Tab */}
      {activeTab === 'experiments' && (
        <div className="card">
          <div className="card-header">
            <h2>Experiments ({experiments.length})</h2>
            <Link
              to={`/experiments?project_id=${project.id}`}
              className="btn btn-primary btn-sm"
            >
              + New Experiment
            </Link>
          </div>
          <div className="table-container">
            {experiments.length === 0 ? (
              <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                No experiments yet for this project.
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
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {experiments.map((exp) => (
                    <tr key={exp.id}>
                      <td>
                        <Link to={`/experiments/${exp.id}`} className="table-link text-mono">
                          {exp.experiment_code}
                        </Link>
                      </td>
                      <td>{exp.title}</td>
                      <td><StatusBadge status={exp.status} /></td>
                      <td style={{ color: 'var(--color-text-secondary)' }}>
                        {exp.experiment_date
                          ? new Date(exp.experiment_date).toLocaleDateString()
                          : '—'}
                      </td>
                      <td style={{ color: 'var(--color-text-secondary)' }}>
                        {exp.researcher ?? '—'}
                      </td>
                      <td>
                        <Link to={`/experiments/${exp.id}`} className="btn btn-secondary btn-sm">
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

      {/* Parameters Tab */}
      {activeTab === 'parameters' && (
        <div className="card">
          <div className="card-header">
            <h2>Synthesis Parameter Definitions ({activeDefs.length})</h2>
            <button className="btn btn-primary btn-sm" onClick={() => setShowParamModal(true)}>
              ⚙ Manage Definitions
            </button>
          </div>
          <div className="table-container">
            {parameterDefs.length === 0 ? (
              <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                <p style={{ marginBottom: 12 }}>No parameter definitions configured yet for this project.</p>
                <button className="btn btn-primary btn-sm" onClick={() => setShowParamModal(true)}>
                  Configure Parameters
                </button>
              </div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Parameter Name</th>
                    <th>Code</th>
                    <th>Data Type</th>
                    <th>Unit</th>
                    <th>Required</th>
                    <th>Range / Options</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {parameterDefs.map((def) => (
                    <tr key={def.id} style={{ opacity: def.status === 'INACTIVE' ? 0.5 : 1 }}>
                      <td style={{ fontWeight: 600 }}>{def.parameter_name}</td>
                      <td className="text-mono" style={{ fontSize: '0.8125rem' }}>{def.parameter_code}</td>
                      <td>
                        <span className="badge badge-planned" style={{ fontSize: '0.65rem' }}>
                          {def.data_type}
                        </span>
                      </td>
                      <td style={{ color: 'var(--color-text-secondary)' }}>{def.unit ?? '—'}</td>
                      <td>
                        {def.required ? (
                          <span style={{ color: 'var(--color-danger)', fontWeight: 600 }}>Required</span>
                        ) : (
                          <span style={{ color: 'var(--color-text-secondary)' }}>Optional</span>
                        )}
                      </td>
                      <td style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                        {def.data_type === 'NUMBER' && (def.minimum_value !== null || def.maximum_value !== null)
                          ? `${def.minimum_value ?? '—'} to ${def.maximum_value ?? '—'}`
                          : def.data_type === 'ENUM' && def.allowed_values
                          ? def.allowed_values.join(', ')
                          : '—'}
                      </td>
                      <td>
                        <span className={`badge ${def.status === 'ACTIVE' ? 'badge-active' : 'badge-archived'}`}>
                          {def.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Parameter Management Modal */}
      {showParamModal && (
        <ParameterManagementModal
          projectId={project.id}
          definitions={parameterDefs}
          onClose={() => setShowParamModal(false)}
          onUpdated={fetchAll}
        />
      )}
    </div>
  )
}
