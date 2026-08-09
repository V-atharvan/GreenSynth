/**
 * GreenSynth Analytics — Phase 19 Multi-Project Research Platform
 */

import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import type { ProjectCreate, ProjectSummary } from '@/types'
import { projectService } from '@/services/projectService'
import {
  projectConfigService,
  ProjectMatrixRow,
  PropertyComparabilityResult,
} from '@/services/projectConfigService'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { EmptyState } from '@/components/EmptyState'
import { StatusBadge } from '@/components/StatusBadge'
import { PageHeader } from '@/components/PageHeader'
import { ConfirmModal } from '@/components/ConfirmModal'
import type { ApiError } from '@/types'
import {
  FolderKanban,
  Layers,
  Filter,
  Search,
  FlaskConical,
  TestTube2,
  CheckCircle2,
  AlertTriangle,
  Info,
  ArrowRightLeft,
  X,
} from 'lucide-react'

const EMPTY_FORM: ProjectCreate = {
  project_code: '',
  name: '',
  material: '',
  extract: '',
  solvent: '',
  synthesis_method: '',
  description: '',
}

export default function Projects() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [matrix, setMatrix] = useState<ProjectMatrixRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [solventFilter, setSolventFilter] = useState<string>('ALL')
  const [methodFilter, setMethodFilter] = useState<string>('ALL')
  const [materialFilter, setMaterialFilter] = useState<string>('ALL')

  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState<ProjectCreate>(EMPTY_FORM)
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [archiveTarget, setArchiveTarget] = useState<ProjectSummary | null>(null)
  const [archiving, setArchiving] = useState(false)

  // Property Comparability Checker Modal State
  const [showCompareModal, setShowCompareModal] = useState(false)
  const [sourceCode, setSourceCode] = useState('P7')
  const [targetCode, setTargetCode] = useState('P8')
  const [sourceProp, setSourceProp] = useState('electrical_conductivity')
  const [targetProp, setTargetProp] = useState('electrical_conductivity')
  const [compResult, setCompResult] = useState<PropertyComparabilityResult | null>(null)
  const [evaluatingComp, setEvaluatingComp] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [projList, matRows] = await Promise.all([
        projectService.getAll(),
        projectConfigService.getMatrix(),
      ])
      setProjects(projList)
      setMatrix(matRows)
    } catch (e: unknown) {
      setError((e as ApiError)?.message ?? 'Failed to load project configuration platform.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const filteredMatrix = matrix.filter((row) => {
    const matchesSearch = `${row.project_code} ${row.project_name} ${row.material} ${row.synthesis_method} ${row.extract} ${row.solvent}`
      .toLowerCase()
      .includes(search.toLowerCase())

    const matchesSolvent = solventFilter === 'ALL' || row.solvent.toUpperCase() === solventFilter.toUpperCase()
    const matchesMethod = methodFilter === 'ALL' || row.synthesis_method.toUpperCase().includes(methodFilter.toUpperCase())
    const matchesMaterial = materialFilter === 'ALL' || row.material.toUpperCase().includes(materialFilter.toUpperCase())

    return matchesSearch && matchesSolvent && matchesMethod && matchesMaterial
  })

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    setSaving(true)
    try {
      await projectService.create(form)
      setShowCreate(false)
      setForm(EMPTY_FORM)
      await fetchData()
    } catch (e: unknown) {
      setFormError((e as ApiError)?.message ?? 'Failed to create project.')
    } finally {
      setSaving(false)
    }
  }

  const handleArchive = async () => {
    if (!archiveTarget) return
    setArchiving(true)
    try {
      await projectService.archive(archiveTarget.id)
      setArchiveTarget(null)
      await fetchData()
    } catch {
      // keep modal open on error
    } finally {
      setArchiving(false)
    }
  }

  const handleEvaluateComparability = async () => {
    setEvaluatingComp(true)
    try {
      const res = await projectConfigService.compareProperties(
        sourceCode,
        targetCode,
        sourceProp,
        targetProp
      )
      setCompResult(res)
    } catch (err) {
      console.error('Failed to evaluate property comparability:', err)
    } finally {
      setEvaluatingComp(false)
    }
  }

  return (
    <div className="gs-page">
      {/* Header */}
      <div className="gs-page-header">
        <div>
          <div style={{ marginBottom: 4 }}>
            <span className="gs-badge blue">Phase 19 — Multi-Project Research Platform</span>
            <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginLeft: 10 }}>Configuration-Driven 8-Project Engine</span>
          </div>
          <div className="gs-page-title">
            <div className="gs-page-title-icon indigo">
              <FolderKanban className="w-5 h-5 text-indigo-600" />
            </div>
            Multi-Project Synthesis Matrix &amp; Platform
          </div>
          <p className="gs-page-subtitle">
            Configuration-driven platform representing all eight semiconductor synthesis projects (P1 to P8) with shared domain engines and explicit cross-project scientific rules.
          </p>
        </div>

        <div className="gs-header-actions" style={{ display: 'flex', gap: 8 }}>
          <button
            className="gs-btn gs-btn-outline"
            onClick={() => setShowCompareModal(true)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
          >
            <ArrowRightLeft className="w-4 h-4 text-emerald-600" /> Check Property Comparability
          </button>
          <button className="gs-btn gs-btn-indigo" onClick={() => setShowCreate(true)}>
            + New Project
          </button>
        </div>
      </div>

      {/* Synthesis Matrix Info Banner */}
      <div className="gs-info-banner blue">
        <div className="gs-info-banner-icon">
          <Info className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <div className="gs-info-banner-title">Configuration Engine Architecture</div>
          <div className="gs-info-banner-text">
            Projects P1–P8 reuse shared synthesis methods (<code>SolGelMethod</code>, <code>HydrothermalMethod</code>, <code>SprayPyrolysisMethod</code>). Differences in material, solvent, and biomass are fully <strong>configuration-driven</strong> with immutable version snapshot logging.
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="gs-panel">
        <div className="gs-panel-body" style={{ display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center' }}>
          <div style={{ flex: 1, minWidth: 240, display: 'flex', alignItems: 'center', gap: 8, background: '#fff', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '6px 12px' }}>
            <Search className="w-4 h-4 text-gray-400 shrink-0" />
            <input
              type="text"
              placeholder="Search by code, material, solvent, or method..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ border: 'none', outline: 'none', width: '100%', fontSize: '0.875rem' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Filter className="w-4 h-4 text-indigo-600" />
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>Solvent:</span>
            <select
              value={solventFilter}
              onChange={(e) => setSolventFilter(e.target.value)}
              className="gs-select"
            >
              <option value="ALL">All Solvents</option>
              <option value="Ethanol">Ethanol</option>
              <option value="Acetone">Acetone</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>Method:</span>
            <select
              value={methodFilter}
              onChange={(e) => setMethodFilter(e.target.value)}
              className="gs-select"
            >
              <option value="ALL">All Methods</option>
              <option value="Sol-gel">Sol-gel (P1, P2)</option>
              <option value="Hydrothermal">Hydrothermal (P3–P6)</option>
              <option value="Spray Pyrolysis">Spray Pyrolysis (P7, P8)</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>Material:</span>
            <select
              value={materialFilter}
              onChange={(e) => setMaterialFilter(e.target.value)}
              className="gs-select"
            >
              <option value="ALL">All Materials</option>
              <option value="CuO">CuO (Copper Oxide)</option>
              <option value="Silica">Silica / Silicon (Rice Husk)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Content */}
      {loading ? (
        <LoadingSpinner message="Loading multi-project synthesis matrix..." />
      ) : error ? (
        <ErrorMessage error={error} onRetry={fetchData} />
      ) : (
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <Layers className="w-4 h-4 text-indigo-600" /> Laboratory Projects Matrix ({filteredMatrix.length} of 8 Projects)
            </span>
          </div>

          <div className="gs-table-wrapper">
            <table className="gs-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Project Name</th>
                  <th>Material System</th>
                  <th>Biomass Source</th>
                  <th>Plant Extract</th>
                  <th>Solvent</th>
                  <th>Synthesis Method</th>
                  <th>Exps</th>
                  <th>Samples</th>
                  <th>Model Status</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredMatrix.map((row) => {
                  const proj = projects.find((p) => p.project_code === row.project_code)
                  return (
                    <tr key={row.project_code}>
                      <td>
                        {proj ? (
                          <Link to={`/projects/${proj.id}`} style={{ fontWeight: 800, color: '#4f46e5', textDecoration: 'none', fontFamily: 'var(--font-mono)' }}>
                            {row.project_code}
                          </Link>
                        ) : (
                          <span style={{ fontWeight: 800, fontFamily: 'var(--font-mono)' }}>{row.project_code}</span>
                        )}
                      </td>
                      <td style={{ maxWidth: 260, fontWeight: 600 }}>{row.project_name}</td>
                      <td>
                        <span className={`gs-badge ${row.material.includes('Silica') ? 'purple' : 'blue'}`}>
                          {row.material}
                        </span>
                      </td>
                      <td style={{ color: row.biomass !== '—' ? '#0d9488' : 'var(--color-text-secondary)', fontWeight: row.biomass !== '—' ? 700 : 400 }}>
                        {row.biomass}
                      </td>
                      <td>{row.extract}</td>
                      <td>
                        <span className={`gs-chip ${row.solvent === 'Ethanol' ? 'stable' : 'warning'}`}>
                          {row.solvent}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600, color: 'var(--color-text)' }}>{row.synthesis_method}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{row.experiment_count}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{row.sample_count}</td>
                      <td>
                        <span className={`gs-chip ${row.model_status === 'APPROVED' ? 'production' : 'muted'}`}>
                          {row.model_status}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {proj && (
                          <button
                            className="gs-btn gs-btn-outline gs-btn-sm"
                            onClick={() => navigate(`/projects/${proj.id}`)}
                          >
                            View
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Property Comparability Checker Modal */}
      {showCompareModal && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 640 }}>
            <div className="modal-header">
              <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <ArrowRightLeft className="w-4 h-4 text-emerald-600" /> Property Comparability Engine (Phase 19 Rule #27)
              </div>
              <button className="modal-close" onClick={() => setShowCompareModal(false)}>
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                Evaluates scientific comparability rules before comparing results across projects. Prevents invalid scientific comparisons between incompatible material systems or synthesis methods.
              </p>

              <div className="gs-form-row">
                <div className="gs-field">
                  <label className="gs-label">Source Project</label>
                  <select value={sourceCode} onChange={(e) => setSourceCode(e.target.value)} className="gs-input">
                    {matrix.map((m) => (
                      <option key={m.project_code} value={m.project_code}>
                        {m.project_code} — {m.material} ({m.synthesis_method})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="gs-field">
                  <label className="gs-label">Target Project</label>
                  <select value={targetCode} onChange={(e) => setTargetCode(e.target.value)} className="gs-input">
                    {matrix.map((m) => (
                      <option key={m.project_code} value={m.project_code}>
                        {m.project_code} — {m.material} ({m.synthesis_method})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="gs-form-row">
                <div className="gs-field">
                  <label className="gs-label">Source Property</label>
                  <input
                    type="text"
                    value={sourceProp}
                    onChange={(e) => setSourceProp(e.target.value)}
                    className="gs-input"
                  />
                </div>

                <div className="gs-field">
                  <label className="gs-label">Target Property</label>
                  <input
                    type="text"
                    value={targetProp}
                    onChange={(e) => setTargetProp(e.target.value)}
                    className="gs-input"
                  />
                </div>
              </div>

              <button
                onClick={handleEvaluateComparability}
                disabled={evaluatingComp}
                className="gs-btn gs-btn-emerald"
                style={{ width: '100%', justifyContent: 'center' }}
              >
                {evaluatingComp ? 'Evaluating Rules...' : '⚡ Check Scientific Comparability'}
              </button>

              {compResult && (
                <div style={{ marginTop: 8 }}>
                  <div
                    className={`gs-alert ${
                      compResult.comparability_status === 'COMPARABLE'
                        ? 'success'
                        : compResult.comparability_status === 'COMPARABLE_WITH_WARNING'
                        ? 'warning'
                        : 'error'
                    }`}
                  >
                    <div style={{ fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                      {compResult.comparability_status === 'COMPARABLE' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                      )}
                      Status: {compResult.comparability_status}
                    </div>
                    <div style={{ fontSize: '0.8125rem' }}>{compResult.reason}</div>
                  </div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowCompareModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Create Project Modal ────────────────────────── */}
      {showCreate && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 640 }}>
            <div className="modal-header">
              <h2 className="modal-title">Create Research Project</h2>
              <button
                className="modal-close"
                onClick={() => { setShowCreate(false); setFormError(null); setForm(EMPTY_FORM) }}
                aria-label="Close"
              >✕</button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="modal-body">
                {formError && <ErrorMessage error={formError} />}

                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label required" htmlFor="code">Project Code</label>
                    <input
                      id="code"
                      className="form-control"
                      placeholder="e.g. P9"
                      value={form.project_code}
                      onChange={(e) => setForm({ ...form, project_code: e.target.value })}
                      required
                      maxLength={32}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label required" htmlFor="material">Material</label>
                    <input
                      id="material"
                      className="form-control"
                      placeholder="e.g. CuO"
                      value={form.material}
                      onChange={(e) => setForm({ ...form, material: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group span-2">
                    <label className="form-label required" htmlFor="pname">Project Name</label>
                    <input
                      id="pname"
                      className="form-control"
                      placeholder="Full descriptive project name"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label required" htmlFor="extract">Extract</label>
                    <input
                      id="extract"
                      className="form-control"
                      placeholder="e.g. Mulberry"
                      value={form.extract}
                      onChange={(e) => setForm({ ...form, extract: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label required" htmlFor="solvent">Solvent</label>
                    <input
                      id="solvent"
                      className="form-control"
                      placeholder="e.g. Ethanol"
                      value={form.solvent}
                      onChange={(e) => setForm({ ...form, solvent: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label required" htmlFor="method">Synthesis Method</label>
                    <input
                      id="method"
                      className="form-control"
                      placeholder="e.g. Spray Pyrolysis"
                      value={form.synthesis_method}
                      onChange={(e) => setForm({ ...form, synthesis_method: e.target.value })}
                      required
                    />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => { setShowCreate(false); setFormError(null); setForm(EMPTY_FORM) }}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Creating…' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmModal
        isOpen={!!archiveTarget}
        title="Archive Project"
        message={`Archive "${archiveTarget?.name}"? The project will be hidden but not deleted.`}
        confirmLabel="Archive Project"
        isLoading={archiving}
        onConfirm={handleArchive}
        onCancel={() => setArchiveTarget(null)}
      />
    </div>
  )
}
