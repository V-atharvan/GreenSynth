/**
 * GreenSynth Analytics — ML Dashboard Page (Phase 14–16)
 *
 * Evidence-based ML pipeline: Dataset → Training → Prediction → Validation
 */

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Cpu, Database, ShieldCheck, TrendingUp, BarChart3 } from 'lucide-react'
import { projectService } from '@/services/projectService'
import { mlService, MLDataset, MLModel, MLPrediction } from '@/services/mlService'
import type { ProjectSummary } from '@/types'

export default function MLDashboard() {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [datasets, setDatasets] = useState<MLDataset[]>([])
  const [models, setModels] = useState<MLModel[]>([])
  const [predictions, setPredictions] = useState<MLPrediction[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    projectService.getProjects().then((pList) => {
      setProjects(pList)
      if (pList.length > 0) {
        setSelectedProject(pList[0].id)
      }
    }).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedProject) return
    setLoading(true)

    Promise.all([
      mlService.getDatasets(selectedProject),
      mlService.getModels(),
      mlService.getPredictions(),
    ]).then(([dList, mList, pList]) => {
      setDatasets(dList)
      setModels(mList)
      setPredictions(pList)
    }).catch(console.error).finally(() => setLoading(false))
  }, [selectedProject])

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
        <div className="gs-header-actions">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="gs-select"
            aria-label="Select project"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.project_code} — {p.name}
              </option>
            ))}
          </select>
          <Link to="/ml/datasets/new" className="gs-btn gs-btn-teal">
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
        <div className="gs-metric-card purple">
          <div className="gs-metric-icon purple" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <TrendingUp size={18} />
          </div>
          <div className="gs-metric-value">{predictions.length}</div>
          <div className="gs-metric-label">Predictions Generated</div>
        </div>
      </div>

      {/* Pipeline action tiles */}
      <div className="gs-action-grid">
        <Link to="/ml/datasets/new" className="gs-action-card teal">
          <div className="gs-action-card-icon teal" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Database size={20} />
          </div>
          <div className="gs-action-card-title">1. Build Dataset</div>
          <div className="gs-action-card-desc">
            Extract completed experiments, select features &amp; targets, validate eligibility &amp; eliminate target leakage.
          </div>
          <div className="gs-action-card-link">Build Dataset Wizard →</div>
        </Link>

        <Link to="/ml/training" className="gs-action-card indigo">
          <div className="gs-action-card-icon indigo" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Cpu size={20} />
          </div>
          <div className="gs-action-card-title">2. Model Training &amp; CV</div>
          <div className="gs-action-card-desc">
            Train baseline, linear, Ridge, Random Forest &amp; Gradient Boosting models with cross-validation &amp; diagnostic charts.
          </div>
          <div className="gs-action-card-link">Train Models →</div>
        </Link>

        <Link to="/ml/predict" className="gs-action-card purple">
          <div className="gs-action-card-icon purple" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <BarChart3 size={20} />
          </div>
          <div className="gs-action-card-title">3. Prediction &amp; Bounds</div>
          <div className="gs-action-card-desc">
            Generate property predictions with uncertainty intervals &amp; applicability domain boundary checks.
          </div>
          <div className="gs-action-card-link">Generate Prediction →</div>
        </Link>

        <Link to="/ml/validation" className="gs-action-card emerald">
          <div className="gs-action-card-icon emerald" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShieldCheck size={20} />
          </div>
          <div className="gs-action-card-title">4. Validation Studio</div>
          <div className="gs-action-card-desc">
            Compare predictions against actual laboratory measurements. Track model health, bias, and drift over time.
          </div>
          <div className="gs-action-card-link">Open Validation Studio →</div>
        </Link>
      </div>

      {/* Datasets table */}
      <div className="gs-panel">
        <div className="gs-panel-header">
          <span className="gs-panel-title">Project Datasets</span>
          <Link to="/ml/datasets/new" className="gs-btn gs-btn-outline gs-btn-sm">
            + Add
          </Link>
        </div>

        {loading ? (
          <div className="gs-loading">
            <div className="gs-spinner" />
            Loading datasets…
          </div>
        ) : datasets.length === 0 ? (
          <div className="gs-empty">
            <div className="gs-empty-icon" style={{ display: 'flex', justifyContent: 'center' }}>
              <Database size={32} />
            </div>
            <div className="gs-empty-title">No Datasets Yet</div>
            <div className="gs-empty-text">
              Build your first dataset from completed experiments to begin the ML pipeline.
            </div>
          </div>
        ) : (
          <div className="gs-table-wrapper">
            <table className="gs-table">
              <thead>
                <tr>
                  <th>Dataset Name</th>
                  <th>Target Property</th>
                  <th>Observations</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((d) => (
                  <tr key={d.id}>
                    <td style={{ fontWeight: 600 }}>{d.name}</td>
                    <td>{d.target_property}</td>
                    <td>{d.eligible_count}</td>
                    <td><span className="gs-chip info">READY</span></td>
                    <td>{new Date(d.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Models table */}
      {models.length > 0 && (
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">Trained Models</span>
          </div>
          <div className="gs-table-wrapper">
            <table className="gs-table">
              <thead>
                <tr>
                  <th>Model Name</th>
                  <th>Type</th>
                  <th>Version</th>
                  <th>Target</th>
                  <th>CV MAE</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <tr key={m.id}>
                    <td style={{ fontWeight: 600 }}>{m.name}</td>
                    <td><span className="gs-badge indigo">{m.model_type}</span></td>
                    <td>{m.version}</td>
                    <td style={{ color: '#0d9488' }}>{m.target_property}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.875rem' }}>
                      {m.metrics?.cv_mae != null ? m.metrics.cv_mae.toFixed(4) : '—'}
                    </td>
                    <td>
                      <span className={`gs-chip ${m.status === 'PRODUCTION_CANDIDATE' ? 'production' : m.status === 'RETIRED' ? 'retired' : 'info'}`}>
                        {m.status}
                      </span>
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
