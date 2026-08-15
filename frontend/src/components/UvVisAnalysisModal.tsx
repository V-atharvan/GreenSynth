/**
 * GreenSynth Analytics — UV-Vis & Tauc Analysis Dashboard Modal
 *
 * Provides:
 *  1. Transition Model selection (Direct Allowed n=2 vs Indirect Allowed n=0.5)
 *  2. Sample thickness input (optional) with missing thickness warning display
 *  3. Configurable Tauc fitting region energy bounds (eV)
 *  4. Interactive SVG Absorbance Spectrum & Tauc Plot with linear regression line and Eg extrapolation
 *  5. Calculated Scientific Properties card (Optical Band Gap Eg in eV, R² fit quality)
 *  6. Analysis Run History dropdown for reproducible comparison
 */

import React, { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import type {
  CalculatedProperty,
  Characterization,
  TaucProcessedResponse,
  TransitionType,
  UVVisAnalysisInput,
  XRDAnalysisRun,
} from '@/types'
import { analysisService } from '@/services/analysisService'
import { ErrorMessage } from '@/components/ErrorMessage'
import { InlineSpinner, LoadingSpinner } from '@/components/LoadingSpinner'
import { UvVisPlotChart } from '@/components/UvVisPlotChart'
import type { ApiError } from '@/types'

interface UvVisAnalysisModalProps {
  characterization: Characterization
  onClose: () => void
}

export function UvVisAnalysisModal({ characterization, onClose }: UvVisAnalysisModalProps) {
  const [history, setHistory] = useState<XRDAnalysisRun[]>([])
  const [currentRun, setCurrentRun] = useState<XRDAnalysisRun | null>(null)
  const [taucRes, setTaucRes] = useState<TaucProcessedResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Config Form State
  const [config, setConfig] = useState<UVVisAnalysisInput>({
    preprocessing: {
      baseline_subtraction: false,
      smoothing: true,
      savgol_window: 11,
      savgol_polyorder: 3,
    },
    tauc: {
      transition_type: 'DIRECT_ALLOWED',
      sample_thickness_cm: undefined,
      fit_energy_min_ev: undefined,
      fit_energy_max_ev: undefined,
    },
    notes: '',
  })

  // Load history & current run
  const loadHistory = async () => {
    setLoading(true)
    setError(null)
    try {
      const runs = await analysisService.listCharacterizationRuns(characterization.id)
      setHistory(runs)
      if (runs.length > 0) {
        await selectRun(runs[0])
      }
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Failed to load analysis runs.')
    } finally {
      setLoading(false)
    }
  }

  const selectRun = async (run: XRDAnalysisRun) => {
    setCurrentRun(run)
    try {
      const taucData = await analysisService.getTaucData(run.id)
      setTaucRes(taucData)
    } catch (e) {
      setTaucRes(null)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [characterization.id])

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setAnalyzing(true)
    try {
      const newRun = await analysisService.runUvVisAnalysis(characterization.id, config)
      await loadHistory()
      await selectRun(newRun)
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="uvvis-modal-title">
      <div className="modal" style={{ maxWidth: 960, maxHeight: '92vh', overflowY: 'auto' }}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title" id="uvvis-modal-title">
              UV-Vis Tauc Band Gap Analysis ({characterization.technique})
            </h2>
            <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
              Optical Absorption & Tauc Plot Method · Instrument: {characterization.instrument_name || 'UV-Vis Spectrophotometer'}
            </div>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>

        <div className="modal-body">
          {error && <ErrorMessage error={error} />}

          {/* Analysis History Run Selector */}
          {history.length > 0 && (
            <div style={{
              background: 'var(--color-bg)',
              padding: '10px 14px',
              borderRadius: 6,
              border: '1px solid var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 16,
            }}>
              <div style={{ fontSize: '0.8125rem', fontWeight: 600 }}>
                Historical Analysis Runs ({history.length})
              </div>
              <select
                className="form-control"
                style={{ width: 'auto', fontSize: '0.8125rem' }}
                value={currentRun?.id ?? ''}
                onChange={(e) => {
                  const r = history.find((h) => h.id === e.target.value)
                  if (r) selectRun(r)
                }}
              >
                {history.map((r, idx) => (
                  <option key={r.id} value={r.id}>
                    Run #{history.length - idx} · {new Date(r.started_at).toLocaleString()} ({r.parameters?.tauc?.transition_type ?? 'Tauc'})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Controls Form */}
          <details style={{ marginBottom: 16, background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid #e2e8f0' }} open={history.length === 0}>
            <summary style={{ fontWeight: 600, cursor: 'pointer', fontSize: '0.875rem' }}>
              Configure Tauc Model & Preprocessing Controls
            </summary>

            <form onSubmit={handleRunAnalysis} style={{ marginTop: 12 }}>
              <div className="form-grid">
                {/* Transition Model */}
                <div className="form-group span-2">
                  <label className="form-label required">Electronic Transition Model</label>
                  <select
                    className="form-control"
                    value={config.tauc.transition_type}
                    onChange={(e) => setConfig({
                      ...config,
                      tauc: { ...config.tauc, transition_type: e.target.value as TransitionType }
                    })}
                  >
                    <option value="DIRECT_ALLOWED">Direct Allowed Transition: (α·hν)² vs hν (n = 2)</option>
                    <option value="INDIRECT_ALLOWED">Indirect Allowed Transition: (α·hν)⁰·⁵ vs hν (n = 0.5)</option>
                  </select>
                </div>

                {/* Thickness */}
                <div className="form-group">
                  <label className="form-label">Sample Thickness (cm) [Optional]</label>
                  <input
                    type="number"
                    step="0.001"
                    className="form-control"
                    placeholder="e.g. 0.05 (for α calculation)"
                    value={config.tauc.sample_thickness_cm ?? ''}
                    onChange={(e) => setConfig({
                      ...config,
                      tauc: { ...config.tauc, sample_thickness_cm: e.target.value ? parseFloat(e.target.value) : undefined }
                    })}
                  />
                  <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
                    If omitted, Absorbance A is used directly.
                  </div>
                </div>

                {/* Preprocessing */}
                <div className="form-group">
                  <label className="form-label">Savitzky-Golay Smoothing</label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8125rem', marginTop: 6 }}>
                    <input
                      type="checkbox"
                      checked={config.preprocessing.smoothing}
                      onChange={(e) => setConfig({
                        ...config,
                        preprocessing: { ...config.preprocessing, smoothing: e.target.checked }
                      })}
                    />
                    Enable Savitzky-Golay noise filter
                  </label>
                </div>

                {/* Energy Range */}
                <div className="form-group">
                  <label className="form-label">Fit Region Min Energy (eV)</label>
                  <input
                    type="number"
                    step="0.05"
                    className="form-control"
                    placeholder="Auto (minimum energy)"
                    value={config.tauc.fit_energy_min_ev ?? ''}
                    onChange={(e) => setConfig({
                      ...config,
                      tauc: { ...config.tauc, fit_energy_min_ev: e.target.value ? parseFloat(e.target.value) : undefined }
                    })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Fit Region Max Energy (eV)</label>
                  <input
                    type="number"
                    step="0.05"
                    className="form-control"
                    placeholder="Auto (maximum energy)"
                    value={config.tauc.fit_energy_max_ev ?? ''}
                    onChange={(e) => setConfig({
                      ...config,
                      tauc: { ...config.tauc, fit_energy_max_ev: e.target.value ? parseFloat(e.target.value) : undefined }
                    })}
                  />
                </div>
              </div>

              <div style={{ marginTop: 12, textAlign: 'right' }}>
                <button type="submit" className="btn btn-primary btn-sm" disabled={analyzing}>
                  {analyzing ? <InlineSpinner /> : '▶ Run UV-Vis Tauc Analysis'}
                </button>
              </div>
            </form>
          </details>

          {/* Results Display */}
          {loading ? (
            <LoadingSpinner message="Loading UV-Vis spectrum data..." />
          ) : currentRun && taucRes ? (
            <div>
              {/* Thickness Warning Banner if applicable */}
              {taucRes.warning_msg && (
                <div style={{
                  fontSize: '0.8125rem',
                  color: '#92400e',
                  background: '#fef3c7',
                  borderLeft: '4px solid #f59e0b',
                  padding: '8px 12px',
                  borderRadius: 4,
                  marginBottom: 12,
                }}>
                  <strong>Scientific Notice:</strong> {taucRes.warning_msg} Absorbance A (a.u.) was used for Tauc plot transformation.
                </div>
              )}

              {/* Tauc Plot Chart */}
              <UvVisPlotChart
                dataPoints={taucRes.data_points}
                fitLine={taucRes.fit_line}
                bandGapEv={taucRes.band_gap_ev}
                transitionType={taucRes.transition_type}
                usingAlpha={taucRes.using_alpha}
              />

              {/* Calculated Properties (Optical Band Gap) */}
              {currentRun.calculated_properties && currentRun.calculated_properties.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, marginBottom: 8 }}>
                    Calculated Optical Properties
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
                    {currentRun.calculated_properties.map((prop: CalculatedProperty) => (
                      <div
                        key={prop.id}
                        style={{
                          background: '#f0fdf4',
                          border: '1px solid #bbf7d0',
                          borderRadius: 6,
                          padding: 12,
                        }}
                      >
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#166534', textTransform: 'uppercase' }}>
                          {prop.property_name} ({prop.calculation_method})
                        </div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#14532d', margin: '4px 0' }}>
                          Eg = {prop.value} {prop.unit}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#166534', fontFamily: 'monospace' }}>
                          R² Fit Quality: {prop.input_values?.r_squared ?? 'N/A'} · Formula: {prop.formula}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-muted)' }}>
              No analysis runs recorded yet. Click "Run UV-Vis Tauc Analysis" above to process the spectrum.
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
