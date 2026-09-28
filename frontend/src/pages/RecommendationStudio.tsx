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
import { useProjectContext } from '@/context/ProjectContext'
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
  XCircle,
  Check,
  FolderKanban,
} from 'lucide-react'

const PARAM_LABELS: Record<string, { label: string; unit?: string }> = {
  substrate_temperature_c: { label: 'Substrate Temp', unit: '°C' },
  substrate_temperature: { label: 'Substrate Temp', unit: '°C' },
  precursor_concentration: { label: 'Precursor Conc', unit: 'M' },
  spray_rate_ml_min: { label: 'Spray Rate', unit: 'mL/min' },
  spray_rate: { label: 'Spray Rate', unit: 'mL/min' },
  spray_duration_min: { label: 'Spray Duration', unit: 'min' },
  spray_duration: { label: 'Spray Duration', unit: 'min' },
  spray_cycles: { label: 'Spray Cycles', unit: 'cycles' },
  nozzle_substrate_distance_cm: { label: 'Nozzle Distance', unit: 'cm' },
  nozzle_distance: { label: 'Nozzle Distance', unit: 'cm' },
  carrier_gas_pressure_kpa: { label: 'Carrier Gas Pres', unit: 'kPa' },
  carrier_gas_pressure: { label: 'Carrier Gas Pres', unit: 'kPa' },
  mulberry_extract_volume: { label: 'Mulberry Ext Vol', unit: 'mL' },
  mulberry_extract_concentration: { label: 'Mulberry Ext Conc', unit: 'wt%' },
  precursor_solution_volume: { label: 'Precursor Sol Vol', unit: 'mL' },
  ethanol_volume: { label: 'Ethanol Vol', unit: 'mL' },
  ambient_temperature_c: { label: 'Ambient Temp', unit: '°C' },
  ambient_temperature: { label: 'Ambient Temp', unit: '°C' },
  ambient_relative_humidity: { label: 'Ambient Humidity', unit: '%' },
}

const formatParamKey = (k: string) => {
  const normalized = k.toLowerCase().trim()
  if (PARAM_LABELS[normalized]) {
    return PARAM_LABELS[normalized].label
  }
  return k.replace(/_/g, ' ')
}

const getParamUnit = (k: string) => {
  const normalized = k.toLowerCase().trim()
  return PARAM_LABELS[normalized]?.unit || ''
}

