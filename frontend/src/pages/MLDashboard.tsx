/**
 * GreenSynth Analytics — ML Dashboard Page (Phase 14–16)
 *
 * Evidence-based ML pipeline: Dataset → Training → Prediction → Validation
 */

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { projectService } from '@/services/projectService'
import type { ProjectSummary } from '@/types'
import { mlService, MLDataset, MLModel, MLPrediction } from '@/services/mlService'

export default function MLDashboard() {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [datasets, setDatasets] = useState<MLDataset[]>([])
  const [models, setModels] = useState<MLModel[]>([])
  const [predictions, setPredictions] = useState<MLPrediction[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    async function loadInitial() {
      try {
        const projs = await projectService.getAll()
        setProjects(projs)
        if (projs.length > 0) setSelectedProject(projs[0].id)
      } catch (err) {
        console.error('Failed to load projects:', err)
      } finally {
        setLoading(false)
      }
    }
    loadInitial()
  }, [])

  useEffect(() => {
    if (!selectedProject) return
    async function loadMLData() {
      setLoading(true)
      try {
        const [dsList, mList, pList] = await Promise.all([
          mlService.getDatasets(selectedProject),
          mlService.getModels(),
          mlService.getPredictions(),
        ])
        setDatasets(dsList)
        setModels(mList)
        setPredictions(pList)
      } catch (err) {
        console.error('Failed to load ML data:', err)
      } finally {
        setLoading(false)
      }
    }
    loadMLData()
  }, [selectedProject])

  const approvedModels = models.filter((m) => m.status === 'PRODUCTION_CANDIDATE')

  return (
    <div className="gs-page">

      {/* Header */}
      <div className="gs-page-header">
        <div>
          <div className="gs-page-title">
            <div className="gs-page-title-icon teal">🤖</div>
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
            ＋ New Dataset
          </Link>
        </div>
      </div>

      {/* Metric cards */}
      <div className="gs-metrics-row">
        <div className="gs-metric-card teal">
          <div className="gs-metric-icon teal">🗄️</div>
          <div className="gs-metric-value">{datasets.length}</div>
          <div className="gs-metric-label">ML Datasets</div>
        </div>
        <div className="gs-metric-card indigo">
          <div className="gs-metric-icon indigo">🧠</div>
          <div className="gs-metric-value">{models.length}</div>
          <div className="gs-metric-label">Trained Models</div>
        </div>
        <div className="gs-metric-card emerald">
          <div className="gs-metric-icon emerald">✅</div>
          <div className="gs-metric-value">{approvedModels.length}</div>
          <div className="gs-metric-label">Approved Candidates</div>
        </div>
        <div className="gs-metric-card purple">
          <div className="gs-metric-icon purple">📈</div>
          <div className="gs-metric-value">{predictions.length}</div>
          <div className="gs-metric-label">Predictions Generated</div>
        </div>
      </div>

      {/* Pipeline action tiles */}
      <div className="gs-action-grid">
        <Link to="/ml/datasets/new" className="gs-action-card teal">
          <div className="gs-action-card-icon teal">🗄️</div>
          <div className="gs-action-card-title">1. Build Dataset</div>
          <div className="gs-action-card-desc">
            Extract completed experiments, select features &amp; targets, validate eligibility &amp; eliminate target leakage.
          </div>
          <div className="gs-action-card-link">Build Dataset Wizard →</div>
        </Link>

        <Link to="/ml/training" className="gs-action-card indigo">
          <div className="gs-action-card-icon indigo">🧠</div>
          <div className="gs-action-card-title">2. Model Training &amp; CV</div>
          <div className="gs-action-card-desc">
            Train baseline, linear, Ridge, Random Forest &amp; Gradient Boosting models with cross-validation &amp; diagnostic charts.
          </div>
          <div className="gs-action-card-link">Train Models →</div>
        </Link>

        <Link to="/ml/predict" className="gs-action-card purple">
          <div className="gs-action-card-icon purple">📊</div>
          <div className="gs-action-card-title">3. Prediction &amp; Bounds</div>
          <div className="gs-action-card-desc">
            Generate property predictions with uncertainty intervals &amp; applicability domain boundary checks.
          </div>
          <div className="gs-action-card-link">Generate Prediction →</div>
        </Link>

        <Link to="/ml/validation" className="gs-action-card emerald">
          <div className="gs-action-card-icon emerald">🛡️</div>
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
          <span className="gs-panel-title">📋 Project Datasets</span>
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
            <div className="gs-empty-icon">🗄️</div>
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
                  <th>Version</th>
                  <th>Target Property</th>
                  <th>Eligible Records</th>
                  <th>Excluded</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((d) => (
                  <tr key={d.id}>
                    <td style={{ fontWeight: 600 }}>{d.name}</td>
                    <td><span className="gs-badge slate">{d.version}</span></td>
                    <td style={{ color: '#0d9488' }}>{d.target_property} ({d.target_unit})</td>
                    <td style={{ fontWeight: 700, color: '#059669' }}>{d.eligible_count}</td>
                    <td style={{ color: '#b45309' }}>{d.excluded_count}</td>
                    <td>
                      <span className={`gs-chip ${d.status === 'IMMUTABLE' ? 'production' : d.status === 'ACTIVE' ? 'active' : 'inactive'}`}>
                        {d.status}
                      </span>
                    </td>
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
            <span className="gs-panel-title">🧠 Trained Models</span>
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
