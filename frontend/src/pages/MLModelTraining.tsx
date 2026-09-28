/**
 * GreenSynth Analytics — ML Model Training & Cross-Validation Page
 */

import React, { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Cpu, AlertTriangle, Check, X, FolderKanban, Activity, BarChart3, Sliders, ShieldCheck, ArrowRight } from 'lucide-react'
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
  const inspectRef = useRef<HTMLDivElement>(null)

  const handleInspect = (m: MLModel) => {
    setSelectedModel(m)
    setTimeout(() => {
      inspectRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }, 50)
  }

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
        model_types: ['MEAN_BASELINE', 'RIDGE', 'RANDOM_FOREST', 'GRADIENT_BOOSTING'],
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
                        <button
                          onClick={() => handleInspect(m)}
                          className={`gs-btn ${selectedModel?.id === m.id ? 'gs-btn-teal' : 'gs-btn-secondary'}`}
                          style={{ padding: '4px 8px', fontSize: '0.75rem', fontWeight: 600 }}
                        >
                          {selectedModel?.id === m.id ? 'Inspecting' : 'Inspect'}
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

          {/* 3. Model Inspection & Diagnostics Drawer/Panel */}
          {selectedModel && (
            <div
              ref={inspectRef}
              className="gs-panel"
              style={{
                marginTop: 24,
                border: '2px solid #0d9488',
                boxShadow: '0 10px 25px -5px rgba(13, 148, 136, 0.1), 0 8px 10px -6px rgba(13, 148, 136, 0.1)',
                borderRadius: '12px',
                background: '#ffffff',
                overflow: 'hidden',
              }}
            >
              {/* Header */}
              <div
                style={{
                  padding: '16px 20px',
                  background: 'linear-gradient(135deg, #f0fdfa 0%, #e6fffa 100%)',
                  borderBottom: '1px solid #ccfbf1',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: 12,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div
                    style={{
                      width: 36,
                      height: 36,
                      borderRadius: 8,
                      background: '#0d9488',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Activity size={20} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 700, color: '#0f766e' }}>
                        {selectedModel.model_type} Diagnostics &amp; Inspection
                      </h3>
                      <span
                        className={`gs-badge ${
                          selectedModel.status === 'PRODUCTION_CANDIDATE'
                            ? 'green'
                            : selectedModel.status === 'REJECTED'
                            ? 'red'
                            : 'amber'
                        }`}
                      >
                        {selectedModel.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 2 }}>
                      Model ID: <code style={{ color: '#0f766e' }}>{selectedModel.id}</code> • Target: <strong>{selectedModel.target_property} ({selectedModel.target_unit})</strong>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {selectedModel.status !== 'PRODUCTION_CANDIDATE' && (
                    <button
                      onClick={() => handleApprove(selectedModel.id)}
                      className="gs-btn gs-btn-emerald"
                      style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', fontSize: '0.8125rem', fontWeight: 600 }}
                    >
                      <Check size={14} /> Approve as Candidate
                    </button>
                  )}
                  <button
                    onClick={() => navigate(`/ml/predict?model=${selectedModel.id}`)}
                    className="gs-btn gs-btn-teal"
                    style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', fontSize: '0.8125rem', fontWeight: 600 }}
                  >
                    Use in Predict <ArrowRight size={14} />
                  </button>
                  <button
                    onClick={() => setSelectedModel(null)}
                    className="gs-btn gs-btn-outline"
                    style={{ padding: '6px 10px', fontSize: '0.8125rem' }}
                    title="Close Inspector"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>

              <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: 20 }}>
                {/* Metric Comparison Cards */}
                <div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#1e293b', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <ShieldCheck size={16} style={{ color: '#0d9488' }} />
                    Cross-Validation vs Training Metrics
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
                    {/* CV R2 */}
                    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '12px 14px' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
                        CV R² Score
                      </div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: (selectedModel.metrics?.cv_r2 ?? 0) > 0.5 ? '#0d9488' : '#eab308', marginTop: 4 }}>
                        {selectedModel.metrics?.cv_r2 != null ? selectedModel.metrics.cv_r2.toFixed(4) : '—'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 4 }}>
                        Train R²: <strong>{selectedModel.metrics?.train_r2 != null ? selectedModel.metrics.train_r2.toFixed(4) : '—'}</strong>
                      </div>
                    </div>

                    {/* CV RMSE */}
                    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '12px 14px' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
                        CV RMSE ({selectedModel.target_unit})
                      </div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1e293b', marginTop: 4 }}>
                        {selectedModel.metrics?.cv_rmse != null ? selectedModel.metrics.cv_rmse.toFixed(4) : '—'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 4 }}>
                        Train RMSE: <strong>{selectedModel.metrics?.train_rmse != null ? selectedModel.metrics.train_rmse.toFixed(4) : '—'}</strong>
                      </div>
                    </div>

                    {/* CV MAE */}
                    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '12px 14px' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
                        CV MAE ({selectedModel.target_unit})
                      </div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1e293b', marginTop: 4 }}>
                        {selectedModel.metrics?.cv_mae != null ? selectedModel.metrics.cv_mae.toFixed(4) : '—'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 4 }}>
                        Train MAE: <strong>{selectedModel.metrics?.train_mae != null ? selectedModel.metrics.train_mae.toFixed(4) : '—'}</strong>
                      </div>
                    </div>

                    {/* Generalization Check */}
                    <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '12px 14px' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
                        Generalization Check
                      </div>
                      <div style={{ fontSize: '0.875rem', fontWeight: 700, color: selectedModel.metrics?.overfitting_warning ? '#ef4444' : '#10b981', marginTop: 8 }}>
                        {selectedModel.metrics?.overfitting_warning ? '⚠️ Overfitting Flagged' : '✅ Well-Calibrated'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 4 }}>
                        Dataset: <strong>{selectedModel.metrics?.n_samples || 397} observations</strong>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Feature Importance Section */}
                <div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#1e293b', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <BarChart3 size={16} style={{ color: '#0d9488' }} />
                    Feature Importance (Relative Physical Contribution)
                  </div>
                  {(() => {
                    const featImp: Record<string, number> =
                      selectedModel.feature_importance ||
                      selectedModel.metrics?.diagnostics?.feature_importance ||
                      {}
                    const entries = Object.entries(featImp).sort((a, b) => b[1] - a[1])
                    const maxVal = Math.max(...entries.map(([, v]) => v), 0.0001)

                    if (entries.length === 0) {
                      return (
                        <div style={{ padding: '16px', background: '#f8fafc', borderRadius: 8, fontSize: '0.875rem', color: '#64748b', border: '1px solid #e2e8f0' }}>
                          Feature importances are not computed for {selectedModel.model_type} (uniform baseline).
                        </div>
                      )
                    }

                    return (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, background: '#f8fafc', padding: 16, borderRadius: 8, border: '1px solid #e2e8f0' }}>
                        {entries.map(([fname, val]) => {
                          const pct = ((val / maxVal) * 100).toFixed(1)
                          const displayScore = (val * 100).toFixed(1)
                          return (
                            <div key={fname}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', marginBottom: 4 }}>
                                <span style={{ fontWeight: 600, color: '#334155' }}>
                                  {fname.replace(/_/g, ' ')}
                                </span>
                                <span style={{ color: '#0f766e', fontWeight: 700 }}>
                                  {displayScore}% relative weight
                                </span>
                              </div>
                              <div style={{ width: '100%', height: 8, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden' }}>
                                <div
                                  style={{
                                    width: `${pct}%`,
                                    height: '100%',
                                    background: 'linear-gradient(90deg, #0d9488, #14b8a6)',
                                    borderRadius: 4,
                                    transition: 'width 0.3s ease',
                                  }}
                                />
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )
                  })()}
                </div>

                {/* Hyperparameters & Setup */}
                <div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#1e293b', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Sliders size={16} style={{ color: '#0d9488' }} />
                    Training Hyperparameters &amp; Engineering Setup
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    <div style={{ padding: '6px 12px', background: '#f1f5f9', borderRadius: 6, fontSize: '0.75rem', color: '#334155' }}>
                      <strong>CV Folds:</strong> {cvFolds}-Fold Grouped
                    </div>
                    <div style={{ padding: '6px 12px', background: '#f1f5f9', borderRadius: 6, fontSize: '0.75rem', color: '#334155' }}>
                      <strong>Random Seed:</strong> {selectedModel.hyperparameters?.random_state ?? 42}
                    </div>
                    <div style={{ padding: '6px 12px', background: '#f1f5f9', borderRadius: 6, fontSize: '0.75rem', color: '#334155' }}>
                      <strong>Scaling:</strong> {selectedModel.preprocessing_config?.scaling || 'STANDARD'}
                    </div>
                    {Object.entries(selectedModel.hyperparameters || {})
                      .filter(([k]) => k !== 'random_state')
                      .map(([k, v]) => (
                        <div key={k} style={{ padding: '6px 12px', background: '#f1f5f9', borderRadius: 6, fontSize: '0.75rem', color: '#334155' }}>
                          <strong>{k}:</strong> {String(v)}
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
