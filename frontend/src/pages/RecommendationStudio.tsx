/**
 * GreenSynth Analytics — Recommendation Studio (Phase 12)
 *
 * Human-in-the-Loop Decision Support System.
 */

import { useEffect, useState } from 'react'
import {
  recommendationService,
  Recommendation,
  RecommendationCandidate,
  RecommendationGeneratePayload,
} from '@/services/recommendationService'
import { mlService, MLModel } from '@/services/mlService'
import { doeService, Objective } from '@/services/doeService'
import { projectService } from '@/services/projectService'
import type { ProjectSummary } from '@/types'
import {
  Lightbulb,
  Info,
  AlertTriangle,
  CheckCircle2,
  Settings,
  Edit2,
  Zap,
  FlaskConical,
  X,
  Check,
} from 'lucide-react'

export default function RecommendationStudio() {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')
  const [objectives, setObjectives] = useState<Objective[]>([])
  const [selectedObjectiveId, setSelectedObjectiveId] = useState<string>('')
  const [models, setModels] = useState<MLModel[]>([])
  const [selectedModelId, setSelectedModelId] = useState<string>('')
  const [rankingMethod, setRankingMethod] = useState<'BALANCED' | 'EXPLOITATION' | 'EXPLORATION'>('BALANCED')
  const [candidateCount, setCandidateCount] = useState<number>(5)
  const [activeSession, setActiveSession] = useState<Recommendation | null>(null)
  const [candidates, setCandidates] = useState<RecommendationCandidate[]>([])
  const [modifyingCandidate, setModifyingCandidate] = useState<RecommendationCandidate | null>(null)
  const [modParams, setModParams] = useState<Record<string, number>>({})
  const [modReason, setModReason] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  useEffect(() => { fetchInitialData() }, [])
  useEffect(() => {
    if (selectedProjectId) fetchProjectDependents(selectedProjectId)
  }, [selectedProjectId])

  const fetchInitialData = async () => {
    try {
      const projs = await projectService.getAll()
      setProjects(projs)
      if (projs.length > 0) setSelectedProjectId(projs[0].id)
    } catch (err: any) {
      setError(err.message || 'Failed to load projects.')
    }
  }

  const fetchProjectDependents = async (projectId: string) => {
    try {
      setLoading(true)
      setError(null)
      const [objs, mdls] = await Promise.all([
        doeService.listObjectives(projectId),
        mlService.listModels(),
      ])
      setObjectives(objs)
      if (objs.length > 0) setSelectedObjectiveId(objs[0].id)
      setModels(mdls)
      if (mdls.length > 0) setSelectedModelId(mdls[0].id)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch objectives and models.')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (!selectedProjectId || !selectedObjectiveId || !selectedModelId) {
      setError('Please select a project, objective, and model.')
      return
    }
    try {
      setLoading(true)
      setError(null)
      setSuccessMsg(null)
      const payload: RecommendationGeneratePayload = {
        project_id: selectedProjectId,
        objective_id: selectedObjectiveId,
        model_id: selectedModelId,
        candidate_count: candidateCount,
        ranking_method: rankingMethod,
        random_seed: 42,
      }
      const session = await recommendationService.generateRecommendations(payload)
      setActiveSession(session)
      setCandidates(session.candidates || [])
      setSuccessMsg(`Generated ${session.candidates.length} candidate experimental conditions!`)
    } catch (err: any) {
      setError(err.response?.data?.message || err.response?.data?.detail || err.message || 'Failed to generate recommendations.')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (candidateId: string) => {
    try {
      setLoading(true)
      const updated = await recommendationService.approveCandidate(candidateId)
      setCandidates((prev) => prev.map((c) => (c.id === candidateId ? updated : c)))
      setSuccessMsg(`Candidate #${updated.rank} approved by researcher!`)
    } catch (err: any) {
      setError(err.message || 'Failed to approve candidate.')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenModifyModal = (candidate: RecommendationCandidate) => {
    setModifyingCandidate(candidate)
    const initialParams: Record<string, number> = {}
    Object.entries(candidate.parameter_set).forEach(([k, v]) => { initialParams[k] = Number(v) })
    setModParams(initialParams)
    setModReason('Adjusted for equipment calibration and substrate heater bounds.')
  }

  const handleSaveModification = async () => {
    if (!modifyingCandidate) return
    try {
      setLoading(true)
      const updated = await recommendationService.modifyCandidate(modifyingCandidate.id, {
        modified_parameter_set: modParams,
        modification_reason: modReason,
      })
      setCandidates((prev) => prev.map((c) => (c.id === modifyingCandidate.id ? updated : c)))
      setModifyingCandidate(null)
      setSuccessMsg(`Researcher modifications saved for Candidate #${updated.rank}!`)
    } catch (err: any) {
      setError(err.message || 'Failed to modify candidate.')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateExperiment = async (candidateId: string) => {
    try {
      setLoading(true)
      const res = await recommendationService.createExperimentFromCandidate(candidateId)
      setCandidates((prev) => prev.map((c) => (c.id === candidateId ? { ...c, status: 'EXPERIMENT_CREATED' } : c)))
      setSuccessMsg(`Created PLANNED experiment ${res.experiment_code}!`)
    } catch (err: any) {
      setError(err.message || 'Failed to create experiment.')
    } finally {
      setLoading(false)
    }
  }

  const selectedModel = models.find((m) => m.id === selectedModelId)
  const isModelValidated = selectedModel && ['PRODUCTION_CANDIDATE', 'EXPERIMENTALLY_VALIDATED'].includes(selectedModel.status)

  const rankColors: Record<number, string> = { 1: 'gold', 2: 'silver', 3: 'bronze' }

  return (
    <div className="gs-page">

      {/* Header */}
      <div className="gs-page-header">
        <div>
          <div className="gs-page-title">
            <div className="gs-page-title-icon teal">
              <Lightbulb className="w-5 h-5 text-teal-600" />
            </div>
            Recommendation Studio
          </div>
          <p className="gs-page-subtitle">
            Human-in-the-Loop Decision Support for Green Synthesis Optimization
          </p>
        </div>
        <span className="gs-chip production">Phase 12 Active</span>
      </div>

      {/* Scientific Principle Banner */}
      <div className="gs-info-banner blue">
        <div className="gs-info-banner-icon">
          <Info className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <div className="gs-info-banner-title">Scientific Principle</div>
          <div className="gs-info-banner-text">
            Recommendations output <em>promising candidate experimental conditions</em> to guide research.
            Models never automate laboratory equipment or claim universal optimality.{' '}
            <strong>Researcher review is required.</strong>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="gs-alert error" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="gs-alert success" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Configuration Panel */}
      <div className="gs-panel">
        <div className="gs-panel-header">
          <span className="gs-panel-title" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <Settings className="w-4 h-4 text-slate-600" /> Optimization Target &amp; Model Selection
          </span>
        </div>
        <div className="gs-panel-body">
          <div className="gs-form-row">
            <div className="gs-field">
              <label className="gs-label">Project</label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="gs-input"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.project_code} — {p.name}</option>
                ))}
              </select>
            </div>

            <div className="gs-field">
              <label className="gs-label">Optimization Objective</label>
              <select
                value={selectedObjectiveId}
                onChange={(e) => setSelectedObjectiveId(e.target.value)}
                className="gs-input"
              >
                <option value="">— Select objective —</option>
                {objectives.map((o) => (
                  <option key={o.id} value={o.id}>{o.name} ({o.target_property})</option>
                ))}
              </select>
            </div>

            <div className="gs-field">
              <label className="gs-label">ML Model (Gate Check)</label>
              <select
                value={selectedModelId}
                onChange={(e) => setSelectedModelId(e.target.value)}
                className="gs-input"
              >
                <option value="">— Select model —</option>
                {models.map((m) => (
                  <option key={m.id} value={m.id}>{m.name} [{m.status}]</option>
                ))}
              </select>
              {selectedModel && !isModelValidated && (
                <div style={{ fontSize: '0.8125rem', color: '#dc2626', marginTop: 4 }}>
                  Status '{selectedModel.status}' blocked — approve model first.
                </div>
              )}
            </div>
          </div>

          <div className="gs-form-row" style={{ marginTop: 20 }}>
            <div className="gs-field">
              <label className="gs-label">Ranking Strategy</label>
              <select
                value={rankingMethod}
                onChange={(e) => setRankingMethod(e.target.value as any)}
                className="gs-input"
              >
                <option value="BALANCED">BALANCED (Tradeoff exploitation &amp; exploration)</option>
                <option value="EXPLOITATION">EXPLOITATION (Maximize predicted target value)</option>
                <option value="EXPLORATION">EXPLORATION (Target high uncertainty domain areas)</option>
              </select>
            </div>

            <div className="gs-field">
              <label className="gs-label">Candidate Count</label>
              <input
                type="number"
                min={1}
                max={15}
                value={candidateCount}
                onChange={(e) => setCandidateCount(Number(e.target.value))}
                className="gs-input"
              />
            </div>

            <div className="gs-field" style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button
                onClick={handleGenerate}
                disabled={loading || !isModelValidated}
                className="gs-btn gs-btn-emerald"
                style={{ width: '100%', justifyContent: 'center', display: 'inline-flex', alignItems: 'center', gap: 6 }}
              >
                <Zap className="w-4 h-4" />
                {loading ? 'Generating…' : 'Generate Candidate Conditions'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Candidate Results */}
      {candidates.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-text)' }}>
              Top Recommended Candidates ({candidates.length})
            </h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
              Session: <code style={{ color: '#0d9488' }}>{activeSession?.id.substring(0, 8)}</code>
            </span>
          </div>

          {candidates.map((cand) => (
            <div key={cand.id} className="gs-candidate-card">
              {/* Card header */}
              <div className="gs-candidate-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div className={`gs-candidate-rank ${rankColors[cand.rank] || ''}`}>#{cand.rank}</div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.9375rem' }}>
                      Rank #{cand.rank} — Overall Score: {(cand.overall_score * 100).toFixed(1)}%
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>{cand.explanation}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  <span className={`gs-chip ${
                    cand.status === 'APPROVED' ? 'stable' :
                    cand.status === 'MODIFIED' ? 'warning' :
                    cand.status === 'EXPERIMENT_CREATED' ? 'info' : 'muted'
                  }`}>{cand.status}</span>
                  <span className={`gs-chip ${
                    cand.evidence_level === 'HIGH' ? 'stable' :
                    cand.evidence_level === 'MODERATE' ? 'info' : 'warning'
                  }`}>{cand.evidence_level} Evidence ({(cand.evidence_score * 100).toFixed(0)}%)</span>
                  <span className={`gs-chip ${
                    cand.applicability_status === 'IN_DOMAIN' ? 'stable' :
                    cand.applicability_status === 'NEAR_BOUNDARY' ? 'warning' : 'critical'
                  }`}>{cand.applicability_status}</span>
                </div>
              </div>

              <hr className="gs-divider" />

              {/* Parameters + Prediction */}
              <div className="gs-two-col" style={{ marginTop: 16 }}>
                {/* Synthesis Parameters */}
                <div>
                  <div className="gs-label" style={{ marginBottom: 10 }}>Proposed Synthesis Parameters</div>
                  <div className="gs-param-grid">
                    {Object.entries(cand.parameter_set).map(([k, v]) => (
                      <div key={k} className="gs-param-item">
                        <div className="gs-param-name">{k}</div>
                        <div className="gs-param-value" style={{ color: '#0d9488' }}>{Number(v).toFixed(2)}</div>
                      </div>
                    ))}
                  </div>

                  {cand.modified_parameter_set && (
                    <div style={{ marginTop: 12, padding: '10px 12px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 'var(--radius-md)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#92400e', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Edit2 className="w-3.5 h-3.5 text-amber-700" /> Researcher Modified Parameters (Original Preserved):
                      </div>
                      <div className="gs-param-grid">
                        {Object.entries(cand.modified_parameter_set).map(([k, v]) => (
                          <div key={k} className="gs-param-item" style={{ background: '#fef3c7', borderColor: '#fcd34d' }}>
                            <div className="gs-param-name">{k}</div>
                            <div className="gs-param-value" style={{ color: '#b45309' }}>{Number(v).toFixed(2)}</div>
                          </div>
                        ))}
                      </div>
                      {cand.modification_reason && (
                        <div style={{ fontSize: '0.75rem', color: '#78350f', marginTop: 6, fontStyle: 'italic' }}>
                          Reason: "{cand.modification_reason}"
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Predicted Performance */}
                <div>
                  <div className="gs-label" style={{ marginBottom: 10 }}>Predicted Property &amp; Uncertainty</div>

                  <div style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '12px 14px', marginBottom: 10 }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: 4 }}>
                      Predicted {cand.predicted_properties.property_name}
                    </div>
                    <div style={{ fontSize: '1.375rem', fontWeight: 800, color: 'var(--color-text)' }}>
                      {cand.predicted_properties.predicted_value}{' '}
                      <span style={{ fontSize: '0.8125rem', fontWeight: 400, color: 'var(--color-text-secondary)' }}>
                        {cand.predicted_properties.unit}
                      </span>
                    </div>
                  </div>

                  {/* Score bars */}
                  <div>
                    <div className="gs-score-bar">
                      <div className="gs-score-label">Evidence Score</div>
                      <div className="gs-score-track">
                        <div className="gs-score-fill teal" style={{ width: `${(cand.evidence_score * 100).toFixed(0)}%` }} />
                      </div>
                      <div className="gs-score-value">{(cand.evidence_score * 100).toFixed(0)}%</div>
                    </div>
                    <div className="gs-score-bar">
                      <div className="gs-score-label">Overall Score</div>
                      <div className="gs-score-track">
                        <div className="gs-score-fill indigo" style={{ width: `${(cand.overall_score * 100).toFixed(0)}%` }} />
                      </div>
                      <div className="gs-score-value">{(cand.overall_score * 100).toFixed(0)}%</div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', marginTop: 10, color: 'var(--color-text-secondary)' }}>
                    <span>95% CI: [{cand.uncertainty.lower_bound} — {cand.uncertainty.upper_bound}] (±{cand.uncertainty.width})</span>
                    <span className={cand.constraint_status === 'SATISFIED' ? '' : ''} style={{ fontWeight: 600, color: cand.constraint_status === 'SATISFIED' ? '#059669' : '#b45309' }}>
                      {cand.constraint_status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action buttons */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--color-border-light)' }}>
                <button onClick={() => handleOpenModifyModal(cand)} className="gs-btn gs-btn-outline gs-btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  <Edit2 className="w-3.5 h-3.5" /> Modify Parameters
                </button>
                <button
                  onClick={() => handleApprove(cand.id)}
                  disabled={cand.status === 'APPROVED' || cand.status === 'EXPERIMENT_CREATED'}
                  className="gs-btn gs-btn-emerald gs-btn-sm"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                >
                  <Check className="w-3.5 h-3.5" /> Approve Candidate
                </button>
                <button
                  onClick={() => handleCreateExperiment(cand.id)}
                  disabled={cand.status === 'EXPERIMENT_CREATED'}
                  className="gs-btn gs-btn-indigo gs-btn-sm"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                >
                  <FlaskConical className="w-3.5 h-3.5" /> Create Planned Experiment
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!candidates.length && !loading && (
        <div className="gs-empty">
          <div className="gs-empty-icon">
            <Lightbulb className="w-8 h-8 text-slate-400" />
          </div>
          <div className="gs-empty-title">No Active Recommendations</div>
          <div className="gs-empty-text">
            Select a project, objective, and approved model, then generate candidate synthesis conditions.
          </div>
        </div>
      )}

      {/* Modify Modal */}
      {modifyingCandidate && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Edit2 className="w-4 h-4 text-indigo-600" /> Modify Parameters — Candidate #{modifyingCandidate.rank}
              </div>
              <button className="modal-close" onClick={() => setModifyingCandidate(null)}>
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="modal-body">
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                Adjust parameters based on lab availability. Original parameters are preserved for scientific traceability.
              </p>
              {Object.entries(modParams).map(([paramName, val]) => (
                <div key={paramName} className="form-group">
                  <label className="form-label">{paramName}</label>
                  <input
                    type="number"
                    step="0.1"
                    value={val}
                    onChange={(e) => setModParams((prev) => ({ ...prev, [paramName]: Number(e.target.value) }))}
                    className="form-control"
                  />
                </div>
              ))}
              <div className="form-group">
                <label className="form-label">Modification Reason</label>
                <textarea
                  value={modReason}
                  onChange={(e) => setModReason(e.target.value)}
                  rows={2}
                  className="form-control"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setModifyingCandidate(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSaveModification}>Save Modifications</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
