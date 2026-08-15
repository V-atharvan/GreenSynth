/**
 * GreenSynth Analytics — ML Model Training & Cross-Validation Page
 */

import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Cpu, AlertTriangle, Check, X } from 'lucide-react'
import { projectService } from '@/services/projectService'
import type { ProjectSummary } from '@/types'
import { mlService, MLDataset, MLModel } from '@/services/mlService'

export default function MLModelTraining() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const preselectedDatasetId = searchParams.get('dataset')

  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')
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

  useEffect(() => {
    projectService.getProjects().then((data) => {
      setProjects(data)
      if (data.length > 0) setSelectedProjectId(data[0].id)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedProjectId) return
    mlService.getDatasets(selectedProjectId).then((ds) => {
      setDatasets(ds)
      if (ds.length > 0 && !selectedDatasetId) setSelectedDatasetId(ds[0].id)
    }).catch(() => {})
  }, [selectedProjectId])

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
      setError(err?.response?.data?.detail || err?.message || 'Training failed.')
    } finally {
      setTraining(false)
    }
  }

  const handleApproveModel = async (modelId: string) => {
    try {
      const updated = await mlService.approveModel(modelId)
      setModels((prev) => prev.map((m) => (m.id === modelId ? updated : m)))
      if (selectedModel?.id === modelId) setSelectedModel(updated)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to approve model.')
    }
  }

  const handleRejectModel = async (modelId: string) => {
    try {
      const updated = await mlService.rejectModel(modelId)
      setModels((prev) => prev.map((m) => (m.id === modelId ? updated : m)))
      if (selectedModel?.id === modelId) setSelectedModel(updated)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to reject model.')
    }
  }

  return (
    <div className="gs-ml-container">
      {/* Header */}
      <div className="gs-page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button onClick={() => navigate('/ml')} className="gs-btn gs-btn-outline" style={{ padding: '8px 12px' }}>← Back</button>
          <div>
            <div className="gs-page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div className="gs-page-title-icon indigo" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Cpu size={20} />
              </div>
              Model Training &amp; Cross-Validation
            </div>
            <p className="gs-page-subtitle">Train baseline, linear, Ridge, Random Forest, &amp; Gradient Boosting models with K-fold cross validation.</p>
          </div>
        </div>
      </div>

      {error && <div className="gs-alert error" style={{ display: 'flex', alignItems: 'center', gap: 8 }}><AlertTriangle size={16} /> {error}</div>}

      {/* Config Panel */}
      <div className="gs-panel">
        <div className="gs-panel-header">
          <span className="gs-panel-title">1. Select Dataset &amp; Training Parameters</span>
        </div>
        <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="gs-form-row">
            <div className="gs-field">
              <label className="gs-label">Project</label>
              <select value={selectedProjectId} onChange={(e) => setSelectedProjectId(e.target.value)} className="gs-select">
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.project_code} — {p.name}</option>
                ))}
              </select>
            </div>
            <div className="gs-field">
              <label className="gs-label">Dataset</label>
              <select value={selectedDatasetId} onChange={(e) => setSelectedDatasetId(e.target.value)} className="gs-select">
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>{d.name} ({d.eligible_count} samples)</option>
                ))}
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

          <div className="gs-form-row">
            <div className="gs-field">
              <label className="gs-label">CV Folds (K)</label>
              <input type="number" min={2} max={10} value={cvFolds} onChange={(e) => setCvFolds(parseInt(e.target.value) || 5)} className="gs-input" />
            </div>
            <div className="gs-field">
              <label className="gs-label">Random Seed</label>
              <input type="number" value={randomSeed} onChange={(e) => setRandomSeed(parseInt(e.target.value) || 42)} className="gs-input" />
            </div>
            <div className="gs-field" style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button onClick={handleRunTraining} disabled={training || !selectedDatasetId} className="gs-btn gs-btn-indigo" style={{ width: '100%', justifyContent: 'center' }}>
                {training ? 'Training Models…' : 'Run Training & Cross Validation'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Model Comparison Table */}
      {models.length > 0 && (
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">2. Model Performance &amp; Comparison</span>
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
                            <button onClick={() => handleApproveModel(m.id)} className="gs-btn gs-btn-emerald gs-btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                              <Check size={14} /> Approve
                            </button>
                          )}
                          {m.status !== 'REJECTED' && (
                            <button onClick={() => handleRejectModel(m.id)} className="gs-btn gs-btn-danger gs-btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                              <X size={14} /> Reject
                            </button>
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
            <span className="gs-panel-title">Diagnostics: {selectedModel.name}</span>
            <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}>
              scikit-learn {selectedModel.library_versions?.['scikit-learn']}
            </span>
          </div>
          <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {selectedModel.metrics.overfitting_warning && (
              <div className="gs-alert warning" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle size={16} /> Potential Overfitting: Train R² ({selectedModel.metrics.train_r2}) significantly exceeds CV R² ({selectedModel.metrics.cv_r2}).
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
