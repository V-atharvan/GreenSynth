/**
 * GreenSynth Analytics — ML Model Training & Cross-Validation Page
 */

import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { projectService } from '@/services/projectService'
import type { ProjectSummary } from '@/types'
import { mlService, MLDataset, MLModel } from '@/services/mlService'

const ALGO_OPTIONS = [
  { id: 'MEAN_BASELINE', label: 'Mean Baseline' },
  { id: 'LINEAR_REGRESSION', label: 'Linear Regression' },
  { id: 'RIDGE', label: 'Ridge Regression' },
  { id: 'RANDOM_FOREST', label: 'Random Forest' },
  { id: 'GRADIENT_BOOSTING', label: 'Gradient Boosting' },
]

export default function MLModelTraining() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [datasets, setDatasets] = useState<MLDataset[]>([])
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('')
  const [selectedModels, setSelectedModels] = useState<string[]>(['MEAN_BASELINE','LINEAR_REGRESSION','RIDGE','RANDOM_FOREST','GRADIENT_BOOSTING'])
  const [scaling, setScaling] = useState<string>('STANDARD')
  const [cvFolds, setCvFolds] = useState<number>(5)
  const [randomSeed, setRandomSeed] = useState<number>(42)
  const [training, setTraining] = useState<boolean>(false)
  const [models, setModels] = useState<MLModel[]>([])
  const [selectedModel, setSelectedModel] = useState<MLModel | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    projectService.getAll().then((p) => { setProjects(p); if (p.length > 0) setSelectedProject(p[0].id) }).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedProject) return
    mlService.getDatasets(selectedProject).then((d) => {
      setDatasets(d)
      if (d.length > 0) setSelectedDatasetId(d[0].id)
    }).catch(console.error)
  }, [selectedProject])

  useEffect(() => {
    if (!selectedDatasetId) return
    mlService.getModels(selectedDatasetId).then((m) => {
      setModels(m)
      if (m.length > 0) setSelectedModel(m[0])
    }).catch(console.error)
  }, [selectedDatasetId])

  const handleToggle = (id: string) => {
    if (selectedModels.includes(id)) {
      if (selectedModels.length > 1) setSelectedModels(selectedModels.filter((m) => m !== id))
    } else {
      setSelectedModels([...selectedModels, id])
    }
  }

  const handleRunTraining = async () => {
    if (!selectedDatasetId) return
    setTraining(true)
    setError(null)
    try {
      const trained = await mlService.trainModels({ dataset_id: selectedDatasetId, model_types: selectedModels, scaling, cv_folds: cvFolds, random_seed: randomSeed })
      setModels(trained)
      if (trained.length > 0) setSelectedModel(trained[0])
    } catch (err: any) {
      setError(err?.message || 'Model training failed.')
    } finally {
      setTraining(false)
    }
  }

  const handleApproveModel = async (modelId: string) => {
    try {
      const updated = await mlService.approveModel(modelId, 'Researcher verified CV metrics & diagnostic performance')
      setModels(models.map((m) => (m.id === modelId ? updated : m)))
      if (selectedModel?.id === modelId) setSelectedModel(updated)
    } catch (err) { console.error('Approve error:', err) }
  }

  const handleRejectModel = async (modelId: string) => {
    try {
      const updated = await mlService.rejectModel(modelId, 'High validation error or poor generalization')
      setModels(models.map((m) => (m.id === modelId ? updated : m)))
      if (selectedModel?.id === modelId) setSelectedModel(updated)
    } catch (err) { console.error('Reject error:', err) }
  }

  return (
    <div className="gs-page">

      {/* Header */}
      <div className="gs-page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button onClick={() => navigate('/ml')} className="gs-btn gs-btn-outline" style={{ padding: '8px 12px' }}>← Back</button>
          <div>
            <div className="gs-page-title">
              <div className="gs-page-title-icon indigo">🧠</div>
              Model Training &amp; Cross-Validation
            </div>
            <p className="gs-page-subtitle">Train baseline, linear, Ridge, Random Forest, &amp; Gradient Boosting models with K-fold cross validation.</p>
          </div>
        </div>
      </div>

      {error && <div className="gs-alert error">⚠️ {error}</div>}

      {/* Config Panel */}
      <div className="gs-panel">
        <div className="gs-panel-header">
          <span className="gs-panel-title">1. Select Dataset &amp; Training Parameters</span>
        </div>
        <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="gs-form-row">
            <div className="gs-field">
              <label className="gs-label">Project</label>
              <select value={selectedProject} onChange={(e) => setSelectedProject(e.target.value)} className="gs-input">
                {projects.map((p) => <option key={p.id} value={p.id}>{p.project_code} — {p.name}</option>)}
              </select>
            </div>
            <div className="gs-field">
              <label className="gs-label">ML Dataset</label>
              <select value={selectedDatasetId} onChange={(e) => setSelectedDatasetId(e.target.value)} className="gs-input">
                {datasets.length === 0 && <option value="">— No datasets —</option>}
                {datasets.map((d) => <option key={d.id} value={d.id}>{d.name} ({d.eligible_count} samples)</option>)}
              </select>
            </div>
            <div className="gs-field">
              <label className="gs-label">Feature Scaling</label>
              <select value={scaling} onChange={(e) => setScaling(e.target.value)} className="gs-input">
                <option value="STANDARD">StandardScaler (Mean=0, Std=1)</option>
                <option value="NONE">Passthrough (None)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="gs-label" style={{ marginBottom: 10, display: 'block' }}>Candidate Algorithms</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {ALGO_OPTIONS.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => handleToggle(m.id)}
                  className="gs-btn"
                  style={{
                    background: selectedModels.includes(m.id) ? '#e0e7ff' : 'var(--color-bg)',
                    color: selectedModels.includes(m.id) ? '#3730a3' : 'var(--color-text-secondary)',
                    border: selectedModels.includes(m.id) ? '1.5px solid #a5b4fc' : '1px solid var(--color-border)',
                    fontWeight: selectedModels.includes(m.id) ? 700 : 500,
                  }}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <div className="gs-form-row" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
            <div className="gs-field">
              <label className="gs-label">CV Folds</label>
              <input type="number" value={cvFolds} onChange={(e) => setCvFolds(parseInt(e.target.value) || 5)} min={2} max={20} className="gs-input" />
            </div>
            <div className="gs-field">
              <label className="gs-label">Random Seed</label>
              <input type="number" value={randomSeed} onChange={(e) => setRandomSeed(parseInt(e.target.value) || 42)} className="gs-input" />
            </div>
            <div className="gs-field" style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button onClick={handleRunTraining} disabled={training || !selectedDatasetId} className="gs-btn gs-btn-indigo" style={{ width: '100%', justifyContent: 'center' }}>
                {training ? '⏳ Training Models…' : '🚀 Run Training & Cross Validation'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Model Comparison Table */}
      {models.length > 0 && (
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">📊 2. Model Performance &amp; Comparison</span>
            <span className="gs-chip info">{models.length} models trained</span>
          </div>
          <div className="gs-table-wrapper">
            <table className="gs-table">
              <thead>
                <tr>
                  <th>Model Name</th>
                  <th>Algorithm</th>
                  <th>CV MAE</th>
                  <th>CV RMSE</th>
                  <th>CV R²</th>
                  <th>Train R²</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => {
                  const isSelected = selectedModel?.id === m.id
                  const cvR2 = m.metrics.cv_r2
                  return (
                    <tr key={m.id} onClick={() => setSelectedModel(m)} style={{ cursor: 'pointer', background: isSelected ? '#eff6ff' : undefined }}>
                      <td style={{ fontWeight: 600 }}>{m.name}</td>
                      <td><span className="gs-badge indigo">{m.model_type}</span></td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{m.metrics.cv_mae}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{m.metrics.cv_rmse}</td>
                      <td style={{ fontWeight: 700, color: cvR2 >= 0.7 ? '#059669' : 'var(--color-text)' }}>{m.metrics.cv_r2}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{m.metrics.train_r2}</td>
                      <td>
                        <span className={`gs-chip ${m.status === 'PRODUCTION_CANDIDATE' ? 'production' : m.status === 'REJECTED' ? 'critical' : 'info'}`}>
                          {m.status}
                        </span>
                      </td>
                      <td>
                        <span style={{ display: 'inline-flex', gap: 6 }} onClick={(e) => e.stopPropagation()}>
                          {m.status !== 'PRODUCTION_CANDIDATE' && (
                            <button onClick={() => handleApproveModel(m.id)} className="gs-btn gs-btn-emerald gs-btn-sm">✓ Approve</button>
                          )}
                          {m.status !== 'REJECTED' && (
                            <button onClick={() => handleRejectModel(m.id)} className="gs-btn gs-btn-danger gs-btn-sm">✗ Reject</button>
                          )}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Selected Model Diagnostics */}
      {selectedModel && (
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">🔍 Diagnostics: {selectedModel.name}</span>
            <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}>
              scikit-learn {selectedModel.library_versions?.['scikit-learn']}
            </span>
          </div>
          <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {selectedModel.metrics.overfitting_warning && (
              <div className="gs-alert warning">
                ⚠️ Potential Overfitting: Train R² ({selectedModel.metrics.train_r2}) significantly exceeds CV R² ({selectedModel.metrics.cv_r2}).
              </div>
            )}

            {selectedModel.feature_importance && (
              <div>
                <div className="gs-label" style={{ marginBottom: 10 }}>Feature Importance / Coefficients</div>
                <div className="gs-param-grid">
                  {Object.entries(selectedModel.feature_importance).map(([fname, val]) => (
                    <div key={fname} className="gs-param-item">
                      <div className="gs-param-name">{fname}</div>
                      <div className="gs-param-value" style={{ color: '#0d9488' }}>{(val as number).toFixed(4)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedModel.metrics.diagnostics?.actual_vs_predicted && (
              <div>
                <div className="gs-label" style={{ marginBottom: 10 }}>Actual vs. Predicted Observations</div>
                <div className="gs-table-wrapper" style={{ maxHeight: 240, overflowY: 'auto' }}>
                  <table className="gs-table">
                    <thead>
                      <tr>
                        <th>Sample ID</th>
                        <th>Actual ({selectedModel.target_unit})</th>
                        <th>Predicted ({selectedModel.target_unit})</th>
                        <th>Residual</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedModel.metrics.diagnostics.actual_vs_predicted.map((pt: any, i: number) => {
                        const res = pt.actual - pt.predicted
                        return (
                          <tr key={i}>
                            <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary)' }}>{pt.sample_id}</td>
                            <td style={{ fontWeight: 600, color: '#059669', fontFamily: 'var(--font-mono)' }}>{pt.actual}</td>
                            <td style={{ fontWeight: 600, color: '#0d9488', fontFamily: 'var(--font-mono)' }}>{pt.predicted}</td>
                            <td style={{ fontFamily: 'var(--font-mono)' }}>{res.toFixed(4)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
