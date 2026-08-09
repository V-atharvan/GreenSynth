/**
 * GreenSynth Analytics — Research Loop: Closed-Loop Learning System (Phase 13)
 */

import React, { useEffect, useState } from 'react'
import { closedLoopService, ResearchLoopSummary, DatasetCandidate } from '@/services/closedLoopService'
import { mlService, MLModel } from '@/services/mlService'
import {
  RotateCw,
  Brain,
  CheckCircle2,
  TrendingDown,
  BarChart2,
  Database,
  FileCheck,
  Check,
  X,
  Award,
  FlaskConical,
  Lightbulb,
  FileSpreadsheet,
} from 'lucide-react'

const STAGE_ICONS = [
  FlaskConical,
  Database,
  Brain,
  Lightbulb,
  FlaskConical,
  FileSpreadsheet,
  CheckCircle2,
  FileCheck,
  Database,
  Award,
]

export default function ClosedLoopDashboard() {
  const [summary, setSummary] = useState<ResearchLoopSummary | null>(null)
  const [candidates, setCandidates] = useState<DatasetCandidate[]>([])
  const [models, setModels] = useState<MLModel[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [processingId, setProcessingId] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [sumRes, candRes, modelRes] = await Promise.all([
        closedLoopService.getSummary(),
        closedLoopService.listDatasetCandidates(),
        mlService.getModels(),
      ])
      setSummary(sumRes)
      setCandidates(candRes)
      setModels(modelRes)
    } catch (err) {
      console.error('Failed to load closed-loop summary:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const handleAcceptCandidate = async (candId: string) => {
    setProcessingId(candId)
    try {
      await closedLoopService.acceptCandidate(candId)
      setMessage(`Candidate ${candId.slice(0, 8)} ACCEPTED into next dataset version.`)
      await loadData()
    } catch (err) {
      console.error('Failed to accept candidate:', err)
    } finally {
      setProcessingId(null)
    }
  }

  const handleRejectCandidate = async (candId: string) => {
    setProcessingId(candId)
    try {
      await closedLoopService.rejectCandidate(candId)
      setMessage(`Candidate ${candId.slice(0, 8)} REJECTED.`)
      await loadData()
    } catch (err) {
      console.error('Failed to reject candidate:', err)
    } finally {
      setProcessingId(null)
    }
  }

  const handlePromoteModel = async (modelId: string) => {
    try {
      await closedLoopService.promoteModel(modelId)
      setMessage(`Model promoted to ACTIVE production state.`)
      await loadData()
    } catch (err) {
      console.error('Failed to promote model:', err)
    }
  }

  const stages = [
    { title: 'Experimental Data',  count: summary?.stage_counts.experimental_data ?? 0 },
    { title: 'Dataset',            count: summary?.stage_counts.dataset ?? 0 },
    { title: 'Model (Active)',      count: summary?.stage_counts.model ?? 'v1.0' },
    { title: 'Recommendation',     count: summary?.stage_counts.recommendation ?? 0 },
    { title: 'Lab Experiment',      count: summary?.stage_counts.experiment ?? 0 },
    { title: 'Actual Result',      count: summary?.stage_counts.actual_result ?? 0 },
    { title: 'Validation',         count: summary?.stage_counts.validation ?? 0 },
    { title: 'Dataset Candidate',  count: summary?.stage_counts.dataset_candidate ?? 0 },
    { title: 'New Dataset',        count: summary?.stage_counts.new_dataset ?? 'v1.0' },
    { title: 'New Model',          count: summary?.stage_counts.new_model ?? 'v1.0' },
  ]

  const pendingCount = candidates.filter((c) => c.researcher_review_status === 'PENDING_REVIEW').length

  return (
    <div className="gs-page">

      {/* Header */}
      <div className="gs-page-header">
        <div>
          <div className="gs-page-title">
            <div className="gs-page-title-icon emerald">
              <RotateCw className="w-5 h-5 text-emerald-600" />
            </div>
            Research Loop — Closed-Loop Learning System
          </div>
          <p className="gs-page-subtitle">
            Autonomous scientific discovery loop linking laboratory experiments, dataset growth, model retraining, and human-in-the-loop promotion.
          </p>
        </div>
        <div className="gs-header-actions">
          <button onClick={loadData} className="gs-btn gs-btn-outline" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <RotateCw className="w-4 h-4" /> Refresh Loop Metrics
          </button>
        </div>
      </div>

      {/* Alert */}
      {message && (
        <div className="gs-alert success" style={{ justifyContent: 'space-between' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> {message}
          </span>
          <button onClick={() => setMessage(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#14532d', fontWeight: 700 }}>
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {loading ? (
        <div className="gs-loading">
          <div className="gs-spinner" />
          Loading research loop…
        </div>
      ) : (
        <>
          {/* Summary metrics */}
          <div className="gs-metrics-row">
            <div className="gs-metric-card emerald">
              <div className="gs-metric-icon emerald">
                <Brain className="w-5 h-5 text-emerald-600" />
              </div>
              <div className="gs-metric-value">{summary?.active_model_version ?? '—'}</div>
              <div className="gs-metric-label">Active Model</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: 4 }}>
                Dataset {summary?.active_dataset_version ?? '—'}
              </div>
            </div>
            <div className="gs-metric-card indigo">
              <div className="gs-metric-icon indigo">
                <CheckCircle2 className="w-5 h-5 text-indigo-600" />
              </div>
              <div className="gs-metric-value">{summary?.validations_completed ?? 0}</div>
              <div className="gs-metric-label">Validations Completed</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: 4 }}>
                Sample size n = {summary?.sample_count_n ?? 0}
              </div>
            </div>
            <div className="gs-metric-card teal">
              <div className="gs-metric-icon teal">
                <TrendingDown className="w-5 h-5 text-teal-600" />
              </div>
              <div className="gs-metric-value">
                {summary?.avg_absolute_error !== undefined && summary?.avg_absolute_error !== null
                  ? summary.avg_absolute_error.toFixed(3)
                  : 'N/A'}
              </div>
              <div className="gs-metric-label">Avg Absolute Error</div>
            </div>
            <div className="gs-metric-card amber">
              <div className="gs-metric-icon amber">
                <BarChart2 className="w-5 h-5 text-amber-600" />
              </div>
              <div className="gs-metric-value" style={{ fontSize: '1.25rem' }}>
                {summary?.evidence_level ?? 'INSUFFICIENT'}
              </div>
              <div className="gs-metric-label">Evidence Quality Level</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: 4 }}>
                Based on n = {summary?.sample_count_n ?? 0} lab points
              </div>
            </div>
          </div>

          {/* 10-Stage Pipeline Visual */}
          <div className="gs-panel">
            <div className="gs-panel-header">
              <span className="gs-panel-title" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <RotateCw className="w-4 h-4 text-emerald-600" /> Closed-Loop Research Workflow Architecture
              </span>
              <span className="gs-chip stable">Immutability &amp; Safety Enforced</span>
            </div>
            <div className="gs-panel-body">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 12 }}>
                {stages.map((stg, i) => {
                  const IconComp = STAGE_ICONS[i] || FlaskConical
                  return (
                    <div
                      key={stg.title}
                      style={{
                        background: 'var(--color-bg)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 'var(--radius-lg)',
                        padding: '14px 10px',
                        textAlign: 'center',
                        position: 'relative',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 8 }}>
                        <IconComp className="w-5 h-5 text-emerald-600" />
                      </div>
                      <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
                        {i + 1}. {stg.title}
                      </div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--color-text)' }}>
                        {stg.count}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Dataset Candidate Review */}
          <div className="gs-panel">
            <div className="gs-panel-header">
              <div>
                <span className="gs-panel-title">Dataset Candidate Review Gate (Human-in-the-Loop)</span>
                <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 4 }}>
                  Review completed prospective experiment results before including them into immutable Dataset V(N+1).
                </p>
              </div>
              {pendingCount > 0 && (
                <span className="gs-chip warning">{pendingCount} Pending Review</span>
              )}
            </div>

            {candidates.length === 0 ? (
              <div className="gs-empty">
                <div className="gs-empty-icon">
                  <FileCheck className="w-8 h-8 text-slate-400" />
                </div>
                <div className="gs-empty-title">No Dataset Candidates</div>
                <div className="gs-empty-text">
                  Validated prospective experiments will appear here automatically after completion.
                </div>
              </div>
            ) : (
              <div className="gs-table-wrapper">
                <table className="gs-table">
                  <thead>
                    <tr>
                      <th>Candidate ID</th>
                      <th>Proposed Target</th>
                      <th>Data Quality</th>
                      <th>Review Status</th>
                      <th>Created</th>
                      <th style={{ textAlign: 'right' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {candidates.map((c) => (
                      <tr key={c.id}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem' }}>{c.candidate_dataset_id.slice(0, 12)}…</td>
                        <td style={{ color: '#059669', fontWeight: 600 }}>{c.proposed_target}</td>
                        <td>
                          <span className="gs-chip stable">{c.data_quality_status}</span>
                        </td>
                        <td>
                          <span className={`gs-chip ${
                            c.researcher_review_status === 'ACCEPTED' ? 'stable' :
                            c.researcher_review_status === 'REJECTED' ? 'critical' : 'warning'
                          }`}>
                            {c.researcher_review_status}
                          </span>
                        </td>
                        <td style={{ color: 'var(--color-text-secondary)' }}>
                          {c.created_at ? new Date(c.created_at).toLocaleDateString() : 'N/A'}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          {c.researcher_review_status === 'PENDING_REVIEW' && (
                            <span style={{ display: 'inline-flex', gap: 8 }}>
                              <button
                                onClick={() => handleAcceptCandidate(c.id)}
                                disabled={processingId === c.id}
                                className="gs-btn gs-btn-emerald gs-btn-sm"
                                style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                              >
                                <Check className="w-3.5 h-3.5" /> Accept
                              </button>
                              <button
                                onClick={() => handleRejectCandidate(c.id)}
                                disabled={processingId === c.id}
                                className="gs-btn gs-btn-danger gs-btn-sm"
                                style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                              >
                                <X className="w-3.5 h-3.5" /> Reject
                              </button>
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Model Lifecycle Panel */}
          <div className="gs-panel">
            <div className="gs-panel-header">
              <div>
                <span className="gs-panel-title">Model Promotion &amp; Retirement Registry</span>
                <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 4 }}>
                  Models are NEVER automatically replaced. Explicit researcher promotion is required to activate a model for recommendations.
                </p>
              </div>
            </div>
            {models.length === 0 ? (
              <div className="gs-empty" style={{ padding: '40px 24px' }}>
                <div className="gs-empty-icon">
                  <Brain className="w-8 h-8 text-slate-400" />
                </div>
                <div className="gs-empty-title">No Models Trained Yet</div>
                <div className="gs-empty-text">Train models from the Machine Learning Center to begin the promotion workflow.</div>
              </div>
            ) : (
              <div className="gs-panel-body">
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16 }}>
                  {models.map((m) => (
                    <div key={m.id} className="gs-candidate-card">
                      <div className="gs-candidate-card-header">
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.9375rem', marginBottom: 2 }}>{m.name}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>v{m.version} · {m.model_type}</div>
                        </div>
                        <span className={`gs-chip ${
                          m.status === 'ACTIVE' ? 'stable' :
                          m.status === 'RETIRED' ? 'retired' :
                          m.status === 'PRODUCTION_CANDIDATE' ? 'production' : 'info'
                        }`}>
                          {m.status}
                        </span>
                      </div>

                      <div className="gs-param-grid">
                        <div className="gs-param-item">
                          <div className="gs-param-name">Target</div>
                          <div className="gs-param-value" style={{ fontSize: '0.8125rem', color: '#0d9488' }}>{m.target_property}</div>
                        </div>
                        <div className="gs-param-item">
                          <div className="gs-param-name">CV MAE</div>
                          <div className="gs-param-value" style={{ fontSize: '0.8125rem' }}>
                            {m.metrics?.cv_mae != null ? m.metrics.cv_mae.toFixed(4) : '—'}
                          </div>
                        </div>
                      </div>

                      {m.status !== 'ACTIVE' && m.status !== 'RETIRED' && (
                        <button
                          onClick={() => handlePromoteModel(m.id)}
                          className="gs-btn gs-btn-emerald"
                          style={{ width: '100%', justifyContent: 'center', marginTop: 4 }}
                        >
                          Promote to ACTIVE Production Model
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
