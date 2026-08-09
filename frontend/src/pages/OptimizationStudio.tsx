/**
 * GreenSynth Analytics — Phase 18 Evidence-Based Optimization Studio
 */

import React, { useEffect, useState } from 'react'
import { projectService } from '@/services/projectService'
import { mlService, MLModel } from '@/services/mlService'
import {
  optimizationService,
  OptimizationObjective,
  OptimizationConstraint,
  OptimizationRun,
  OptimizationCandidate,
  OptimizationReport,
} from '@/services/optimizationService'
import type { ProjectSummary } from '@/types'
import {
  Ruler,
  Target,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Zap,
  FlaskConical,
  Download,
  BarChart2,
  Settings,
  Layers,
  Search,
  Info,
  Check,
  X,
} from 'lucide-react'

export default function OptimizationStudio() {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')

  const [objectives, setObjectives] = useState<OptimizationObjective[]>([])
  const [selectedObjectiveId, setSelectedObjectiveId] = useState<string>('')
  const [newObjProperty, setNewObjProperty] = useState<string>('conductivity_s_cm')
  const [newObjDirection, setNewObjDirection] = useState<'MAXIMIZE' | 'MINIMIZE' | 'TARGET'>('MAXIMIZE')
  const [newObjTargetVal, setNewObjTargetVal] = useState<string>('5.0')
  const [newObjWeight, setNewObjWeight] = useState<number>(1.0)

  const [constraints, setConstraints] = useState<OptimizationConstraint[]>([])
  const [models, setModels] = useState<MLModel[]>([])
  const [selectedModelId, setSelectedModelId] = useState<string>('')
  const [generationMethod, setGenerationMethod] = useState<'GRID_SEARCH' | 'RANDOM_SEARCH' | 'MODEL_GUIDED_SEARCH'>('RANDOM_SEARCH')
  const [requestedCount, setRequestedCount] = useState<number>(10)
  const [randomSeed, setRandomSeed] = useState<number>(42)
  const [allowOutOfDomain, setAllowOutOfDomain] = useState<boolean>(false)

  const [runs, setRuns] = useState<OptimizationRun[]>([])
  const [activeRun, setActiveRun] = useState<OptimizationRun | null>(null)
  const [selectedCandidates, setSelectedCandidates] = useState<string[]>([])
  const [reportModal, setReportModal] = useState<OptimizationReport | null>(null)

  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  useEffect(() => {
    async function loadProjects() {
      try {
        const projs = await projectService.getAll()
        setProjects(projs)
        if (projs.length > 0) setSelectedProjectId(projs[0].id)
      } catch (err) {
        console.error('Failed to load projects:', err)
      }
    }
    loadProjects()
  }, [])

  useEffect(() => {
    if (!selectedProjectId) return
    async function loadProjectData() {
      setLoading(true)
      try {
        const [objs, constrs, mdls, runList] = await Promise.all([
          optimizationService.listObjectives(selectedProjectId),
          optimizationService.listConstraints(selectedProjectId),
          mlService.getModels(),
          optimizationService.listRuns(selectedProjectId),
        ])
        setObjectives(objs)
        if (objs.length > 0 && objs[0].id) setSelectedObjectiveId(objs[0].id)
        setConstraints(constrs)
        setModels(mdls)
        if (mdls.length > 0) setSelectedModelId(mdls[0].id)
        setRuns(runList)
        if (runList.length > 0) setActiveRun(runList[0])
      } catch (err) {
        console.error('Failed to load optimization data:', err)
      } finally {
        setLoading(false)
      }
    }
    loadProjectData()
  }, [selectedProjectId])

  const handleCreateObjective = async () => {
    if (!selectedProjectId) return
    setError(null)
    setSuccessMsg(null)
    try {
      const created = await optimizationService.createObjective({
        project_id: selectedProjectId,
        name: `${newObjDirection} ${newObjProperty}`,
        target_property: newObjProperty,
        direction: newObjDirection,
        target_value: newObjDirection === 'TARGET' ? parseFloat(newObjTargetVal) : undefined,
        weight: newObjWeight,
      })
      setObjectives([created, ...objectives])
      if (created.id) setSelectedObjectiveId(created.id)
      setSuccessMsg(`Created optimization objective '${created.name}'!`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to create objective.')
    }
  }

  const handleRunCandidateGeneration = async () => {
    if (!selectedProjectId || !selectedObjectiveId || !selectedModelId) {
      setError('Please select a project, objective, and model.')
      return
    }
    setLoading(true)
    setError(null)
    setSuccessMsg(null)

    try {
      const run = await optimizationService.createRun({
        project_id: selectedProjectId,
        objective_id: selectedObjectiveId,
        model_id: selectedModelId,
        generation_method: generationMethod,
        requested_candidate_count: requestedCount,
        random_seed: randomSeed,
        allow_out_of_domain: allowOutOfDomain,
      })
      setActiveRun(run)
      setRuns([run, ...runs])
      setSuccessMsg(`Generated ${run.candidates.length} candidate experimental conditions!`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Candidate generation failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectCandidate = async (candidateId: string) => {
    try {
      const updated = await optimizationService.selectCandidate(candidateId, 'Selected by researcher for laboratory trial.')
      if (activeRun) {
        setActiveRun({
          ...activeRun,
          candidates: activeRun.candidates.map((c) => (c.id === candidateId ? updated : c)),
        })
      }
      setSuccessMsg('Candidate selected by researcher!')
    } catch (err) {
      console.error('Failed to select candidate:', err)
    }
  }

  const handleCreateExperiment = async (candidateId: string) => {
    try {
      const res = await optimizationService.createProposedExperiment(candidateId)
      if (activeRun) {
        setActiveRun({
          ...activeRun,
          candidates: activeRun.candidates.map((c) =>
            c.id === candidateId ? { ...c, status: 'CONVERTED_TO_EXPERIMENT' } : c
          ),
        })
      }
      setSuccessMsg(`Created PLANNED experiment ${res.experiment_code}! Proposed conditions intact; lab actuals empty.`)
    } catch (err) {
      console.error('Failed to create experiment:', err)
    }
  }

  const handleViewReport = async () => {
    if (!activeRun) return
    try {
      const rep = await optimizationService.getReport(activeRun.id)
      setReportModal(rep)
    } catch (err) {
      console.error('Failed to load report:', err)
    }
  }

  const selectedModel = models.find((m) => m.id === selectedModelId)
  const isModelCritical = selectedModel && selectedModel.status === 'RETIRED'

  return (
    <div className="gs-page">

      {/* Header */}
      <div className="gs-page-header">
        <div>
          <div style={{ marginBottom: 4 }}>
            <span className="gs-badge blue">Phase 18 — Evidence-Based Optimization</span>
            <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginLeft: 10 }}>Candidate Generation &amp; Ranking Engine</span>
          </div>
          <div className="gs-page-title">
            <div className="gs-page-title-icon amber">
              <Ruler className="w-5 h-5 text-amber-600" />
            </div>
            Evidence-Based Optimization Studio
          </div>
          <p className="gs-page-subtitle">
            Systematically formulate objective targets, set parameter &amp; property constraints, validate model readiness, and rank promising experimental candidate conditions.
          </p>
        </div>

        <div className="gs-header-actions">
          <div className="gs-field">
            <label className="gs-label">Active Project</label>
            <select
              className="gs-select"
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Scientific Principle Disclaimer Banner */}
      <div className="gs-info-banner blue">
        <div className="gs-info-banner-icon">
          <Info className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <div className="gs-info-banner-title">Mandatory Scientific Principle</div>
          <div className="gs-info-banner-text">
            Optimization results represent <em>promising candidate experimental conditions</em> based on available data and validated models. Candidate values are <strong>model-predicted estimates</strong> and require physical laboratory validation.
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

      {/* Grid layout: Config + Controls */}
      <div className="gs-two-col">

        {/* 1. Define Objective & Constraints */}
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <Target className="w-4 h-4 text-emerald-600" /> 1. Define Objective &amp; Weights
            </span>
          </div>
          <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div className="gs-form-row">
              <div className="gs-field">
                <label className="gs-label">Target Property</label>
                <select
                  value={newObjProperty}
                  onChange={(e) => setNewObjProperty(e.target.value)}
                  className="gs-input"
                >
                  <option value="conductivity_s_cm">Electrical Conductivity (S/cm)</option>
                  <option value="band_gap_ev">Optical Band Gap (eV)</option>
                  <option value="crystallite_size_nm">Crystallite Size (nm)</option>
                  <option value="film_thickness_nm">Film Thickness (nm)</option>
                </select>
              </div>

              <div className="gs-field">
                <label className="gs-label">Direction</label>
                <select
                  value={newObjDirection}
                  onChange={(e) => setNewObjDirection(e.target.value as any)}
                  className="gs-input"
                >
                  <option value="MAXIMIZE">MAXIMIZE (Higher is better)</option>
                  <option value="MINIMIZE">MINIMIZE (Lower is better)</option>
                  <option value="TARGET">TARGET (Target value match)</option>
                </select>
              </div>

              {newObjDirection === 'TARGET' && (
                <div className="gs-field">
                  <label className="gs-label">Target Value</label>
                  <input
                    type="number"
                    step="any"
                    value={newObjTargetVal}
                    onChange={(e) => setNewObjTargetVal(e.target.value)}
                    className="gs-input"
                  />
                </div>
              )}

              <div className="gs-field">
                <label className="gs-label">Weight (0.1 - 1.0)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="1.0"
                  value={newObjWeight}
                  onChange={(e) => setNewObjWeight(parseFloat(e.target.value) || 1.0)}
                  className="gs-input"
                />
              </div>
            </div>

            <button
              onClick={handleCreateObjective}
              className="gs-btn gs-btn-emerald"
              style={{ width: 'fit-content' }}
            >
              + Create Objective
            </button>

            {objectives.length > 0 && (
              <div>
                <div className="gs-label" style={{ marginBottom: 8 }}>Active Objectives List</div>
                <div className="gs-table-wrapper">
                  <table className="gs-table">
                    <thead>
                      <tr>
                        <th>Objective Name</th>
                        <th>Target</th>
                        <th>Direction</th>
                        <th>Weight</th>
                        <th>Select</th>
                      </tr>
                    </thead>
                    <tbody>
                      {objectives.map((o) => (
                        <tr key={o.id} style={{ background: selectedObjectiveId === o.id ? '#ecfdf5' : undefined }}>
                          <td style={{ fontWeight: 600 }}>{o.name}</td>
                          <td><span className="gs-badge indigo">{o.target_property}</span></td>
                          <td style={{ fontWeight: 700, color: '#059669' }}>{o.direction}</td>
                          <td style={{ fontFamily: 'var(--font-mono)' }}>{o.weight}</td>
                          <td>
                            <input
                              type="radio"
                              name="selected_objective"
                              checked={selectedObjectiveId === o.id}
                              onChange={() => setSelectedObjectiveId(o.id!)}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 2. Select Model & Algorithm Controls */}
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <Settings className="w-4 h-4 text-indigo-600" /> 2. Validated Model &amp; Search Space
            </span>
          </div>
          <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            <div className="gs-field">
              <label className="gs-label">Select Validated ML Model</label>
              <select
                value={selectedModelId}
                onChange={(e) => setSelectedModelId(e.target.value)}
                className="gs-input"
              >
                {models.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.model_type}) — Target: {m.target_property} [{m.status}]
                  </option>
                ))}
              </select>
            </div>

            {selectedModel && (
              <div style={{ padding: '12px 14px', background: '#f8fafc', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
                  <span style={{ color: 'var(--color-text-secondary)' }}>Model Gate Check:</span>
                  <span className={`gs-chip ${isModelCritical ? 'critical' : 'stable'}`}>
                    {isModelCritical ? 'BLOCKED (RETIRED)' : 'PASSED (APPROVED)'}
                  </span>
                </div>
              </div>
            )}

            <div className="gs-form-row">
              <div className="gs-field">
                <label className="gs-label">Search Strategy</label>
                <select
                  value={generationMethod}
                  onChange={(e) => setGenerationMethod(e.target.value as any)}
                  className="gs-input"
                >
                  <option value="RANDOM_SEARCH">RANDOM SEARCH (Reproducible seed)</option>
                  <option value="GRID_SEARCH">GRID SEARCH (Factorial step combinations)</option>
                  <option value="MODEL_GUIDED_SEARCH">MODEL-GUIDED SEARCH (Model prediction guided)</option>
                </select>
              </div>

              <div className="gs-field">
                <label className="gs-label">Candidate Count</label>
                <input
                  type="number"
                  value={requestedCount}
                  onChange={(e) => setRequestedCount(parseInt(e.target.value) || 10)}
                  min={1}
                  max={100}
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

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                id="out_of_domain_cb"
                checked={allowOutOfDomain}
                onChange={(e) => setAllowOutOfDomain(e.target.checked)}
              />
              <label htmlFor="out_of_domain_cb" style={{ fontSize: '0.8125rem', color: 'var(--color-text)' }}>
                Allow Out-Of-Domain candidates (with explicit reliability warnings)
              </label>
            </div>

            <button
              onClick={handleRunCandidateGeneration}
              disabled={loading || isModelCritical || !selectedObjectiveId || !selectedModelId}
              className="gs-btn gs-btn-indigo"
              style={{ width: '100%', justifyContent: 'center', display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              <Zap className="w-4 h-4" />
              {loading ? 'Generating Candidates…' : '⚡ Run Candidate Generation'}
            </button>
          </div>
        </div>

      </div>

      {/* Candidates Results Table */}
      {activeRun && (
        <div className="gs-panel">
          <div className="gs-panel-header">
            <div>
              <span className="gs-panel-title" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <BarChart2 className="w-4 h-4 text-emerald-600" /> Ranked Promising Candidate Conditions ({activeRun.candidates.length})
              </span>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
                Run ID: <code style={{ color: '#0d9488' }}>{activeRun.id.substring(0, 8)}</code> | Seed: {activeRun.random_seed} | Feasible: {activeRun.feasible_candidate_count}
              </p>
            </div>
            <button
              onClick={handleViewReport}
              className="gs-btn gs-btn-outline gs-btn-sm"
              style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
            >
              <Download className="w-3.5 h-3.5" /> View Optimization Report
            </button>
          </div>

          <div className="gs-table-wrapper">
            <table className="gs-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Candidate Params</th>
                  <th>Predicted Target</th>
                  <th>Uncertainty Bounds</th>
                  <th>Objective Score</th>
                  <th>Score Breakdown</th>
                  <th>Domain</th>
                  <th>Novelty</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {activeRun.candidates.map((c) => {
                  const targetProp = Object.keys(c.predictions)[0] || 'target'
                  const predVal = c.predictions[targetProp]
                  const uncert = c.uncertainties[targetProp]
                  return (
                    <tr key={c.id}>
                      <td style={{ fontWeight: 800, color: c.rank <= 3 ? '#059669' : 'var(--color-text)' }}>
                        #{c.rank}
                      </td>
                      <td>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, fontSize: '0.75rem' }}>
                          {Object.entries(c.parameter_values).slice(0, 4).map(([kp, vp]) => (
                            <span key={kp} style={{ fontFamily: 'var(--font-mono)' }}>
                              {kp.replace('_', ' ')}: <strong>{vp}</strong>
                            </span>
                          ))}
                        </div>
                      </td>
                      <td style={{ fontWeight: 700, color: '#0d9488', fontFamily: 'var(--font-mono)' }}>
                        {predVal} {uncert?.unit || ''}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                        {uncert?.lower_bound !== undefined ? `[${uncert.lower_bound}, ${uncert.upper_bound}]` : 'N/A'}
                      </td>
                      <td style={{ fontWeight: 800, fontSize: '1rem', color: '#059669', fontFamily: 'var(--font-mono)' }}>
                        {c.objective_score.toFixed(4)}
                      </td>
                      <td>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}>
                          Total: {c.objective_score}
                        </span>
                      </td>
                      <td>
                        <span className={`gs-chip ${c.domain_status === 'IN_DOMAIN' ? 'stable' : c.domain_status === 'NEAR_BOUNDARY' ? 'warning' : 'critical'}`}>
                          {c.domain_status}
                        </span>
                      </td>
                      <td>
                        <span className="gs-chip info">{c.novelty_category}</span>
                      </td>
                      <td>
                        <span className={`gs-chip ${c.status === 'CONVERTED_TO_EXPERIMENT' ? 'production' : c.status === 'SELECTED' ? 'stable' : 'muted'}`}>
                          {c.status}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <span style={{ display: 'inline-flex', gap: 6 }}>
                          {c.status !== 'SELECTED' && c.status !== 'CONVERTED_TO_EXPERIMENT' && (
                            <button
                              onClick={() => handleSelectCandidate(c.id)}
                              className="gs-btn gs-btn-emerald gs-btn-sm"
                            >
                              ✓ Select
                            </button>
                          )}
                          {c.status !== 'CONVERTED_TO_EXPERIMENT' && (
                            <button
                              onClick={() => handleCreateExperiment(c.id)}
                              className="gs-btn gs-btn-indigo gs-btn-sm"
                            >
                              🔬 Create Experiment
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

      {/* Report Modal */}
      {reportModal && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 720 }}>
            <div className="modal-header">
              <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Download className="w-4 h-4 text-emerald-600" /> Optimization Report — {reportModal.project_code}
              </div>
              <button className="modal-close" onClick={() => setReportModal(null)}>
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div className="gs-alert warning">
                ⚠️ {reportModal.disclaimer}
              </div>
              <div className="gs-param-grid">
                <div className="gs-param-item">
                  <div className="gs-param-name">Project</div>
                  <div className="gs-param-value">{reportModal.project_name}</div>
                </div>
                <div className="gs-param-item">
                  <div className="gs-param-name">Objective</div>
                  <div className="gs-param-value">{reportModal.objective_name} ({reportModal.direction})</div>
                </div>
                <div className="gs-param-item">
                  <div className="gs-param-name">Validated Model</div>
                  <div className="gs-param-value">{reportModal.model_name} (v{reportModal.model_version})</div>
                </div>
                <div className="gs-param-item">
                  <div className="gs-param-name">Feasible Candidates</div>
                  <div className="gs-param-value">{reportModal.feasible_candidates_count} / {reportModal.total_candidates_generated}</div>
                </div>
              </div>

              <div>
                <div className="gs-label" style={{ marginBottom: 8 }}>Top Ranked Promising Candidates Summary</div>
                <div className="gs-table-wrapper">
                  <table className="gs-table">
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Parameters</th>
                        <th>Predicted Score</th>
                        <th>Domain</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reportModal.top_candidates.map((c) => (
                        <tr key={c.id}>
                          <td style={{ fontWeight: 700 }}>#{c.rank}</td>
                          <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                            {JSON.stringify(c.parameter_values)}
                          </td>
                          <td style={{ fontWeight: 700, color: '#059669' }}>{c.objective_score.toFixed(4)}</td>
                          <td><span className="gs-chip stable">{c.domain_status}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setReportModal(null)}>Close Report</button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
