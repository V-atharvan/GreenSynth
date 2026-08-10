/**
 * GreenSynth Analytics — ML Dataset Builder Page
 */

import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Database, Plus, Trash2, CheckCircle2, AlertCircle, ArrowLeft } from 'lucide-react'
import { projectService } from '@/services/projectService'
import type { ProjectSummary } from '@/types'
import { mlService, MLDataset, MLDatasetFeatureSpec, MLDatasetRecord } from '@/services/mlService'

export default function MLDatasetBuilder() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [datasetName, setDatasetName] = useState<string>('CuO Conductivity Dataset')
  const [description, setDescription] = useState<string>('Training dataset for CuO semiconductor conductivity')
  const [targetProperty, setTargetProperty] = useState<string>('Electrical Conductivity')
  const [targetUnit, setTargetUnit] = useState<string>('S/cm')
  const [targetType, setTargetType] = useState<string>('CALCULATED')

  const [features, setFeatures] = useState<MLDatasetFeatureSpec[]>([
    { feature_name: 'substrate_temperature', source_parameter: 'substrate_temperature', unit: '°C', data_type: 'NUMBER' },
    { feature_name: 'spray_rate', source_parameter: 'spray_rate', unit: 'mL/min', data_type: 'NUMBER' },
  ])

  const [building, setBuilding] = useState<boolean>(false)
  const [createdDataset, setCreatedDataset] = useState<MLDataset | null>(null)
  const [datasetRecords, setDatasetRecords] = useState<MLDatasetRecord[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadProjects() {
      try {
        const projs = await projectService.getAll()
        setProjects(projs)
        if (projs.length > 0) {
          setSelectedProject(projs[0].id)
        }
      } catch (err) {
        console.error('Failed to load projects:', err)
      }
    }
    loadProjects()
  }, [])

  const handleAddFeature = () => {
    setFeatures([
      ...features,
      { feature_name: `feature_${features.length + 1}`, source_parameter: `param_${features.length + 1}`, unit: 'a.u.', data_type: 'NUMBER' },
    ])
  }

  const handleRemoveFeature = (index: number) => {
    setFeatures(features.filter((_, i) => i !== index))
  }

  const handleFeatureChange = (index: number, field: keyof MLDatasetFeatureSpec, value: string) => {
    const updated = [...features]
    updated[index] = { ...updated[index], [field]: value }
    setFeatures(updated)
  }

  const handleBuildDataset = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedProject) return
    setBuilding(true)
    setError(null)

    try {
      const ds = await mlService.createDataset({
        project_id: selectedProject,
        name: datasetName,
        description,
        target_property: targetProperty,
        target_type: targetType,
        target_unit: targetUnit,
        features,
      })
      setCreatedDataset(ds)

      const recs = await mlService.getDatasetRecords(ds.id)
      setDatasetRecords(recs)
    } catch (err: any) {
      console.error('Build dataset error:', err)
      setError(err?.message || 'Failed to assemble dataset.')
    } finally {
      setBuilding(false)
    }
  }

  return (
    <div className="gs-page">
      {/* Header */}
      <div className="gs-page-header">
        <div>
          <div className="gs-page-title">
            <button
              onClick={() => navigate('/ml')}
              className="btn btn-secondary btn-icon"
              style={{ marginRight: 8 }}
              title="Back to Machine Learning Studio"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>

            <div className="gs-page-title-icon teal">
              <Database className="w-5 h-5" />
            </div>
            <span>Dataset Builder Wizard</span>
          </div>
          <div className="gs-page-subtitle">
            Formulate an immutable ML dataset from completed experimental observations.
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Dataset Form Card */}
      <form onSubmit={handleBuildDataset} className="card">
        <div className="card-header">
          <h2>1. Target & Project Configuration</h2>
        </div>

        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label required">Target Project</label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="form-control"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.project_code} — {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label required">Dataset Name</label>
              <input
                type="text"
                value={datasetName}
                onChange={(e) => setDatasetName(e.target.value)}
                required
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label className="form-label required">Target Property</label>
              <input
                type="text"
                value={targetProperty}
                onChange={(e) => setTargetProperty(e.target.value)}
                required
                placeholder="e.g. Electrical Conductivity"
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label className="form-label required">Target Unit</label>
              <input
                type="text"
                value={targetUnit}
                onChange={(e) => setTargetUnit(e.target.value)}
                required
                placeholder="e.g. S/cm"
                className="form-control"
              />
            </div>
          </div>

          <h2 style={{ fontSize: '1rem', fontWeight: 600, borderTop: '1px solid var(--color-border-light)', paddingTop: 16 }}>
            2. Input Feature Definitions
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {features.map((feat, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'var(--color-bg)', padding: '12px 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-light)' }}>
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ fontSize: '0.75rem', marginBottom: 2 }}>Feature Name</label>
                  <input
                    type="text"
                    value={feat.feature_name}
                    onChange={(e) => handleFeatureChange(idx, 'feature_name', e.target.value)}
                    placeholder="Feature Name"
                    className="form-control"
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="form-label" style={{ fontSize: '0.75rem', marginBottom: 2 }}>Source Parameter Code</label>
                  <input
                    type="text"
                    value={feat.source_parameter}
                    onChange={(e) => handleFeatureChange(idx, 'source_parameter', e.target.value)}
                    placeholder="Source Parameter Code"
                    className="form-control"
                  />
                </div>
                <div style={{ width: 120 }}>
                  <label className="form-label" style={{ fontSize: '0.75rem', marginBottom: 2 }}>Unit</label>
                  <input
                    type="text"
                    value={feat.unit}
                    onChange={(e) => handleFeatureChange(idx, 'unit', e.target.value)}
                    placeholder="Unit"
                    className="form-control"
                  />
                </div>
                {features.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveFeature(idx)}
                    className="btn btn-danger btn-sm"
                    style={{ marginTop: 18 }}
                    title="Remove feature"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}

            <div>
              <button
                type="button"
                onClick={handleAddFeature}
                className="btn btn-secondary btn-sm"
              >
                <Plus className="w-4 h-4" /> Add Input Feature
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid var(--color-border-light)', paddingTop: 16 }}>
            <button
              type="submit"
              disabled={building}
              className="btn btn-primary"
            >
              {building ? 'Assembling Dataset...' : 'Build & Validate Dataset'}
            </button>
          </div>
        </div>
      </form>

      {/* Dataset Preview */}
      {createdDataset && (
        <div className="card">
          <div className="card-header">
            <div>
              <h2 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                Dataset Created: {createdDataset.name} (v{createdDataset.version})
              </h2>
              <p className="text-muted" style={{ fontSize: '0.8125rem', marginTop: 2 }}>
                Target Property: <strong>{createdDataset.target_property}</strong> ({createdDataset.target_unit})
              </p>
            </div>
            <button
              onClick={() => navigate('/ml/training')}
              className="btn btn-primary btn-sm"
            >
              Proceed to Model Training →
            </button>
          </div>

          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="gs-metrics-row">
              <div className="gs-metric-card emerald">
                <span className="gs-metric-label">Eligible Records</span>
                <span className="gs-metric-value">{createdDataset.eligible_count}</span>
              </div>
              <div className="gs-metric-card amber">
                <span className="gs-metric-label">Excluded Records</span>
                <span className="gs-metric-value">{createdDataset.excluded_count}</span>
              </div>
              <div className="gs-metric-card teal">
                <span className="gs-metric-label">Dataset Status</span>
                <span className="gs-metric-value" style={{ fontSize: '1.25rem' }}>{createdDataset.status}</span>
              </div>
            </div>

            {/* Record Preview Table */}
            <div>
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: 12 }}>Record Preview & Eligibility</h3>
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Experiment ID</th>
                      <th>Sample ID</th>
                      {features.map((f) => (
                        <th key={f.feature_name}>{f.feature_name}</th>
                      ))}
                      <th>Target ({createdDataset.target_unit})</th>
                      <th>Status</th>
                      <th>Exclusion Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {datasetRecords.map((r) => (
                      <tr key={r.id} style={{ background: r.is_eligible ? undefined : 'var(--color-danger-bg)' }}>
                        <td className="text-mono">{r.experiment_id.substring(0, 8)}...</td>
                        <td className="text-mono">{r.sample_id.substring(0, 8)}...</td>
                        {features.map((f) => (
                          <td key={f.feature_name}>
                            {r.feature_values[f.feature_name] ?? 'N/A'}
                          </td>
                        ))}
                        <td style={{ fontWeight: 600, color: 'var(--color-primary)' }}>{r.target_value ?? 'N/A'}</td>
                        <td>
                          {r.is_eligible ? (
                            <span className="badge badge-active">Eligible</span>
                          ) : (
                            <span className="badge badge-failed">Excluded</span>
                          )}
                        </td>
                        <td className="text-muted">{r.exclusion_reason ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
