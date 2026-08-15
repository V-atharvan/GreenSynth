/**
 * GreenSynth Analytics — XRD Analysis Modal & Dashboard
 *
 * Provides:
 *  1. Preprocessing controls (Baseline subtraction, Savitzky-Golay smoothing)
 *  2. Peak detection controls (Prominence, Min distance)
 *  3. Scherrer equation crystallite size inputs (Wavelength λ, Shape factor K)
 *  4. Raw vs Processed XRD pattern plot with peak markers
 *  5. Detected Peak Table with FWHM (degrees)
 *  6. Calculated Properties cards (Scherrer crystallite size in nm with explicit assumptions)
 *  7. Analysis Run History dropdown for reproducible comparison
 */

import React, { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import type {
  CalculatedProperty,
  Characterization,
  XRDAnalysisInput,
  XRDAnalysisRun,
  XRDDataPoint,
} from '@/types'
import { analysisService } from '@/services/analysisService'
import { ErrorMessage } from '@/components/ErrorMessage'
import { InlineSpinner, LoadingSpinner } from '@/components/LoadingSpinner'
import { XrdPlotChart } from '@/components/XrdPlotChart'
import type { ApiError } from '@/types'

interface XrdAnalysisModalProps {
  characterization: Characterization
  onClose: () => void
}

export function XrdAnalysisModal({ characterization, onClose }: XrdAnalysisModalProps) {
  const [history, setHistory] = useState<XRDAnalysisRun[]>([])
  const [currentRun, setCurrentRun] = useState<XRDAnalysisRun | null>(null)
  const [curveData, setCurveData] = useState<XRDDataPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConfig, setShowConfig] = useState(false)

  // Config Form State
  const [config, setConfig] = useState<XRDAnalysisInput>({
    preprocessing: {
      baseline_subtraction: true,
      baseline_window: 50,
      smoothing: true,
      savgol_window: 11,
      savgol_polyorder: 3,
    },
    peak_detection: {
      prominence: 20.0,
      min_distance: 5,
    },
    scherrer: {
      calculate_crystallite_size: true,
      wavelength_nm: 0.15406,
      shape_factor_k: 0.9,
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
      const ptsRes = await analysisService.getProcessedData(run.id)
      setCurveData(ptsRes.data_points)
    } catch (e) {
      setCurveData([])
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
      const newRun = await analysisService.runXrdAnalysis(characterization.id, config)
      await loadHistory()
      await selectRun(newRun)
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="xrd-modal-title">
      <div className="modal" style={{ maxWidth: 960, maxHeight: '92vh', overflowY: 'auto' }}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title" id="xrd-modal-title">
              XRD Pattern Analysis ({characterization.technique})
            </h2>
            <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
              Sample Characterization · Instrument: {characterization.instrument_name || 'Standard XRD'}
            </div>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>

        <div className="modal-body">
          {error && <ErrorMessage error={error} />}

          {/* Configuration Controls */}
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header" style={{ cursor: 'pointer' }} onClick={() => setShowConfig(!showConfig)}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>Configure Analysis & Preprocessing Parameters</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-primary)' }}>{showConfig ? 'Hide' : 'Show'}</span>
              </h3>
            </div>
            
            {showConfig && (
              <form onSubmit={handleRunAnalysis} style={{ padding: 12 }}>
                <div className="form-grid">
                  {/* 1. Preprocessing */}
                  <div className="form-group span-2">
                    <label className="form-label" style={{ fontWeight: 600 }}>Preprocessing</label>
                    <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8125rem' }}>
                        <input
                          type="checkbox"
                          checked={config.preprocessing.baseline_subtraction}
                          onChange={(e) => setConfig({
                            ...config,
                            preprocessing: { ...config.preprocessing, baseline_subtraction: e.target.checked }
                          })}
                        />
                        Rolling Baseline Subtraction
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8125rem' }}>
                        <input
                          type="checkbox"
                          checked={config.preprocessing.smoothing}
                          onChange={(e) => setConfig({
                            ...config,
                            preprocessing: { ...config.preprocessing, smoothing: e.target.checked }
                          })}
                        />
                        Savitzky-Golay Noise Smoothing
                      </label>
                    </div>
                  </div>

                  {/* 2. Peak Detection */}
                  <div className="form-group">
                    <label className="form-label">Min Peak Prominence</label>
                    <input
                      type="number"
                      step="0.1"
                      className="form-control"
                      value={config.peak_detection.prominence ?? ''}
                      onChange={(e) => setConfig({
                        ...config,
                        peak_detection: { ...config.peak_detection, prominence: e.target.value ? parseFloat(e.target.value) : null }
                      })}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Min Distance (points)</label>
                    <input
                      type="number"
                      className="form-control"
                      value={config.peak_detection.min_distance}
                      onChange={(e) => setConfig({
                        ...config,
                        peak_detection: { ...config.peak_detection, min_distance: parseInt(e.target.value, 10) || 5 }
                      })}
                    />
                  </div>

                  {/* 3. Scherrer Equation */}
                  <div className="form-group">
                    <label className="form-label">X-Ray Wavelength λ (nm)</label>
                    <input
                      type="number"
                      step="0.00001"
                      className="form-control"
                      value={config.scherrer.wavelength_nm}
                      onChange={(e) => setConfig({
                        ...config,
                        scherrer: { ...config.scherrer, wavelength_nm: parseFloat(e.target.value) || 0.15406 }
                      })}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Scherrer Shape Factor K</label>
                    <input
                      type="number"
                      step="0.01"
                      className="form-control"
                      value={config.scherrer.shape_factor_k}
                      onChange={(e) => setConfig({
                        ...config,
                        scherrer: { ...config.scherrer, shape_factor_k: parseFloat(e.target.value) || 0.9 }
                      })}
                    />
                  </div>
                </div>

                <div style={{ marginTop: 12, textAlign: 'right' }}>
                  <button type="submit" className="btn btn-primary btn-sm" disabled={analyzing}>
                    {analyzing ? <InlineSpinner /> : 'Run Analysis'}
                  </button>
                </div>
              </form>
            )}
          </div>

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
                    Run #{history.length - idx} · {new Date(r.started_at).toLocaleString()} ({r.peaks?.length ?? 0} peaks)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Controls Form */}
          <details style={{ marginBottom: 16, background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid #e2e8f0' }} open={history.length === 0}>
            <summary style={{ fontWeight: 600, cursor: 'pointer', fontSize: '0.875rem' }}>
              Configure Analysis & Preprocessing Parameters
            </summary>

            <form onSubmit={handleRunAnalysis} style={{ marginTop: 12 }}>
              <div className="form-grid">
                {/* 1. Preprocessing */}
                <div className="form-group span-2">
                  <label className="form-label" style={{ fontWeight: 600 }}>1. Preprocessing</label>
                  <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8125rem' }}>
                      <input
                        type="checkbox"
                        checked={config.preprocessing.baseline_subtraction}
                        onChange={(e) => setConfig({
                          ...config,
                          preprocessing: { ...config.preprocessing, baseline_subtraction: e.target.checked }
                        })}
                      />
                      Rolling Baseline Subtraction
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8125rem' }}>
                      <input
                        type="checkbox"
                        checked={config.preprocessing.smoothing}
                        onChange={(e) => setConfig({
                          ...config,
                          preprocessing: { ...config.preprocessing, smoothing: e.target.checked }
                        })}
                      />
                      Savitzky-Golay Noise Smoothing
                    </label>
                  </div>
                </div>

                {/* 2. Peak Detection */}
                <div className="form-group">
                  <label className="form-label">Min Peak Prominence</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-control"
                    value={config.peak_detection.prominence ?? ''}
                    onChange={(e) => setConfig({
                      ...config,
                      peak_detection: { ...config.peak_detection, prominence: e.target.value ? parseFloat(e.target.value) : null }
                    })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Min Distance (points)</label>
                  <input
                    type="number"
                    className="form-control"
                    value={config.peak_detection.min_distance}
                    onChange={(e) => setConfig({
                      ...config,
                      peak_detection: { ...config.peak_detection, min_distance: parseInt(e.target.value, 10) || 5 }
                    })}
                  />
                </div>

                {/* 3. Scherrer Equation */}
                <div className="form-group">
                  <label className="form-label">X-Ray Wavelength λ (nm)</label>
                  <input
                    type="number"
                    step="0.00001"
                    className="form-control"
                    value={config.scherrer.wavelength_nm}
                    onChange={(e) => setConfig({
                      ...config,
                      scherrer: { ...config.scherrer, wavelength_nm: parseFloat(e.target.value) || 0.15406 }
                    })}
                  />
                  <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>Cu-Kα₁ = 0.15406 nm</div>
                </div>

                <div className="form-group">
                  <label className="form-label">Scherrer Shape Factor K</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    value={config.scherrer.shape_factor_k}
                    onChange={(e) => setConfig({
                      ...config,
                      scherrer: { ...config.scherrer, shape_factor_k: parseFloat(e.target.value) || 0.9 }
                    })}
                  />
                  <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>Spherical = 0.90</div>
                </div>
              </div>

              <div style={{ marginTop: 12, textAlign: 'right' }}>
                <button type="submit" className="btn btn-primary btn-sm" disabled={analyzing}>
                  {analyzing ? <InlineSpinner /> : '▶ Run XRD Analysis'}
                </button>
              </div>
            </form>
          </details>

          {/* Results Display */}
          {loading ? (
            <LoadingSpinner message="Loading XRD pattern data..." />
          ) : currentRun ? (
            <div>
              {/* Pattern Chart */}
              <XrdPlotChart dataPoints={curveData} peaks={currentRun.peaks ?? []} />

              {/* Calculated Properties (Scherrer Crystallite Size) */}
              {currentRun.calculated_properties && currentRun.calculated_properties.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, marginBottom: 8 }}>
                    Calculated Scientific Properties
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
                          {prop.value} {prop.unit}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#166534', fontFamily: 'monospace' }}>
                          Formula: {prop.formula}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Detected Peaks Table */}
              <div style={{ marginTop: 20 }}>
                <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, marginBottom: 8 }}>
                  Detected Diffraction Peaks ({currentRun.peaks?.length ?? 0})
                </h3>
                {currentRun.peaks?.length === 0 ? (
                  <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
                    No peaks detected with the current prominence threshold. Try reducing min peak prominence in configuration.
                  </div>
                ) : (
                  <div className="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Peak #</th>
                          <th>2θ Angle (°)</th>
                          <th>Intensity</th>
                          <th>FWHM (°)</th>
                          <th>Prominence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {currentRun.peaks?.map((p, idx) => (
                          <tr key={p.id || idx}>
                            <td style={{ fontWeight: 600 }}>#{idx + 1}</td>
                            <td className="text-mono" style={{ fontWeight: 700 }}>{p.peak_position.toFixed(2)}°</td>
                            <td className="text-mono">{p.intensity.toFixed(1)}</td>
                            <td className="text-mono">{p.fwhm ? `${p.fwhm.toFixed(3)}°` : '—'}</td>
                            <td className="text-mono" style={{ color: 'var(--color-text-secondary)' }}>
                              {p.prominence ? p.prominence.toFixed(1) : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-muted)' }}>
              No analysis runs recorded yet. Click "Run XRD Analysis" above to process the raw pattern.
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
