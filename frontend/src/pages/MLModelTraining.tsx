/**
 * GreenSynth Analytics — ML Model Training & Cross-Validation Page
 */

import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Cpu, AlertTriangle, Check, X, FolderKanban } from 'lucide-react'
import { mlService, MLDataset, MLModel } from '@/services/mlService'
import { useProjectContext } from '@/context/ProjectContext'

export default function MLModelTraining() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const preselectedDatasetId = searchParams.get('dataset')

  const { projectId, projectCode, projectName } = useProjectContext()
  const [datasets, setDatasets] = useState<MLDataset[]>([])
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(preselectedDatasetId || '')

  const [targetProperty, setTargetProperty] = useState<string>('band_gap_ev')
  const [cvFolds, setCvFolds] = useState<number>(5)
  const [randomSeed, setRandomSeed] = useState<number>(42)

  const [models, setModels] = useState<MLModel[]>([])
  const [selectedModel, setSelectedModel] = useState<MLModel | null>(null)

  const [loading, setLoading] = useState(false)
  const [training, setTraining] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadDatasets = useCallback(async () => {
    if (!projectId) return
    try {
      const ds = await mlService.getDatasets(projectId)
      setDatasets(ds)
      if (ds.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(ds[0].id)
      }
    } catch (err) {
      console.error('Failed to load datasets for training:', err)
    }
  }, [projectId, selectedDatasetId])

  useEffect(() => {
    loadDatasets()
  }, [loadDatasets])

  const handleRunTraining = async () => {
    if (!selectedDatasetId) return
    setTraining(true)
    setError(null)
    try {
      const res = await mlService.trainModels({
        dataset_id: selectedDatasetId,
        model_types: ['BASELINE', 'RIDGE', 'RANDOM_FOREST', 'GRADIENT_BOOSTING'],
        cv_folds: cvFolds,
        random_seed: randomSeed,
      })
      setModels(res)
      if (res.length > 0) setSelectedModel(res[0])
    } catch (err: any) {
      setError(err?.message || 'Model training failed. Please verify dataset feature values.')
    } finally {
      setTraining(false)
    }
  }

  const handleApprove = async (modelId: string) => {
    try {
      const updated = await mlService.approveModel(modelId)
      setModels(models.map((m) => (m.id === modelId ? updated : m)))
      if (selectedModel?.id === modelId) setSelectedModel(updated)
    } catch (err: any) {
      setError(err?.message || 'Failed to approve model.')
    }
  }

  const handleReject = async (modelId: string) => {
    try {
      const updated = await mlService.rejectModel(modelId)
      setModels(models.map((m) => (m.id === modelId ? updated : m)))
      if (selectedModel?.id === modelId) setSelectedModel(updated)
    } catch (err: any) {
      setError(err?.message || 'Failed to reject model.')
    }
  }

  return (
    <div className="gs-page">
      {/* Header */}
      <div className="gs-page-header">
        <div>
          <div className="gs-page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className="gs-page-title-icon teal" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Cpu size={20} />
            </div>
            Model Training &amp; Cross-Validation Studio
          </div>
          <p className="gs-page-subtitle">
            Train baseline, linear ridge, and tree-based ensemble regressors with k-fold cross validation.
          </p>
        </div>
        <div className="gs-header-actions">
          <button
            onClick={handleRunTraining}
            disabled={training || !selectedDatasetId}
            className="gs-btn gs-btn-teal"
            style={{ fontWeight: 600 }}
          >
            {training ? 'Training Ensembles...' : '▶ Train Models'}
          </button>
        </div>
      </div>

      {error && (
        <div className="gs-alert error" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {/* Config Panel */}
      <div className="gs-panel">
        <div className="gs-panel-header">
          <span className="gs-panel-title">1. Select Dataset &amp; Training Parameters</span>
        </div>
        <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="gs-form-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
            <div className="gs-field">
              <label className="gs-label">Assigned Project</label>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '9px 12px',
                  background: '#f8fafc',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  fontSize: '13px',
                  fontWeight: 600,
                  color: '#0f766e',
                }}
              >
                <FolderKanban size={15} />
                <span>{projectCode ? `${projectCode} — ${projectName || projectCode}` : 'Loading...'}</span>
              </div>
            </div>
            <div className="gs-field">
              <label className="gs-label">Dataset</label>
              <select value={selectedDatasetId} onChange={(e) => setSelectedDatasetId(e.target.value)} className="gs-select">
                {datasets.length === 0 ? (
                  <option value="">No datasets available for project</option>
                ) : (
                  datasets.map((d) => (
                    <option key={d.id} value={d.id}>{d.name} ({d.eligible_count} samples)</option>
                  ))
                )}
              </select>
            </div>
            <div className="gs-field">
              <label className="gs-label">Target Property</label>
              <select value={targetProperty} onChange={(e) => setTargetProperty(e.target.value)} className="gs-select">
                <option value="band_gap_ev">Optical Band Gap Eg (eV)</option>
                <option value="crystallite_size_nm">Crystallite Size D (nm)</option>
                <option value="electrical_conductivity_s_cm">Electrical Conductivity σ (S/cm)</option>
              </select>
            </div>
          </div>

          <div className="gs-form-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <div className="gs-field">
              <label className="gs-label">K-Fold CV Folds</label>
              <input
                type="number"
                min="2"
                max="10"
                value={cvFolds}
                onChange={(e) => setCvFolds(parseInt(e.target.value) || 5)}
                className="gs-input"
              />
            </div>
            <div className="gs-field">
              <label className="gs-label">Random Seed</label>
              <input
                type="number"
                value={randomSeed}
                onChange={(e) => setRandomSeed(parseInt(e.target.value) || 42)}
                className="gs-input"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Models Result Section */}
      {models.length > 0 && (
        <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: '#1e3a5f' }}>
            2. Trained Model Leaderboard &amp; Cross-Validation
          </h2>

          <div className="gs-table-wrap">
            <table className="gs-table">
              <thead>
                <tr>
                  <th>Algorithm</th>
                  <th>CV R² Mean ± Std</th>
                  <th>CV RMSE</th>
                  <th>CV MAE</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <tr key={m.id} style={{ background: selectedModel?.id === m.id ? '#f0fdf4' : undefined }}>
                    <td>
                      <strong>{m.model_type}</strong>
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>ID: {m.id.slice(0, 8)}...</div>
                    </td>
                    <td>
                      {m.metrics?.cv_r2 != null ? m.metrics.cv_r2.toFixed(4) : '—'}
                    </td>
                    <td>{m.metrics?.cv_rmse != null ? m.metrics.cv_rmse.toFixed(4) : '—'}</td>
                    <td>{m.metrics?.cv_mae != null ? m.metrics.cv_mae.toFixed(4) : '—'}</td>
                    <td>
                      <span className={`gs-badge ${m.status === 'PRODUCTION_CANDIDATE' ? 'green' : m.status === 'REJECTED' ? 'red' : 'amber'}`}>
                        {m.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button onClick={() => setSelectedModel(m)} className="gs-btn gs-btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem' }}>
                          Inspect
                        </button>
                        {m.status !== 'PRODUCTION_CANDIDATE' && (
                          <button onClick={() => handleApprove(m.id)} className="gs-btn gs-btn-emerald" style={{ padding: '4px 8px', fontSize: '0.75rem' }} title="Approve for prediction">
                            <Check size={14} />
                          </button>
                        )}
                        {m.status !== 'REJECTED' && (
                          <button onClick={() => handleReject(m.id)} className="gs-btn gs-btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem', color: '#ef4444' }} title="Reject candidate">
                            <X size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
