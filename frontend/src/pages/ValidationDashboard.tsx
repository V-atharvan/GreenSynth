/**
 * GreenSynth Analytics — Model Validation & Drift Center (Phase 17)
 */

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { mlService, MLModel } from '@/services/mlService'
import { validationService, ModelPerformanceHistory, ValidationResult } from '@/services/validationService'
import {
  ShieldCheck,
  FlaskConical,
  TrendingDown,
  Target,
  BarChart2,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Ruler,
  FileSpreadsheet,
} from 'lucide-react'

export default function ValidationDashboard() {
  const [models, setModels] = useState<MLModel[]>([])
  const [selectedModelId, setSelectedModelId] = useState<string>('')
  const [history, setHistory] = useState<ModelPerformanceHistory | null>(null)
  const [valResults, setValResults] = useState<ValidationResult[]>([])

  const [loading, setLoading] = useState<boolean>(true)
  const [retraining, setRetraining] = useState<boolean>(false)
  const [retrainSuccess, setRetrainSuccess] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadModels() {
      try {
        const list = await mlService.getModels()
        setModels(list)
        if (list.length > 0) setSelectedModelId(list[0].id)
      } catch (err) {
        console.error('Failed to load models:', err)
      } finally {
        setLoading(false)
      }
    }
    loadModels()
  }, [])

  useEffect(() => {
    if (!selectedModelId) return
    async function loadHistory() {
      setLoading(true)
      try {
        const hist = await validationService.getPerformanceHistory(selectedModelId)
        setHistory(hist)
        const results = await validationService.getValidationResults(selectedModelId)
        setValResults(results)
      } catch (err) {
        console.error('Failed to load history:', err)
      } finally {
        setLoading(false)
      }
    }
    loadHistory()
  }, [selectedModelId])

  const handleRetrain = async () => {
    if (!selectedModelId) return
    setRetraining(true)
    setError(null)
    setRetrainSuccess(null)
    try {
      const newModels = await validationService.retrainModel(
        selectedModelId,
        'Retraining v2 dataset incorporating new prospective validation results'
      )
      setRetrainSuccess(
        `Retraining completed! Created Model v2 (${newModels[0]?.name}). Model v1 remains immutable.`
      )
      const updatedList = await mlService.getModels()
      setModels(updatedList)
    } catch (err: any) {
      console.error('Retrain error:', err)
      setError(err?.message || 'Retraining failed.')
    } finally {
      setRetraining(false)
    }
  }

  return (
    <div className="gs-page">

      {/* Header */}
      <div className="gs-page-header">
        <div>
          <div className="gs-page-title">
            <div className="gs-page-title-icon emerald">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
            </div>
            Model Validation &amp; Drift Center
          </div>
          <p className="gs-page-subtitle">
            Statistical (Level 1), Holdout (Level 2) &amp; Prospective Experimental (Level 3) Validation Tracking.
          </p>
        </div>
        <div className="gs-header-actions">
          {models.length > 0 && (
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="gs-select"
              aria-label="Select model"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} (v{m.version}) — {m.status}
                </option>
              ))}
            </select>
          )}
          <Link to="/validation/experimental" className="gs-btn gs-btn-emerald" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <FlaskConical className="w-4 h-4" /> Prospective Validation
          </Link>
          <Link to="/ml/validation" className="gs-btn gs-btn-outline">
            Model Health Studio →
          </Link>
        </div>
      </div>

      {/* Alerts */}
      {retrainSuccess && (
        <div className="gs-alert success" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{retrainSuccess}</span>
        </div>
      )}
      {error && (
        <div className="gs-alert error" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Warning banners */}
      {history && history.warnings.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {history.warnings.map((w, i) => (
            <div
              key={i}
              className={`gs-alert ${w.includes('drift') ? 'error' : 'warning'}`}
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <div className="gs-loading">
          <div className="gs-spinner" />
          Loading validation data…
        </div>
      ) : (
        <>
          {/* Validation metrics */}
          {history && (
            <div className="gs-metrics-row">
              <div className="gs-metric-card teal">
                <div className="gs-metric-icon teal">
                  <Ruler className="w-5 h-5 text-teal-600" />
                </div>
                <div className="gs-metric-value">
                  {history.statistical_metrics.cv_r2 ?? 'N/A'}
                </div>
                <div className="gs-metric-label">Statistical CV R² (L1)</div>
              </div>
              <div className="gs-metric-card indigo">
                <div className="gs-metric-icon indigo">
                  <FlaskConical className="w-5 h-5 text-indigo-600" />
                </div>
                <div className="gs-metric-value">n = {history.n_experimental_validations}</div>
                <div className="gs-metric-label">Physical Validations (L2/L3)</div>
              </div>
              <div className="gs-metric-card emerald">
                <div className="gs-metric-icon emerald">
                  <TrendingDown className="w-5 h-5 text-emerald-600" />
                </div>
                <div className="gs-metric-value">
                  {history.experimental_mae !== null && history.experimental_mae !== undefined
                    ? history.experimental_mae.toFixed(3)
                    : 'N/A'}
                </div>
                <div className="gs-metric-label">Experimental MAE</div>
              </div>
              <div className="gs-metric-card purple">
                <div className="gs-metric-icon purple">
                  <Target className="w-5 h-5 text-purple-600" />
                </div>
                <div className="gs-metric-value">
                  {history.interval_coverage_rate !== undefined && history.interval_coverage_rate !== null
                    ? `${(history.interval_coverage_rate * 100).toFixed(0)}%`
                    : 'N/A'}
                </div>
                <div className="gs-metric-label">95% Interval Coverage</div>
              </div>
            </div>
          )}

          {/* Scatter plot */}
          {valResults.length > 0 && (
            <div className="gs-panel">
              <div className="gs-panel-header">
                <span className="gs-panel-title" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <BarChart2 className="w-4 h-4 text-emerald-600" /> Predicted vs Actual Physical Measurement Plot
                </span>
                <span className="gs-chip info">n = {valResults.length} validated points</span>
              </div>
              <div className="gs-panel-body">
                <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: 16 }}>
                  Dashed diagonal represents perfect 1:1 prediction agreement (y = x). Points near the line indicate accurate predictions.
                </p>
                <div style={{ height: 260, background: '#f8fafc', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
                  <svg width="100%" height="100%" viewBox="0 0 400 220">
                    <line x1="48" y1="170" x2="370" y2="30" stroke="#94a3b8" strokeWidth="1.5" strokeDasharray="5 4" />
                    <line x1="48" y1="170" x2="370" y2="170" stroke="#cbd5e1" strokeWidth="1" />
                    <line x1="48" y1="30" x2="48" y2="170" stroke="#cbd5e1" strokeWidth="1" />
                    {valResults.map((r, i) => {
                      const maxV = Math.max(...valResults.map((v) => Math.max(v.predicted_value, v.actual_value)), 10.0)
                      const cx = 48 + (r.predicted_value / maxV) * 322
                      const cy = 170 - (r.actual_value / maxV) * 140
                      return (
                        <g key={r.id || i}>
                          <circle cx={cx} cy={cy} r="5.5" fill="#0d9488" opacity="0.85" />
                        </g>
                      )
                    })}
                    <text x="210" y="212" fill="#64748b" fontSize="10" textAnchor="middle">Predicted Value</text>
                    <text x="16" y="100" fill="#64748b" fontSize="10" textAnchor="middle" transform="rotate(-90 16 100)">Actual Measured Value</text>
                  </svg>
                </div>
              </div>
            </div>
          )}

          {/* Retraining action */}
          <div className="gs-panel">
            <div className="gs-panel-header">
              <div>
                <div className="gs-panel-title" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <RefreshCw className="w-4 h-4 text-indigo-600" /> Dataset v2 &amp; Retraining Workflow
                </div>
                <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 4 }}>
                  Incorporates newly completed physical validation records into Dataset v2 to train Model v2. Model v1 remains immutable.
                </p>
              </div>
              <button
                onClick={handleRetrain}
                disabled={retraining || !selectedModelId}
                className="gs-btn gs-btn-indigo"
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
              >
                <RefreshCw className={`w-4 h-4 ${retraining ? 'animate-spin' : ''}`} />
                {retraining ? 'Training Model v2…' : 'Retrain & Version Model (v2)'}
              </button>
            </div>
          </div>

          {/* Validation results table */}
          <div className="gs-panel">
            <div className="gs-panel-header">
              <span className="gs-panel-title" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <FileSpreadsheet className="w-4 h-4 text-emerald-600" /> Validation Results Traceability
              </span>
            </div>
            {valResults.length === 0 ? (
              <div className="gs-empty">
                <div className="gs-empty-icon">
                  <FlaskConical className="w-8 h-8 text-slate-400" />
                </div>
                <div className="gs-empty-title">No Validation Results Yet</div>
                <div className="gs-empty-text">
                  No physical or holdout validation results recorded yet for this model version.
                </div>
              </div>
            ) : (
              <div className="gs-table-wrapper">
                <table className="gs-table">
                  <thead>
                    <tr>
                      <th>Validation Type</th>
                      <th>Target</th>
                      <th>Predicted</th>
                      <th>Interval</th>
                      <th>Actual Lab</th>
                      <th>Abs Error</th>
                      <th>Criterion</th>
                    </tr>
                  </thead>
                  <tbody>
                    {valResults.map((r) => (
                      <tr key={r.id}>
                        <td><span className="gs-chip info">{r.validation_type}</span></td>
                        <td style={{ fontWeight: 600 }}>{r.target_property}</td>
                        <td style={{ color: '#0d9488', fontFamily: 'var(--font-mono)' }}>{r.predicted_value} {r.unit}</td>
                        <td style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.8125rem' }}>
                          {r.prediction_lower_bound !== undefined ? `[${r.prediction_lower_bound}, ${r.prediction_upper_bound}]` : '—'}
                        </td>
                        <td style={{ color: '#059669', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{r.actual_value} {r.unit}</td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>{r.absolute_error}</td>
                        <td>
                          {r.criterion_result === 'SATISFIED' ? (
                            <span className="gs-chip stable">Satisfied</span>
                          ) : r.criterion_result === 'NOT_SATISFIED' ? (
                            <span className="gs-chip critical">Not Satisfied</span>
                          ) : (
                            <span className="gs-chip muted">Completed</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
