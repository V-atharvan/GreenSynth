/**
 * GreenSynth Analytics — ML Prediction & Uncertainty Bounds Page
 */

import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { TrendingUp, AlertTriangle, Sparkles, RotateCcw } from 'lucide-react'
import { mlService, MLModel, MLPrediction } from '@/services/mlService'

export default function MLPredictionPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const preselectedModelId = searchParams.get('model')

  const [models, setModels] = useState<MLModel[]>([])
  const [selectedModelId, setSelectedModelId] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<MLModel | null>(null)
  const [inputFields, setInputFields] = useState<Record<string, number>>({})
  const [notes, setNotes] = useState<string>('')
  const [predicting, setPredicting] = useState<boolean>(false)
  const [prediction, setPrediction] = useState<MLPrediction | null>(null)
  const [error, setError] = useState<string | null>(null)

  const getSensibleDefault = (featureName: string, ranges?: any): number => {
    if (ranges && ranges[featureName]?.mean != null) {
      return Number(ranges[featureName].mean.toFixed(2))
    }
    const fn = featureName.toLowerCase()
    if (fn.includes('precursor_concentration')) return 0.25
    if (fn.includes('precursor_solution_volume')) return 50.0
    if (fn.includes('extract_concentration')) return 10.0
    if (fn.includes('extract_volume')) return 20.0
    if (fn.includes('ethanol_volume')) return 30.0
    if (fn.includes('substrate_temperature')) return 350.0
    if (fn.includes('spray_rate')) return 2.5
    if (fn.includes('spray_duration')) return 15.0
    if (fn.includes('distance')) return 15.0
    if (fn.includes('pressure')) return 150.0
    if (fn.includes('cycles')) return 5.0
    if (fn.includes('ambient_temperature')) return 25.0
    if (fn.includes('humidity')) return 45.0
    return 1.0
  }

  const initInputFields = (model: MLModel) => {
    const defaults: Record<string, number> = {}
    const ranges = (model as any).feature_ranges_json
    model.feature_names.forEach((fn) => {
      defaults[fn] = getSensibleDefault(fn, ranges)
    })
    setInputFields(defaults)
  }

  useEffect(() => {
    async function loadApprovedModels() {
      try {
        const mList = await mlService.getModels()
        setModels(mList)
        if (mList.length > 0) {
          const target = preselectedModelId
            ? mList.find((m) => m.id === preselectedModelId) || mList[0]
            : mList.find((m) => m.model_type === 'RANDOM_FOREST' || m.status === 'PRODUCTION_CANDIDATE') || mList[0]
          setSelectedModelId(target.id)
          setSelectedModel(target)
          initInputFields(target)
        }
      } catch (err) {
        console.error('Failed to load models:', err)
      }
    }
    loadApprovedModels()
  }, [preselectedModelId])

  const handleModelChange = (modelId: string) => {
    setSelectedModelId(modelId)
    const m = models.find((mod) => mod.id === modelId) || null
    setSelectedModel(m)
    if (m) initInputFields(m)
  }

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedModelId) return
    setPredicting(true)
    setError(null)
    setPrediction(null)
    try {
      const res = await mlService.generatePrediction(selectedModelId, {
        input_parameters: inputFields,
        notes: notes || undefined,
      })
      setPrediction(res)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Prediction failed.')
    } finally {
      setPredicting(false)
    }
  }

  const domainColor = (status?: string) => {
    if (status === 'IN_DOMAIN') return 'production'
    if (status === 'OUT_OF_DOMAIN') return 'critical'
    return 'warning'
  }

  return (
    <div className="gs-ml-container">

      {/* Header */}
      <div className="gs-page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            onClick={() => navigate('/ml')}
            className="gs-btn gs-btn-outline"
            style={{ padding: '8px 12px' }}
          >
            ← Back
          </button>
          <div>
            <div className="gs-page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div className="gs-page-title-icon purple" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <TrendingUp size={20} />
              </div>
              ML Prediction &amp; Uncertainty Bounds
            </div>
            <p className="gs-page-subtitle">
              Generate property predictions with applicability domain checks &amp; confidence intervals.
            </p>
          </div>
        </div>
      </div>

      {error && <div className="gs-alert error" style={{ display: 'flex', alignItems: 'center', gap: 8 }}><AlertTriangle size={16} /> {error}</div>}

      {/* Model Selection & Input Form */}
      <form onSubmit={handlePredict}>
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">Select Model &amp; Enter Synthesis Parameters</span>
          </div>
          <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="gs-field">
              <label className="gs-label">Select Validated ML Model</label>
              <select
                value={selectedModelId}
                onChange={(e) => handleModelChange(e.target.value)}
                className="gs-input"
              >
                {models.length === 0 && <option value="">— No models available —</option>}
                {models.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.model_type}) — {m.target_property} [{m.status}]
                  </option>
                ))}
              </select>
            </div>

            {selectedModel && (
              <>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 12, borderBottom: '1px solid var(--color-border-light)', flexWrap: 'wrap', gap: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--color-text)' }}>
                      Synthesis Parameter Inputs
                    </div>
                    <button
                      type="button"
                      onClick={() => selectedModel && initInputFields(selectedModel)}
                      className="gs-btn gs-btn-secondary"
                      style={{ padding: '3px 8px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 4 }}
                      title="Reset to benchmark synthesis values"
                    >
                      <RotateCcw size={12} /> Reset to Typical Synthesis Conditions
                    </button>
                  </div>
                  <span className="gs-chip teal" style={{ background: '#d1fae5', color: '#065f46' }}>
                    Target: {selectedModel.target_property} ({selectedModel.target_unit})
                  </span>
                </div>

                <div className="gs-form-row">
                  {selectedModel.feature_names.map((fname) => {
                    const range = (selectedModel as any).feature_ranges_json?.[fname]
                    const spec = selectedModel.feature_specs?.find((s: any) => s.feature_name === fname)
                    return (
                      <div key={fname} className="gs-field">
                        <label className="gs-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span>
                            {fname.replace(/_/g, ' ')}
                            {spec?.unit ? ` (${spec.unit})` : ''}
                          </span>
                          {range && (
                            <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 400 }}>
                              [{range.min} — {range.max}]
                            </span>
                          )}
                        </label>
                        <input
                          type="number"
                          step="any"
                          value={inputFields[fname] ?? 0}
                          onChange={(e) => setInputFields({ ...inputFields, [fname]: parseFloat(e.target.value) || 0 })}
                          required
                          className="gs-input"
                        />
                      </div>
                    )
                  })}
                </div>

                <div className="gs-field">
                  <label className="gs-label">Researcher Notes (Optional)</label>
                  <input
                    type="text"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Optional notes for this prediction run"
                    className="gs-input"
                  />
                </div>
              </>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="submit"
                disabled={predicting || !selectedModelId}
                className="gs-btn gs-btn-indigo"
              >
                {predicting ? 'Calculating…' : 'Generate Property Prediction'}
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Prediction Result */}
      {prediction && (
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">Prediction Output &amp; Uncertainty Bounds</span>
            <span className={`gs-chip ${domainColor(prediction.applicability_status)}`}>
              Domain: {prediction.applicability_status}
            </span>
          </div>
          <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Main result box */}
            <div style={{
              background: 'linear-gradient(135deg, #f0fdf4 0%, #eff6ff 100%)',
              border: '1px solid #bbf7d0',
              borderRadius: 'var(--radius-lg)',
              padding: '32px 24px',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '0.8125rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)', marginBottom: 8 }}>
                Predicted {prediction.predicted_property}
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: '#0d9488', lineHeight: 1 }}>
                {prediction.predicted_value}
                <span style={{ fontSize: '1rem', fontWeight: 400, color: 'var(--color-text-secondary)', marginLeft: 6 }}>
                  {prediction.unit}
                </span>
              </div>
              {prediction.uncertainty_lower !== undefined && prediction.uncertainty_upper !== undefined && (
                <div style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginTop: 12 }}>
                  Estimated 95% Interval: <strong>[{prediction.uncertainty_lower} — {prediction.uncertainty_upper}] {prediction.unit}</strong>
                </div>
              )}
            </div>

            {/* Warnings */}
            {prediction.warnings && prediction.warnings.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div className="gs-label">Applicability Warnings</div>
                {prediction.warnings.map((w, idx) => (
                  <div key={idx} className="gs-alert warning" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <AlertTriangle size={16} /> {w}
                  </div>
                ))}
              </div>
            )}

            {/* Input traceability */}
            <div>
              <div className="gs-label" style={{ marginBottom: 10 }}>Input Conditions Traceability</div>
              <div className="gs-param-grid">
                {Object.entries(prediction.input_parameters).map(([key, val]) => (
                  <div key={key} className="gs-param-item">
                    <div className="gs-param-name">{key}</div>
                    <div className="gs-param-value">{val}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
