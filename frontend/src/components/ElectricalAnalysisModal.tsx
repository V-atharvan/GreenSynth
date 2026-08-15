/**
 * GreenSynth Analytics — Electrical Analysis Dashboard Modal
 *
 * Provides:
 *  1. Unit selectors (Voltage: V/mV, Current: A/mA/uA/nA, Length: cm/mm/m/um)
 *  2. Sample Geometry configuration (Rectangular Bar L, W, T)
 *  3. Configurable I-V fit region voltage bounds
 *  4. Interactive SVG I-V curve plot with linear regression fit line
 *  5. Calculated Scientific Properties cards:
 *     - Electrical Resistance R (Ohms)
 *     - Electrical Resistivity rho (Ohm*cm) [if geometry provided]
 *     - Electrical Conductivity sigma (S/cm) [if geometry provided]
 *  6. Analysis Run History dropdown for reproducible comparison
 */

import React, { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import type {
  CalculatedProperty,
  Characterization,
  CurrentUnit,
  ElectricalAnalysisInput,
  ElectricalProcessedResponse,
  GeometryType,
  LengthUnit,
  VoltageUnit,
  XRDAnalysisRun,
} from '@/types'
import { analysisService } from '@/services/analysisService'
import { ErrorMessage } from '@/components/ErrorMessage'
import { InlineSpinner, LoadingSpinner } from '@/components/LoadingSpinner'
import { ElectricalPlotChart } from '@/components/ElectricalPlotChart'
import type { ApiError } from '@/types'

interface ElectricalAnalysisModalProps {
  characterization: Characterization
  onClose: () => void
}

export function ElectricalAnalysisModal({ characterization, onClose }: ElectricalAnalysisModalProps) {
  const [history, setHistory] = useState<XRDAnalysisRun[]>([])
  const [currentRun, setCurrentRun] = useState<XRDAnalysisRun | null>(null)
  const [elecRes, setElecRes] = useState<ElectricalProcessedResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Config Form State
  const [config, setConfig] = useState<ElectricalAnalysisInput>({
    units: {
      voltage_unit: 'V',
      current_unit: 'A',
      resistance_unit: 'Ohm',
      length_unit: 'cm',
    },
    geometry: {
      geometry_type: 'RECTANGULAR_BAR',
      length: undefined,
      width: undefined,
      thickness: undefined,
    },
    fit_voltage_min: undefined,
    fit_voltage_max: undefined,
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
      const data = await analysisService.getElectricalData(run.id)
      setElecRes(data)
    } catch (e) {
      setElecRes(null)
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
      const newRun = await analysisService.runElectricalAnalysis(characterization.id, config)
      await loadHistory()
      await selectRun(newRun)
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 960, maxHeight: '92vh', overflowY: 'auto' }}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title" id="electrical-modal-title">
              Electrical Property & I-V Curve Analysis ({characterization.technique})
            </h2>
            <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
              I-V Linear Regression · Resistance, Resistivity & Conductivity Calculation · Instrument: {characterization.instrument_name || 'SourceMeter'}
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
                    Run #{history.length - idx} · {new Date(r.started_at).toLocaleString()} ({r.calculated_properties?.length ?? 0} properties)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Controls Form */}
          <details style={{ marginBottom: 16, background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid #e2e8f0' }} open={history.length === 0}>
            <summary style={{ fontWeight: 600, cursor: 'pointer', fontSize: '0.875rem' }}>
              Configure Units & Sample Geometry Controls
            </summary>

            <form onSubmit={handleRunAnalysis} style={{ marginTop: 12 }}>
              <div className="form-grid">
                {/* Units Selection */}
                <div className="form-group">
                  <label className="form-label required">Voltage Unit in Raw File</label>
                  <select
                    className="form-control"
                    value={config.units.voltage_unit}
                    onChange={(e) => setConfig({
                      ...config,
                      units: { ...config.units, voltage_unit: e.target.value as VoltageUnit }
                    })}
                  >
                    <option value="V">Volts (V)</option>
                    <option value="mV">Millivolts (mV)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label required">Current Unit in Raw File</label>
                  <select
                    className="form-control"
                    value={config.units.current_unit}
                    onChange={(e) => setConfig({
                      ...config,
                      units: { ...config.units, current_unit: e.target.value as CurrentUnit }
                    })}
                  >
                    <option value="A">Amperes (A)</option>
                    <option value="mA">Milliamperes (mA)</option>
                    <option value="uA">Microamperes (µA)</option>
                    <option value="nA">Nanoamperes (nA)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label required">Dimension Units</label>
                  <select
                    className="form-control"
                    value={config.units.length_unit}
                    onChange={(e) => setConfig({
                      ...config,
                      units: { ...config.units, length_unit: e.target.value as LengthUnit }
                    })}
                  >
                    <option value="cm">Centimeters (cm)</option>
                    <option value="mm">Millimeters (mm)</option>
                    <option value="um">Micrometers (µm)</option>
                    <option value="m">Meters (m)</option>
                  </select>
                </div>

                {/* Geometry Inputs */}
                <div className="form-group">
                  <label className="form-label">Sample Geometry</label>
                  <select
                    className="form-control"
                    value={config.geometry.geometry_type}
                    onChange={(e) => setConfig({
                      ...config,
                      geometry: { ...config.geometry, geometry_type: e.target.value as GeometryType }
                    })}
                  >
                    <option value="RECTANGULAR_BAR">Rectangular Bar (L x W x T)</option>
                    <option value="THIN_FILM">Thin Film (2-Probe)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Path Length L ({config.units.length_unit})</label>
                  <input
                    type="number"
                    step="0.001"
                    className="form-control"
                    placeholder="e.g. 1.0"
                    value={config.geometry.length ?? ''}
                    onChange={(e) => setConfig({
                      ...config,
                      geometry: { ...config.geometry, length: e.target.value ? parseFloat(e.target.value) : undefined }
                    })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Sample Width W ({config.units.length_unit})</label>
                  <input
                    type="number"
                    step="0.001"
                    className="form-control"
                    placeholder="e.g. 0.5"
                    value={config.geometry.width ?? ''}
                    onChange={(e) => setConfig({
                      ...config,
                      geometry: { ...config.geometry, width: e.target.value ? parseFloat(e.target.value) : undefined }
                    })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Sample Thickness T ({config.units.length_unit})</label>
                  <input
                    type="number"
                    step="0.001"
                    className="form-control"
                    placeholder="e.g. 0.05"
                    value={config.geometry.thickness ?? ''}
                    onChange={(e) => setConfig({
                      ...config,
                      geometry: { ...config.geometry, thickness: e.target.value ? parseFloat(e.target.value) : undefined }
                    })}
                  />
                  <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
                    Required for Resistivity (ρ) & Conductivity (σ).
                  </div>
                </div>

                {/* Fit Region */}
                <div className="form-group">
                  <label className="form-label">Fit Region Voltage Min ({config.units.voltage_unit})</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-control"
                    placeholder="Auto (min voltage)"
                    value={config.fit_voltage_min ?? ''}
                    onChange={(e) => setConfig({
                      ...config,
                      fit_voltage_min: e.target.value ? parseFloat(e.target.value) : undefined
                    })}
                  />
                </div>
              </div>

              <div style={{ marginTop: 12, textAlign: 'right' }}>
                <button type="submit" className="btn btn-primary btn-sm" disabled={analyzing}>
                  {analyzing ? <InlineSpinner /> : '▶ Run Electrical Analysis'}
                </button>
              </div>
            </form>
          </details>

          {/* Results Display */}
          {loading ? (
            <LoadingSpinner message="Loading I-V measurement data..." />
          ) : currentRun && elecRes ? (
            <div>
              {/* Dimension Warning Banner if applicable */}
              {elecRes.warning_msg && (
                <div style={{
                  fontSize: '0.8125rem',
                  color: '#92400e',
                  background: '#fef3c7',
                  borderLeft: '4px solid #f59e0b',
                  padding: '8px 12px',
                  borderRadius: 4,
                  marginBottom: 12,
                }}>
                  <strong>Scientific Notice:</strong> {elecRes.warning_msg}
                </div>
              )}

              {/* I-V Plot Chart */}
              <ElectricalPlotChart
                dataPoints={elecRes.data_points}
                fitLine={elecRes.fit_line}
                resistanceOhms={elecRes.resistance_ohms}
                voltageUnit={elecRes.voltage_unit}
                currentUnit={elecRes.current_unit}
              />

              {/* Calculated Properties Cards */}
              {currentRun.calculated_properties && currentRun.calculated_properties.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, marginBottom: 8 }}>
                    Calculated Electrical Properties ({currentRun.calculated_properties.length})
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>
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
                          {prop.property_name}
                        </div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#14532d', margin: '4px 0' }}>
                          {prop.value} {prop.unit}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#166534', fontFamily: 'monospace' }}>
                          Method: {prop.calculation_method}
                          {prop.formula && <div>Formula: {prop.formula}</div>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-muted)' }}>
              No analysis runs recorded yet. Click "Run Electrical Analysis" above to calculate resistance.
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
