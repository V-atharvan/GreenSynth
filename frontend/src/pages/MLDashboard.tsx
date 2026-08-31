/**
 * GreenSynth Analytics — ML Dashboard Page (Phase 14–16)
 *
 * Evidence-based ML pipeline: Dataset → Training → Prediction → Validation
 */

import React, { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Cpu, Database, ShieldCheck, TrendingUp, BarChart3, FolderKanban } from 'lucide-react'
import { mlService, MLDataset, MLModel, MLPrediction } from '@/services/mlService'
import { useProjectContext } from '@/context/ProjectContext'

export default function MLDashboard() {
  const { projectId, projectCode, projectName } = useProjectContext()
  const [datasets, setDatasets] = useState<MLDataset[]>([])
  const [models, setModels] = useState<MLModel[]>([])
  const [predictions, setPredictions] = useState<MLPrediction[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  const fetchData = useCallback(async () => {
    if (!projectId) return
    setLoading(true)

    try {
      const [dList, mList, pList] = await Promise.all([
        mlService.getDatasets(projectId),
        mlService.getModels(),
        mlService.getPredictions(),
      ])
      setDatasets(dList)
      setModels(mList)
      setPredictions(pList)
    } catch (err) {
      console.error('Failed to load ML dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const approvedModels = models.filter((m) => m.status === 'PRODUCTION_CANDIDATE')

  return (
    <div className="gs-page">

      {/* Header */}
      <div className="gs-page-header">
        <div>
          <div className="gs-page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className="gs-page-title-icon teal" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Cpu size={20} />
            </div>
            Machine Learning Center
          </div>
          <p className="gs-page-subtitle">
            Evidence-based dataset preparation, model training, validation &amp; uncertainty-quantified predictions.
          </p>
        </div>
        <div className="gs-header-actions" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
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
            <span>{projectCode ? `${projectCode} — ${projectName || projectCode}` : 'Loading project...'}</span>
          </div>
          <Link to="/ml/datasets/new" className="gs-btn gs-btn-teal" style={{ fontWeight: 600 }}>
            + New Dataset
          </Link>
        </div>
      </div>

      {/* Metric cards */}
      <div className="gs-metrics-row">
        <div className="gs-metric-card teal">
          <div className="gs-metric-icon teal" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Database size={18} />
          </div>
          <div className="gs-metric-value">{datasets.length}</div>
          <div className="gs-metric-label">ML Datasets</div>
        </div>
        <div className="gs-metric-card indigo">
          <div className="gs-metric-icon indigo" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Cpu size={18} />
          </div>
          <div className="gs-metric-value">{models.length}</div>
          <div className="gs-metric-label">Trained Models</div>
        </div>
        <div className="gs-metric-card emerald">
          <div className="gs-metric-icon emerald" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShieldCheck size={18} />
          </div>
          <div className="gs-metric-value">{approvedModels.length}</div>
          <div className="gs-metric-label">Approved Candidates</div>
        </div>
        <div className="gs-metric-card amber">
          <div className="gs-metric-icon amber" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <TrendingUp size={18} />
          </div>
          <div className="gs-metric-value">{predictions.length}</div>
          <div className="gs-metric-label">Predictions Made</div>
        </div>
      </div>

      {/* Pipeline steps navigation */}
      <div className="gs-pipeline-nav">
        <Link to="/ml/datasets/new" className="gs-pipeline-step">
          <div className="gs-pipeline-step-num">1</div>
          <div>
            <div className="gs-pipeline-step-title">Dataset Builder</div>
            <div className="gs-pipeline-step-desc">Prepare multi-modal training sets</div>
          </div>
        </Link>
        <Link to="/ml/training" className="gs-pipeline-step">
          <div className="gs-pipeline-step-num">2</div>
          <div>
            <div className="gs-pipeline-step-title">Model Training</div>
            <div className="gs-pipeline-step-desc">Train ensemble regressors</div>
          </div>
        </Link>
        <Link to="/ml/predict" className="gs-pipeline-step">
          <div className="gs-pipeline-step-num">3</div>
          <div>
            <div className="gs-pipeline-step-title">Predict &amp; Uncertainty</div>
            <div className="gs-pipeline-step-desc">Evaluate forward synthesis targets</div>
          </div>
        </Link>
        <Link to="/ml/validation" className="gs-pipeline-step">
          <div className="gs-pipeline-step-num">4</div>
          <div>
            <div className="gs-pipeline-step-title">Validation Studio</div>
            <div className="gs-pipeline-step-desc">Health checks &amp; drift monitoring</div>
          </div>
        </Link>
      </div>

      {/* Main content grid */}
      <div className="gs-grid-2">
        {/* Datasets section */}
        <div className="gs-card">
          <div className="gs-card-header">
            <h3 className="gs-card-title">
              <Database size={16} /> Datasets ({datasets.length})
            </h3>
            <Link to="/ml/datasets/new" className="gs-link">
              + New Dataset
            </Link>
          </div>
          {loading ? (
            <div className="gs-loading-placeholder">Loading datasets...</div>
          ) : datasets.length === 0 ? (
            <div className="gs-empty-placeholder">
              No datasets built for this project yet. Use the Dataset Builder to construct feature matrices.
            </div>
          ) : (
            <div className="gs-table-wrap">
              <table className="gs-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Target</th>
                    <th>Records</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {datasets.map((ds) => (
                    <tr key={ds.id}>
                      <td>
                        <strong>{ds.name}</strong>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                          v{ds.version}
                        </div>
                      </td>
                      <td>{ds.target_property} ({ds.target_unit})</td>
                      <td>{ds.eligible_count}</td>
                      <td>
                        <span className="gs-badge green">{ds.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Models section */}
        <div className="gs-card">
          <div className="gs-card-header">
            <h3 className="gs-card-title">
              <Cpu size={16} /> Trained Models ({models.length})
            </h3>
            <Link to="/ml/training" className="gs-link">
              + Train Model
            </Link>
          </div>
          {loading ? (
            <div className="gs-loading-placeholder">Loading models...</div>
          ) : models.length === 0 ? (
            <div className="gs-empty-placeholder">
              No models trained yet. Go to Model Training to run training jobs.
            </div>
          ) : (
            <div className="gs-table-wrap">
              <table className="gs-table">
                <thead>
                  <tr>
                    <th>Algorithm</th>
                    <th>Target</th>
                    <th>R² Score</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((mod) => (
                    <tr key={mod.id}>
                      <td>
                        <strong>{mod.model_type}</strong>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                          {mod.id.slice(0, 8)}...
                        </div>
                      </td>
                      <td>{mod.target_property}</td>
                      <td>
                        {mod.metrics?.cv_r2 != null ? mod.metrics.cv_r2.toFixed(4) : '—'}
                      </td>
                      <td>
                        <span className={`gs-badge ${mod.status === 'PRODUCTION_CANDIDATE' ? 'green' : 'amber'}`}>
                          {mod.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
