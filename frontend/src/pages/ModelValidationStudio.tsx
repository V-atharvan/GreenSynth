/**
 * GreenSynth Analytics — Phase 17 Model Health & Experimental Validation Studio
 */
import React, { useState, useEffect } from 'react'
import { ShieldCheck, Ban, Check, AlertTriangle, BarChart3 } from 'lucide-react'
import { mlService, MLModel, MLPrediction } from '@/services/mlService'

export default function ModelValidationStudio() {
  const [models, setModels] = useState<MLModel[]>([])
  const [selectedModelId, setSelectedModelId] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<MLModel | null>(null)
  const [modelHealth, setModelHealth] = useState<any | null>(null)
  const [predictions, setPredictions] = useState<MLPrediction[]>([])
  const [selectedPrediction, setSelectedPrediction] = useState<MLPrediction | null>(null)
  const [actualValueInput, setActualValueInput] = useState<string>('')
  const [validationSuccessMsg, setValidationSuccessMsg] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [loading, setLoading] = useState<boolean>(false)

  useEffect(() => {
    mlService.getModels().then((mList) => {
      setModels(mList)
      if (mList.length > 0) {
        setSelectedModelId(mList[0].id)
        setSelectedModel(mList[0])
      }
    }).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedModelId) return
    setLoading(true)
    const m = models.find((x) => x.id === selectedModelId) || null
    setSelectedModel(m)

    Promise.all([
      mlService.getModelHealth(selectedModelId),
      mlService.getPredictions(selectedModelId),
    ]).then(([health, unvalPreds]) => {
      setModelHealth(health)
      setPredictions(unvalPreds)
      if (unvalPreds.length > 0) setSelectedPrediction(unvalPreds[0])
      else setSelectedPrediction(null)
    }).catch((err) => {
      console.error('Failed to load model validation data:', err)
    }).finally(() => setLoading(false))
  }, [selectedModelId, models])

  const handleValidatePrediction = async () => {
    if (!selectedPrediction || !actualValueInput) return
    const val = parseFloat(actualValueInput)
    if (isNaN(val)) {
      setErrorMsg('Please enter a valid numeric value for actual measurement.')
      return
    }

    setErrorMsg(null)
    setValidationSuccessMsg(null)
    try {
      await mlService.validatePrediction(selectedPrediction.id, val)
      setValidationSuccessMsg(`Validation recorded! Actual: ${val} ${selectedPrediction.unit}. Error metrics updated.`)
      setActualValueInput('')
      const [health, unvalPreds] = await Promise.all([
        mlService.getModelHealth(selectedModelId),
        mlService.getPredictions(selectedModelId),
      ])
      setModelHealth(health)
      setPredictions(unvalPreds)
      if (unvalPreds.length > 0) setSelectedPrediction(unvalPreds[0])
      else setSelectedPrediction(null)
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || err?.message || 'Failed to validate prediction.')
    }
  }

  const handleRetireModel = async () => {
    if (!selectedModelId) return
    if (!window.confirm('Are you sure you want to RETIRE this model? It will no longer be available for predictions.')) return
    try {
      const updated = await mlService.retireModel(selectedModelId)
      setModels((prev) => prev.map((m) => (m.id === selectedModelId ? updated : m)))
      setSelectedModel(updated)
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || 'Failed to retire model.')
    }
  }

  const healthStatus = modelHealth?.status === 'HEALTHY' ? 'healthy' : modelHealth?.status === 'DRIFTED' ? 'warning' : 'critical'

  return (
    <div className="gs-page">

      {/* Header */}
      <div className="gs-page-header">
        <div>
          <div className="gs-page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className="gs-page-title-icon indigo" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldCheck size={20} />
            </div>
            Model Monitoring &amp; Experimental Validation Studio
          </div>
          <p className="gs-page-subtitle">
            Phase 17 closed-loop validation linking predictions to actual laboratory measurements with condition deviation tracking.
          </p>
        </div>
        <div className="gs-header-actions">
          {models.length > 0 && (
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="gs-select"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.model_type}) — {m.status}
                </option>
              ))}
            </select>
          )}
          {selectedModel && selectedModel.status !== 'RETIRED' && (
            <button onClick={handleRetireModel} className="gs-btn gs-btn-danger" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <Ban size={14} /> Retire Model
            </button>
          )}
        </div>
      </div>

      {loading && (
        <div className="gs-loading"><div className="gs-spinner" /> Loading model data…</div>
      )}

      {/* Health Status Banner */}
      {modelHealth && (
        <div className={`gs-health-bar ${healthStatus}`}>
          <div className={`gs-health-dot ${healthStatus}`} />
          <div style={{ flex: 1 }}>
            <div className="gs-health-status">
              Model Health: {modelHealth.status}
            </div>
            <div className="gs-health-desc">{modelHealth.recommendation}</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24, paddingLeft: 24, borderLeft: '1px solid var(--color-border)' }}>
            {[
              { label: 'Validations', value: modelHealth.validation_count },
              { label: 'MAE Error', value: modelHealth.mae },
              { label: 'Bias', value: modelHealth.bias },
            ].map(({ label, value }) => (
              <div key={label}>
                <div style={{ fontSize: '0.6875rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--color-text-secondary)', letterSpacing: '0.05em' }}>{label}</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-text)', marginTop: 2, fontFamily: 'var(--font-mono)' }}>{value ?? 'N/A'}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main two-column panel */}
      <div className="gs-two-col">

        {/* Left: Select Prediction */}
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">1. Select Prediction &amp; Link Experiment</span>
          </div>
          <div className="gs-panel-body">
            {predictions.length === 0 ? (
              <div className="gs-empty" style={{ padding: '40px 0' }}>
                <div className="gs-empty-icon" style={{ display: 'flex', justifyContent: 'center' }}><BarChart3 size={32} /></div>
                <div className="gs-empty-title">No Predictions Available</div>
                <div className="gs-empty-text">Generate predictions from the ML Center first, then return here to validate them.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div className="gs-field">
                  <label className="gs-label">Generated Prediction</label>
                  <select
                    value={selectedPrediction?.id || ''}
                    onChange={(e) => setSelectedPrediction(predictions.find((p) => p.id === e.target.value) || null)}
                    className="gs-input"
                  >
                    {predictions.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.predicted_property}: {p.predicted_value} {p.unit} ({p.applicability_status})
                      </option>
                    ))}
                  </select>
                </div>

                {selectedPrediction && (
                  <div style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {[
                      { label: 'Predicted Target', value: `${selectedPrediction.predicted_property} (${selectedPrediction.unit})`, highlight: true },
                      { label: 'Predicted Value', value: `${selectedPrediction.predicted_value} ${selectedPrediction.unit}`, bold: true },
                      ...(selectedPrediction.uncertainty_lower !== undefined
                        ? [{ label: 'Uncertainty Interval (95%)', value: `[${selectedPrediction.uncertainty_lower}, ${selectedPrediction.uncertainty_upper}]` }]
                        : []),
                    ].map(({ label, value, highlight, bold }) => (
                      <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
                        <span style={{ color: 'var(--color-text-secondary)' }}>{label}:</span>
                        <span style={{ fontWeight: bold ? 700 : 600, color: highlight ? '#0d9488' : 'var(--color-text)' }}>{value}</span>
                      </div>
                    ))}

                    <div style={{ paddingTop: 10, borderTop: '1px solid var(--color-border-light)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#b45309', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                        Proposed / Prediction-Derived Conditions
                      </div>
                      <div className="gs-param-grid">
                        {Object.entries(selectedPrediction.input_parameters).map(([k, v]) => (
                          <div key={k} className="gs-param-item">
                            <div className="gs-param-name">{k.replace('_', ' ')}</div>
                            <div className="gs-param-value">{v}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right: Enter Lab Result */}
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">2. Enter Actual Laboratory Measurement</span>
          </div>
          <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div className="gs-field">
              <label className="gs-label">
                Actual Measured Property Value ({selectedPrediction?.unit || 'unit'})
              </label>
              <input
                type="number"
                step="any"
                placeholder="e.g. 4.7"
                value={actualValueInput}
                onChange={(e) => setActualValueInput(e.target.value)}
                className="gs-input"
              />
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 4 }}>
                Enter actual laboratory characterization value. Predictions are preserved side-by-side and never overwritten.
              </div>
            </div>

            {errorMsg && <div className="gs-alert error" style={{ display: 'flex', alignItems: 'center', gap: 8 }}><AlertTriangle size={16} /> {errorMsg}</div>}
            {validationSuccessMsg && <div className="gs-alert success" style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Check size={16} /> {validationSuccessMsg}</div>}

            <button
              onClick={handleValidatePrediction}
              disabled={!selectedPrediction || !actualValueInput}
              className="gs-btn gs-btn-teal"
              style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <Check size={14} /> Validate Prediction &amp; Calculate Error
            </button>

            <div className="gs-info-banner amber">
              <div className="gs-info-banner-icon" style={{ display: 'flex', alignItems: 'center' }}><AlertTriangle size={18} /></div>
              <div>
                <div className="gs-info-banner-title">Immutability Guarantee</div>
                <div className="gs-info-banner-text">
                  Predictions are never overwritten. Laboratory measurements are recorded alongside predictions for complete scientific traceability.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
