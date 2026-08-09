/**
 * GreenSynth Analytics — FTIR Spectroscopy & Peak Annotation Dashboard Modal
 *
 * Provides:
 *  1. Noise smoothing & peak detection controls
 *  2. Interactive SVG FTIR spectrum plot with detected peak markers and annotations
 *  3. Detected Peaks Table (Wavenumber cm^-1, Signal Value, Prominence, Width)
 *  4. Researcher Functional Group Peak Annotations form (e.g. C=O stretch)
 *  5. Analysis Run History dropdown for reproducible comparison
 */

import React, { useEffect, useState } from 'react'
import type {
  Characterization,
  FTIRAnalysisInput,
  FTIRAnnotationResponse,
  FTIRProcessedResponse,
  XRDAnalysisRun,
} from '@/types'
import { analysisService } from '@/services/analysisService'
import { ErrorMessage } from '@/components/ErrorMessage'
import { InlineSpinner, LoadingSpinner } from '@/components/LoadingSpinner'
import { FtirPlotChart } from '@/components/FtirPlotChart'
import type { ApiError } from '@/types'

interface FtirAnalysisModalProps {
  characterization: Characterization
  onClose: () => void
}

export function FtirAnalysisModal({ characterization, onClose }: FtirAnalysisModalProps) {
  const [history, setHistory] = useState<XRDAnalysisRun[]>([])
  const [currentRun, setCurrentRun] = useState<XRDAnalysisRun | null>(null)
  const [ftirRes, setFtirRes] = useState<FTIRProcessedResponse | null>(null)
  const [annotations, setAnnotations] = useState<FTIRAnnotationResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Annotation Form State
  const [annWn, setAnnWn] = useState<number | ''>('')
  const [annLabel, setAnnLabel] = useState('')
  const [annInterp, setAnnInterp] = useState('')
  const [annConfidence, setAnnConfidence] = useState('Medium')

  // Config Form State
  const [config, setConfig] = useState<FTIRAnalysisInput>({
    preprocessing: {
      smoothing: true,
      savgol_window: 11,
      savgol_polyorder: 3,
    },
    peak_detection: {
      prominence: undefined,
      min_distance: 10,
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
      const data = await analysisService.getFtirData(run.id)
      setFtirRes(data)
      const anns = await analysisService.listFtirAnnotations(run.id)
      setAnnotations(anns)
    } catch (e) {
      setFtirRes(null)
      setAnnotations([])
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
      const newRun = await analysisService.runFtirAnalysis(characterization.id, config)
      await loadHistory()
      await selectRun(newRun)
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleAddAnnotation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentRun || !annWn || !annLabel.trim()) return
    try {
      const newAnn = await analysisService.addFtirAnnotation(currentRun.id, {
        wavenumber_cm1: Number(annWn),
        label: annLabel.trim(),
        interpretation: annInterp.trim() || undefined,
        confidence: annConfidence,
      })
      setAnnotations([...annotations, newAnn])
      setAnnWn('')
      setAnnLabel('')
      setAnnInterp('')
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Failed to add annotation.')
    }
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="ftir-modal-title">
      <div className="modal" style={{ maxWidth: 960, maxHeight: '92vh', overflowY: 'auto' }}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title" id="ftir-modal-title">
              FTIR Spectroscopy & Functional Group Peak Analysis ({characterization.technique})
            </h2>
            <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
              Savitzky-Golay Smoothing · Peak Detection · Researcher Annotations · Instrument: {characterization.instrument_name || 'FTIR Spectrometer'}
            </div>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
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
                    Run #{history.length - idx} · {new Date(r.started_at).toLocaleString()} ({r.peaks?.length ?? 0} peaks)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Controls Form */}
          <details style={{ marginBottom: 16, background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid #e2e8f0' }} open={history.length === 0}>
            <summary style={{ fontWeight: 600, cursor: 'pointer', fontSize: '0.875rem' }}>
              ⚙ Configure Smoothing & Peak Detection Controls
            </summary>

            <form onSubmit={handleRunAnalysis} style={{ marginTop: 12 }}>
              <div className="form-grid">
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

                <div className="form-group">
                  <label className="form-label">Window Length (odd integer)</label>
                  <input
                    type="number"
                    step="2"
                    className="form-control"
                    value={config.preprocessing.savgol_window}
                    onChange={(e) => setConfig({
                      ...config,
                      preprocessing: { ...config.preprocessing, savgol_window: parseInt(e.target.value) || 11 }
                    })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Peak Prominence Threshold</label>
                  <input
                    type="number"
                    step="0.5"
                    className="form-control"
                    placeholder="Auto (5% signal height)"
                    value={config.peak_detection.prominence ?? ''}
                    onChange={(e) => setConfig({
                      ...config,
                      peak_detection: { ...config.peak_detection, prominence: e.target.value ? parseFloat(e.target.value) : undefined }
                    })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Min Distance Between Peaks</label>
                  <input
                    type="number"
                    className="form-control"
                    value={config.peak_detection.min_distance}
                    onChange={(e) => setConfig({
                      ...config,
                      peak_detection: { ...config.peak_detection, min_distance: parseInt(e.target.value) || 10 }
                    })}
                  />
                </div>
              </div>

              <div style={{ marginTop: 12, textAlign: 'right' }}>
                <button type="submit" className="btn btn-primary btn-sm" disabled={analyzing}>
                  {analyzing ? <InlineSpinner /> : '▶ Run FTIR Spectrum Analysis'}
                </button>
              </div>
            </form>
          </details>

          {/* Results Display */}
          {loading ? (
            <LoadingSpinner message="Loading FTIR spectrum data..." />
          ) : currentRun && ftirRes ? (
            <div>
              {/* FTIR Plot Chart */}
              <FtirPlotChart
                dataPoints={ftirRes.data_points}
                detectedPeaks={ftirRes.detected_peaks}
                annotations={annotations}
                signalType={ftirRes.signal_type}
              />

              {/* Add Researcher Annotation Form */}
              <div style={{ marginTop: 16, background: '#fcfeff', padding: 12, borderRadius: 6, border: '1px solid #dbeafe' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: 8, color: '#1e40af' }}>
                  ✏ Add Researcher Peak Annotation (Functional Group Assignment)
                </h4>
                <form onSubmit={handleAddAnnotation} style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 2fr 1fr auto', gap: 8, alignItems: 'end' }}>
                  <div>
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Wavenumber (cm⁻¹)</label>
                    <input
                      type="number"
                      step="1"
                      required
                      className="form-control"
                      placeholder="e.g. 1700"
                      value={annWn}
                      onChange={(e) => setAnnWn(e.target.value ? parseFloat(e.target.value) : '')}
                    />
                  </div>
                  <div>
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Annotation Label</label>
                    <input
                      type="text"
                      required
                      className="form-control"
                      placeholder="e.g. C=O Stretch"
                      value={annLabel}
                      onChange={(e) => setAnnLabel(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Scientific Interpretation</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. Carbonyl group capping agent"
                      value={annInterp}
                      onChange={(e) => setAnnInterp(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Confidence</label>
                    <select
                      className="form-control"
                      value={annConfidence}
                      onChange={(e) => setAnnConfidence(e.target.value)}
                    >
                      <option value="High">High</option>
                      <option value="Medium">Medium</option>
                      <option value="Tentative">Tentative</option>
                    </select>
                  </div>
                  <button type="submit" className="btn btn-primary btn-sm">
                    + Add
                  </button>
                </form>
              </div>

              {/* Detected Peaks & Annotations Table */}
              <div style={{ marginTop: 16 }}>
                <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, marginBottom: 8 }}>
                  📌 Detected Peaks & Researcher Annotations ({ftirRes.detected_peaks.length})
                </h3>
                <div style={{ overflowX: 'auto', maxHeight: 240, overflowY: 'auto' }}>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Wavenumber (cm⁻¹)</th>
                        <th>Signal Height</th>
                        <th>Prominence</th>
                        <th>Width (cm⁻¹)</th>
                        <th>Researcher Annotation</th>
                        <th>Confidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ftirRes.detected_peaks.map((p, i) => {
                        const matchedAnn = annotations.find(
                          (a) => Math.abs(a.wavenumber_cm1 - p.wavenumber_cm1) < 15.0
                        )
                        return (
                          <tr key={i}>
                            <td style={{ fontWeight: 600 }}>{p.wavenumber_cm1.toFixed(1)}</td>
                            <td>{p.signal_value.toFixed(2)}</td>
                            <td>{p.prominence.toFixed(2)}</td>
                            <td>{p.width_cm1.toFixed(1)}</td>
                            <td>
                              {matchedAnn ? (
                                <span style={{ color: '#b91c1c', fontWeight: 600 }}>
                                  🏷 {matchedAnn.label} ({matchedAnn.interpretation || 'Annotated'})
                                </span>
                              ) : (
                                <span style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
                                  Unannotated
                                </span>
                              )}
                            </td>
                            <td>{matchedAnn?.confidence || 'N/A'}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-muted)' }}>
              No analysis runs recorded yet. Click "Run FTIR Spectrum Analysis" above to process the spectrum.
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
