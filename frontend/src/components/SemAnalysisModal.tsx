/**
 * GreenSynth Analytics — SEM Image Viewer & Scale Calibration Modal
 *
 * Provides:
 *  1. Micrograph image preview
 *  2. Image metadata & scale calibration form (Scale Bar nm vs Pixels => nm/pixel ratio)
 *  3. Visual Annotations tool (point / region notes)
 *  4. Researcher Manual Physical Distance Measurement tool (pixel distance => physical nm/um conversion)
 *  5. Warnings when image scale is missing or uncalibrated
 */

import React, { useEffect, useState } from 'react'
import type {
  Characterization,
  RawFile,
  SEMAnnotationResponse,
  SEMMeasurementResponse,
  SEMMetadataResponse,
  SEMMetadataUpdate,
} from '@/types'
import { analysisService } from '@/services/analysisService'
import { ErrorMessage } from '@/components/ErrorMessage'
import { InlineSpinner, LoadingSpinner } from '@/components/LoadingSpinner'
import type { ApiError } from '@/types'

interface SemAnalysisModalProps {
  characterization: Characterization
  file: RawFile
  onClose: () => void
}

export function SemAnalysisModal({ characterization, file, onClose }: SemAnalysisModalProps) {
  const [metadata, setMetadata] = useState<SEMMetadataResponse | null>(null)
  const [annotations, setAnnotations] = useState<SEMAnnotationResponse[]>([])
  const [measurements, setMeasurements] = useState<SEMMeasurementResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [savingMeta, setSavingMeta] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Scale Calibration Form State
  const [metaForm, setMetaForm] = useState<SEMMetadataUpdate>({
    magnification: undefined,
    accelerating_voltage_kv: undefined,
    working_distance_mm: undefined,
    detector: 'SE',
    scale_bar_nm: undefined,
    scale_bar_pixels: undefined,
    notes: '',
  })

  // Measurement Form State
  const [pxDist, setPxDist] = useState<number | ''>('')
  const [measLabel, setMeasLabel] = useState('Particle Diameter')

  // Annotation Form State
  const [annType, setAnnType] = useState('point')
  const [annLabel, setAnnLabel] = useState('')
  const [annNotes, setAnnNotes] = useState('')

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const meta = await analysisService.getSemMetadata(file.id)
      setMetadata(meta)
      setMetaForm({
        magnification: meta.magnification ?? undefined,
        accelerating_voltage_kv: meta.accelerating_voltage_kv ?? undefined,
        working_distance_mm: meta.working_distance_mm ?? undefined,
        detector: meta.detector ?? 'SE',
        scale_bar_nm: meta.scale_bar_nm ?? undefined,
        scale_bar_pixels: meta.scale_bar_pixels ?? undefined,
        notes: meta.notes ?? '',
      })

      const anns = await analysisService.listSemAnnotations(file.id)
      setAnnotations(anns)

      const meass = await analysisService.listSemMeasurements(file.id)
      setMeasurements(meass)
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Failed to load SEM image details.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
  }, [file.id])

  const handleUpdateMetadata = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSavingMeta(true)
    try {
      const updated = await analysisService.updateSemMetadata(file.id, metaForm)
      setMetadata(updated)
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Failed to update metadata.')
    } finally {
      setSavingMeta(false)
    }
  }

  const handleAddMeasurement = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!pxDist) return
    setError(null)
    try {
      const newMeas = await analysisService.addSemMeasurement(file.id, {
        pixel_distance: Number(pxDist),
        label: measLabel.trim() || 'Particle Measurement',
      })
      setMeasurements([...measurements, newMeas])
      setPxDist('')
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Failed to record measurement.')
    }
  }

  const handleAddAnnotation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!annLabel.trim()) return
    setError(null)
    try {
      const newAnn = await analysisService.addSemAnnotation(file.id, {
        annotation_type: annType,
        coordinates_json: { x: 100, y: 100 },
        label: annLabel.trim(),
        notes: annNotes.trim() || undefined,
      })
      setAnnotations([...annotations, newAnn])
      setAnnLabel('')
      setAnnNotes('')
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Failed to add annotation.')
    }
  }

  const imageUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/files/${file.id}/download`

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="sem-modal-title">
      <div className="modal" style={{ maxWidth: 960, maxHeight: '92vh', overflowY: 'auto' }}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title" id="sem-modal-title">
              SEM Micrograph Viewer & Scale Calibration ({characterization.technique})
            </h2>
            <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
              File: {file.original_filename} · Instrument: {characterization.instrument_name || 'FE-SEM'}
            </div>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="modal-body">
          {error && <ErrorMessage error={error} />}

          {loading ? (
            <LoadingSpinner message="Loading SEM image details..." />
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 16 }}>
              {/* Left Column: Image Viewer & Annotations / Measurements */}
              <div>
                {/* Image Box */}
                <div style={{
                  background: '#090d16',
                  borderRadius: 6,
                  padding: 12,
                  textAlign: 'center',
                  border: '1px solid var(--color-border)',
                  position: 'relative',
                  minHeight: 320,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <img
                    src={imageUrl}
                    alt={file.original_filename}
                    style={{ maxWidth: '100%', maxHeight: 420, objectFit: 'contain', borderRadius: 4 }}
                    onError={(e) => {
                      // Fallback preview box if blob is not loaded
                      e.currentTarget.style.display = 'none'
                    }}
                  />
                  <div style={{
                    position: 'absolute',
                    bottom: 16,
                    right: 16,
                    background: 'rgba(0,0,0,0.75)',
                    color: 'white',
                    padding: '4px 10px',
                    borderRadius: 4,
                    fontSize: '0.75rem',
                    fontFamily: 'monospace',
                  }}>
                    Scale: {metadata?.nm_per_pixel ? `${metadata.nm_per_pixel} nm/px` : 'Uncalibrated'}
                  </div>
                </div>

                {/* Scale Missing Warning Banner */}
                {!metadata?.nm_per_pixel && (
                  <div style={{
                    fontSize: '0.8125rem',
                    color: '#92400e',
                    background: '#fef3c7',
                    borderLeft: '4px solid #f59e0b',
                    padding: '8px 12px',
                    borderRadius: 4,
                    marginTop: 12,
                  }}>
                    ⚠️ <strong>Scale Calibration Missing:</strong> Physical distance measurements are unavailable because image scale is not calibrated. Enter scale bar information in the right panel to calibrate.
                  </div>
                )}

                {/* Manual Measurement Tool Form */}
                <div style={{ marginTop: 16, background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid #e2e8f0' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: 8, color: '#0f172a' }}>
                    📏 Manual Distance Measurement Tool (Researcher Measurement)
                  </h4>
                  <form onSubmit={handleAddMeasurement} style={{ display: 'grid', gridTemplateColumns: '1fr 2fr auto', gap: 8, alignItems: 'end' }}>
                    <div>
                      <label className="form-label" style={{ fontSize: '0.75rem' }}>Pixel Length (px)</label>
                      <input
                        type="number"
                        step="1"
                        required
                        className="form-control"
                        placeholder="e.g. 50"
                        value={pxDist}
                        onChange={(e) => setPxDist(e.target.value ? parseFloat(e.target.value) : '')}
                      />
                    </div>
                    <div>
                      <label className="form-label" style={{ fontSize: '0.75rem' }}>Label / Feature</label>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="e.g. Particle Diameter #1"
                        value={measLabel}
                        onChange={(e) => setMeasLabel(e.target.value)}
                      />
                    </div>
                    <button type="submit" className="btn btn-primary btn-sm">
                      + Measure
                    </button>
                  </form>
                </div>

                {/* Manual Measurements List Table */}
                {measurements.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <h4 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: 6 }}>
                      Measured Dimensions ({measurements.length})
                    </h4>
                    <table className="table" style={{ fontSize: '0.8125rem' }}>
                      <thead>
                        <tr>
                          <th>Feature Label</th>
                          <th>Pixel Dist</th>
                          <th>Physical Size</th>
                          <th>Unit</th>
                        </tr>
                      </thead>
                      <tbody>
                        {measurements.map((m) => (
                          <tr key={m.id}>
                            <td>{m.label || 'Feature'}</td>
                            <td>{m.pixel_distance} px</td>
                            <td style={{ fontWeight: 700, color: '#047857' }}>
                              {m.physical_distance_nm !== null ? m.physical_distance_nm : 'Uncalibrated'}
                            </td>
                            <td>{m.unit}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Right Column: Metadata & Scale Calibration Controls */}
              <div style={{ background: '#f8fafc', padding: 14, borderRadius: 6, border: '1px solid #e2e8f0' }}>
                <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, marginBottom: 12 }}>
                  ⚙ SEM Image Metadata & Scale Calibration
                </h3>

                <form onSubmit={handleUpdateMetadata}>
                  <div className="form-group" style={{ marginBottom: 10 }}>
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Magnification (x)</label>
                    <input
                      type="number"
                      step="100"
                      className="form-control"
                      placeholder="e.g. 50000"
                      value={metaForm.magnification ?? ''}
                      onChange={(e) => setMetaForm({ ...metaForm, magnification: e.target.value ? parseFloat(e.target.value) : undefined })}
                    />
                  </div>

                  <div className="form-group" style={{ marginBottom: 10 }}>
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Accelerating Voltage (kV)</label>
                    <input
                      type="number"
                      step="0.1"
                      className="form-control"
                      placeholder="e.g. 15.0"
                      value={metaForm.accelerating_voltage_kv ?? ''}
                      onChange={(e) => setMetaForm({ ...metaForm, accelerating_voltage_kv: e.target.value ? parseFloat(e.target.value) : undefined })}
                    />
                  </div>

                  <div className="form-group" style={{ marginBottom: 10 }}>
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Working Distance (mm)</label>
                    <input
                      type="number"
                      step="0.1"
                      className="form-control"
                      placeholder="e.g. 8.5"
                      value={metaForm.working_distance_mm ?? ''}
                      onChange={(e) => setMetaForm({ ...metaForm, working_distance_mm: e.target.value ? parseFloat(e.target.value) : undefined })}
                    />
                  </div>

                  <div className="form-group" style={{ marginBottom: 10 }}>
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Detector Type</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. SE / BSE"
                      value={metaForm.detector ?? ''}
                      onChange={(e) => setMetaForm({ ...metaForm, detector: e.target.value })}
                    />
                  </div>

                  <hr style={{ margin: '12px 0', borderColor: '#cbd5e1' }} />
                  <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#1e293b', marginBottom: 8 }}>
                    📏 Scale Bar Calibration
                  </div>

                  <div className="form-group" style={{ marginBottom: 10 }}>
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Scale Bar Length (nm)</label>
                    <input
                      type="number"
                      step="1"
                      className="form-control"
                      placeholder="e.g. 500"
                      value={metaForm.scale_bar_nm ?? ''}
                      onChange={(e) => setMetaForm({ ...metaForm, scale_bar_nm: e.target.value ? parseFloat(e.target.value) : undefined })}
                    />
                  </div>

                  <div className="form-group" style={{ marginBottom: 10 }}>
                    <label className="form-label" style={{ fontSize: '0.75rem' }}>Scale Bar Pixel Width (px)</label>
                    <input
                      type="number"
                      step="1"
                      className="form-control"
                      placeholder="e.g. 100"
                      value={metaForm.scale_bar_pixels ?? ''}
                      onChange={(e) => setMetaForm({ ...metaForm, scale_bar_pixels: e.target.value ? parseFloat(e.target.value) : undefined })}
                    />
                  </div>

                  <button type="submit" className="btn btn-primary btn-sm" style={{ width: '100%', marginTop: 8 }} disabled={savingMeta}>
                    {savingMeta ? <InlineSpinner /> : '💾 Save Calibration & Metadata'}
                  </button>
                </form>
              </div>
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
