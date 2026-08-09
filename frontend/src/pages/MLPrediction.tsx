/**
 * GreenSynth Analytics — ML Prediction & Uncertainty Bounds Page
 */

import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { mlService, MLModel, MLPrediction } from '@/services/mlService'

export default function MLPredictionPage() {
  const navigate = useNavigate()
  const [models, setModels] = useState<MLModel[]>([])
  const [selectedModelId, setSelectedModelId] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<MLModel | null>(null)
  const [inputFields, setInputFields] = useState<Record<string, number>>({})
  const [notes, setNotes] = useState<string>('')
  const [predicting, setPredicting] = useState<boolean>(false)
  const [prediction, setPrediction] = useState<MLPrediction | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadApprovedModels() {
      try {
        const mList = await mlService.getModels()
        setModels(mList)
        if (mList.length > 0) {
          setSelectedModelId(mList[0].id)
          setSelectedModel(mList[0])
          initInputFields(mList[0])
        }
      } catch (err) {
        console.error('Failed to load models:', err)
      }
    }
    loadApprovedModels()
  }, [])

  const initInputFields = (model: MLModel) => {
    const defaults: Record<string, number> = {}
    model.feature_names.forEach((fn) => { defaults[fn] = 300.0 })
    setInputFields(defaults)
  }

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
      const result = await mlService.generatePrediction(selectedModelId, { input_parameters: inputFields, notes })
      setPrediction(result)
    } catch (err: any) {
      setError(err?.message || 'Failed to generate prediction.')
    } finally {
      setPredicting(false)
    }
  }

  const domainColor = (status: string) => {
    if (status === 'VALID' || status === 'IN_DOMAIN') return 'stable'
    if (status === 'CAUTION' || status === 'NEAR_BOUNDARY') return 'warning'
    return 'critical'
  }

  return (
    <div className="gs-page">

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
            <div className="gs-page-title">
              <div className="gs-page-title-icon purple">📈</div>
              ML Prediction &amp; Uncertainty Bounds
            </div>
            <p className="gs-page-subtitle">
              Generate property predictions with applicability domain checks &amp; confidence intervals.
            </p>
          </div>
        </div>
      </div>

      {error && <div className="gs-alert error">⚠️ {error}</div>}

      {/* Model Selection & Input Form */}
      <form onSubmit={handlePredict}>
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">⚙️ Select Model &amp; Enter Synthesis Parameters</span>
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
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 12, borderBottom: '1px solid var(--color-border-light)' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--color-text)' }}>
                    Synthesis Parameter Inputs
                  </div>
                  <span className="gs-chip teal" style={{ background: '#d1fae5', color: '#065f46' }}>
                    Target: {selectedModel.target_property} ({selectedModel.target_unit})
                  </span>
                </div>

                <div className="gs-form-row">
                  {selectedModel.feature_names.map((fname) => (
                    <div key={fname} className="gs-field">
                      <label className="gs-label">{fname.replace(/_/g, ' ')}</label>
                      <input
                        type="number"
                        step="any"
                        value={inputFields[fname] ?? 0}
                        onChange={(e) => setInputFields({ ...inputFields, [fname]: parseFloat(e.target.value) || 0 })}
                        required
                        className="gs-input"
                      />
                    </div>
                  ))}
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
                {predicting ? '⏳ Calculating…' : '⚡ Generate Property Prediction'}
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Prediction Result */}
      {prediction && (
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">✅ Prediction Output &amp; Uncertainty Bounds</span>
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
                  <div key={idx} className="gs-alert warning">⚠️ {w}</div>
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