export default function RecommendationStudio() {
  const { projectId, projectCode, projectName } = useProjectContext()
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
  const [toasts, setToasts] = useState<Array<{
    id: string
    type: 'success' | 'warning' | 'error' | 'info'
    title: string
    message: string
    rank?: number
  }>>([])

  const showToast = (toast: {
    type: 'success' | 'warning' | 'error' | 'info'
    title: string
    message: string
    rank?: number
  }) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast = { ...toast, id }
    setToasts((prev) => [newToast, ...prev].slice(0, 4))

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 5000)
  }

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  useEffect(() => {
    if (projectId) fetchProjectDependents(projectId)
  }, [projectId])

  const fetchProjectDependents = async (projectId: string) => {
    try {
      setLoading(true)
      setError(null)
      const [objs, mdls] = await Promise.all([
        doeService.listObjectives(projectId),
        mlService.getModels(),
      ])
      setObjectives(objs)
      if (objs.length > 0) setSelectedObjectiveId(objs[0].id)
      setModels(mdls)
      if (mdls.length > 0) setSelectedModelId(mdls[0].id)
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch objectives and models.')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (!projectId || !selectedObjectiveId || !selectedModelId) {
      setError('Please select an objective and model.')
      showToast({ type: 'warning', title: 'Selection Incomplete', message: 'Please select an objective and model.' })
      return
    }
    try {
      setLoading(true)
      setError(null)
      setSuccessMsg(null)
      const payload: RecommendationGeneratePayload = {
        project_id: projectId,
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
      showToast({
        type: 'info',
        title: 'Conditions Generated',
        message: `Successfully computed ${session.candidates.length} candidate synthesis recipes.`,
      })
    } catch (err: any) {
      const msg = err.response?.data?.message || err.response?.data?.detail || err.message || 'Failed to generate recommendations.'
      setError(msg)
      showToast({ type: 'error', title: 'Generation Failed', message: msg })
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
      showToast({
        type: 'success',
        title: `Candidate #${updated.rank} Approved`,
        message: `Status transitioned to APPROVED. Researcher sign-off logged for physical synthesis.`,
        rank: updated.rank,
      })
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to approve candidate.'
      setError(msg)
      showToast({ type: 'error', title: 'Approval Failed', message: msg })
    } finally {
      setLoading(false)
    }
  }

  const handleReject = async (candidateId: string) => {
    try {
      setLoading(true)
      const updated = await recommendationService.rejectCandidate(candidateId)
      setCandidates((prev) => prev.map((c) => (c.id === candidateId ? updated : c)))
      setSuccessMsg(`Candidate #${updated.rank} marked as rejected.`)
      showToast({
        type: 'error',
        title: `Candidate #${updated.rank} Rejected`,
        message: `Status transitioned to REJECTED. Recipe dismissed from candidate queue.`,
        rank: updated.rank,
      })
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to reject candidate.'
      setError(msg)
      showToast({ type: 'error', title: 'Rejection Failed', message: msg })
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
      showToast({
        type: 'warning',
        title: `Candidate #${updated.rank} Modified`,
        message: `Status transitioned to MODIFIED. Equipment calibration adjustments logged.`,
        rank: updated.rank,
      })
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to modify candidate.'
      setError(msg)
      showToast({ type: 'error', title: 'Modification Failed', message: msg })
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
      const cand = candidates.find((c) => c.id === candidateId)
      showToast({
        type: 'info',
        title: `Planned Experiment Created`,
        message: `Status transitioned to EXPERIMENT_CREATED. Lab experiment ${res.experiment_code} queued for execution!`,
        rank: cand?.rank,
      })
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to create experiment.'
      setError(msg)
      showToast({ type: 'error', title: 'Experiment Creation Failed', message: msg })
    } finally {
      setLoading(false)
    }
  }

  const selectedObjective = objectives.find((o) => o.id === selectedObjectiveId)
  const selectedModel = models.find((m) => m.id === selectedModelId)
  const isModelValidated = selectedModel && ['PRODUCTION_CANDIDATE', 'EXPERIMENTALLY_VALIDATED'].includes(selectedModel.status)
  const isTargetMatched = Boolean(
    selectedObjective &&
    selectedModel &&
    selectedModel.target_property?.trim().toLowerCase() === selectedObjective.target_property?.trim().toLowerCase()
  )
  const hasTargetMismatch = Boolean(
    selectedObjective &&
    selectedModel &&
    selectedModel.target_property?.trim().toLowerCase() !== selectedObjective.target_property?.trim().toLowerCase()
  )

  const handleObjectiveChange = (objId: string) => {
    setSelectedObjectiveId(objId)
    const obj = objectives.find((o) => o.id === objId)
    if (obj) {
      const matchingModel = models.find((m) =>
        m.target_property?.trim().toLowerCase() === obj.target_property?.trim().toLowerCase() &&
        ['PRODUCTION_CANDIDATE', 'EXPERIMENTALLY_VALIDATED'].includes(m.status)
      ) || models.find((m) =>
        m.target_property?.trim().toLowerCase() === obj.target_property?.trim().toLowerCase()
      )
      if (matchingModel) {
        setSelectedModelId(matchingModel.id)
      }
    }
  }

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
              <label className="gs-label">Optimization Objective</label>
              <select
                value={selectedObjectiveId}
                onChange={(e) => handleObjectiveChange(e.target.value)}
                className="gs-input"
              >
                <option value="">— Select objective —</option>
                {objectives.map((o) => (
                  <option key={o.id} value={o.id}>{o.name} ({o.target_property})</option>
                ))}
              </select>
              {selectedObjective && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6, flexWrap: 'wrap', fontSize: '0.75rem' }}>
                  <span style={{ padding: '2px 6px', borderRadius: 4, background: '#e0f2fe', color: '#0369a1', fontWeight: 600 }}>
                    Target: {selectedObjective.target_property}
                  </span>
                  <span style={{ padding: '2px 6px', borderRadius: 4, background: '#f1f5f9', color: '#475569', fontWeight: 600 }}>
                    {selectedObjective.direction} {selectedObjective.target_value != null ? `(${selectedObjective.target_value} ${selectedObjective.unit || ''})` : ''}
                  </span>
                </div>
              )}
            </div>

            <div className="gs-field">
              <label className="gs-label">ML Model (Gate Check)</label>
              <select
                value={selectedModelId}
                onChange={(e) => setSelectedModelId(e.target.value)}
                className="gs-input"
              >
                <option value="">— Select model —</option>
                {models.map((m) => {
                  const matches = selectedObjective && m.target_property?.trim().toLowerCase() === selectedObjective.target_property?.trim().toLowerCase()
                  return (
                    <option key={m.id} value={m.id}>
                      {m.name} [{m.target_property}] [{m.status}]{matches ? ' ★ Matches Objective' : ''}
                    </option>
                  )
                })}
              </select>
              {selectedModel && !isModelValidated && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                  <div style={{ fontSize: '0.8125rem', color: '#dc2626' }}>
                    Status '{selectedModel.status}' blocked — approve model first.
                  </div>
                  <button
                    type="button"
                    onClick={async () => {
                      try {
                        const updated = await mlService.approveModel(selectedModel.id)
                        setModels(models.map((m) => (m.id === selectedModel.id ? updated : m)))
                      } catch (err: any) {
                        setError(err?.message || 'Failed to approve model.')
                      }
                    }}
                    className="gs-btn gs-btn-emerald"
                    style={{ padding: '3px 8px', fontSize: '0.75rem', fontWeight: 600 }}
                  >
                    ✓ Approve Now
                  </button>
                </div>
              )}
              {hasTargetMismatch && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6, fontSize: '0.8125rem', color: '#d97706' }}>
                  <AlertTriangle size={14} className="shrink-0" />
                  <span>
                    Target mismatch: Model predicts <strong>{selectedModel?.target_property}</strong>, but objective requires <strong>{selectedObjective?.target_property}</strong>.
                  </span>
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
                disabled={loading || !isModelValidated || hasTargetMismatch}
                className="gs-btn gs-btn-emerald"
                style={{ width: '100%', justifyContent: 'center', display: 'inline-flex', alignItems: 'center', gap: 6 }}
                title={hasTargetMismatch ? `Selected model target (${selectedModel?.target_property}) does not match objective (${selectedObjective?.target_property})` : undefined}
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
                    cand.status === 'REJECTED' ? 'critical' :
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
                    {Object.entries(cand.parameter_set).map(([k, v]) => {
                      const label = formatParamKey(k)
                      const unit = getParamUnit(k)
                      return (
                        <div key={k} className="gs-param-item" title={`${label} (${k}): ${Number(v).toFixed(2)} ${unit}`}>
                          <div className="gs-param-name">{label}</div>
                          <div className="gs-param-value" style={{ color: '#0d9488' }}>
                            {Number(v).toFixed(2)}
                            {unit && (
                              <span style={{ fontSize: '0.6875rem', fontWeight: 500, color: 'var(--color-text-secondary)', marginLeft: 3 }}>
                                {unit}
                              </span>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {cand.modified_parameter_set && (
                    <div style={{ marginTop: 12, padding: '10px 12px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 'var(--radius-md)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#92400e', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Edit2 className="w-3.5 h-3.5 text-amber-700" /> Researcher Modified Parameters (Original Preserved):
                      </div>
                      <div className="gs-param-grid">
                        {Object.entries(cand.modified_parameter_set).map(([k, v]) => {
                          const label = formatParamKey(k)
                          const unit = getParamUnit(k)
                          return (
                            <div key={k} className="gs-param-item" style={{ background: '#fef3c7', borderColor: '#fcd34d' }} title={`${label} (${k}): ${Number(v).toFixed(2)} ${unit}`}>
                              <div className="gs-param-name">{label}</div>
                              <div className="gs-param-value" style={{ color: '#b45309' }}>
                                {Number(v).toFixed(2)}
                                {unit && (
                                  <span style={{ fontSize: '0.6875rem', fontWeight: 500, color: 'var(--color-text-secondary)', marginLeft: 3 }}>
                                    {unit}
                                  </span>
                                )}
                              </div>
                            </div>
                          )
                        })}
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
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--color-border-light)', flexWrap: 'wrap' }}>
                <button
                  onClick={() => handleOpenModifyModal(cand)}
                  disabled={cand.status === 'EXPERIMENT_CREATED'}
                  className="gs-btn gs-btn-outline gs-btn-sm"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                >
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
                  onClick={() => handleReject(cand.id)}
                  disabled={cand.status === 'REJECTED' || cand.status === 'EXPERIMENT_CREATED'}
                  className="gs-btn gs-btn-outline gs-btn-sm"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#dc2626', borderColor: '#fca5a5' }}
                >
                  <X className="w-3.5 h-3.5" /> Reject
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
                  <label className="form-label" style={{ fontWeight: 600 }}>
                    {formatParamKey(paramName)} <span style={{ color: 'var(--color-text-secondary)', fontWeight: 400 }}>({paramName})</span> {getParamUnit(paramName) ? `[${getParamUnit(paramName)}]` : ''}
                  </label>
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

      {/* Top-Right Floating Toast Notifications */}
      <div className="gs-toast-container">
        {toasts.map((toast) => {
          const isSuccess = toast.type === 'success'
          const isError = toast.type === 'error'
          const isWarning = toast.type === 'warning'
          const isInfo = toast.type === 'info'

          const accentColor = isSuccess ? '#10b981' : isError ? '#ef4444' : isWarning ? '#f59e0b' : '#6366f1'
          const bgLight = isSuccess ? '#ecfdf5' : isError ? '#fef2f2' : isWarning ? '#fffbeb' : '#eef2ff'

          return (
            <div
              key={toast.id}
              className="gs-toast-card"
              style={{ borderLeft: `5px solid ${accentColor}` }}
            >
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  background: bgLight,
                  color: accentColor,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  marginTop: 1,
                }}
              >
                {isSuccess && <CheckCircle2 size={18} />}
                {isError && <XCircle size={18} />}
                {isWarning && <Edit2 size={17} />}
                {isInfo && <FlaskConical size={18} />}
              </div>
              <div style={{ flex: 1, minWidth: 0, paddingRight: 16 }}>
                <div style={{ fontWeight: 700, fontSize: '0.875rem', color: '#0f172a', marginBottom: 2 }}>
                  {toast.title}
                </div>
                <div style={{ fontSize: '0.8125rem', color: '#64748b', lineHeight: 1.4 }}>
                  {toast.message}
                </div>
              </div>
              <button
                onClick={() => dismissToast(toast.id)}
                style={{
                  position: 'absolute',
                  top: 10,
                  right: 10,
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#94a3b8',
                  padding: 4,
                  borderRadius: 4,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
                title="Dismiss"
              >
                <X size={14} />
              </button>
              <div className="gs-toast-timer" style={{ color: accentColor }} />
            </div>
          )
        })}
      </div>
    </div>
  )
}
