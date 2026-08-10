/**
 * GreenSynth Analytics — Prospective Experimental Validation Workflow Page
 */

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FlaskConical,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  FileCheck,
} from 'lucide-react'
import { mlService, MLPrediction } from '@/services/mlService'
import { validationService, ProspectiveExperiment, ValidationResult, ValidationCriterion } from '@/services/validationService'

export default function ExperimentalValidation() {
  const [predictions, setPredictions] = useState<MLPrediction[]>([])
  const [selectedPredId, setSelectedPredId] = useState<string>('')
  const [criteria, setCriteria] = useState<ValidationCriterion[]>([])
  const [selectedCritId, setSelectedCritId] = useState<string>('')

  const [prospectiveExp, setProspectiveExp] = useState<ProspectiveExperiment | null>(null)
  const [valResult, setValResult] = useState<ValidationResult | null>(null)

  const [labExpId, setLabExpId] = useState<string>('')
  const [sampleId, setSampleId] = useState<string>('')
  const [measUncertainty, setMeasUncertainty] = useState<string>('0.05')

  const [loading, setLoading] = useState<boolean>(false)
  const [step, setStep] = useState<number>(1)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function initData() {
      try {
        const preds = await mlService.getPredictions()
        setPredictions(preds)
        if (preds.length > 0) setSelectedPredId(preds[0].id)

        const crits = await validationService.getCriteria()
        setCriteria(crits)
        if (crits.length > 0) setSelectedCritId(crits[0].id)
      } catch (err) {
        console.error('Failed to load validation data:', err)
      }
    }
    initData()
  }, [])

  const selectedPred = predictions.find((p) => p.id === selectedPredId)

  // Step 1 -> Step 2: Approve Prospective Experiment
  const handleApproveProspective = async () => {
    if (!selectedPred) return
    setLoading(true)
    setError(null)

    try {
      const prosp = await validationService.createProspective({
        prediction_id: selectedPred.id,
        project_id: '00000000-0000-0000-0000-000000000000',
        researcher: 'Dr. Validation Engineer',
        notes: 'Approved prediction for physical synthesis',
      })
      setProspectiveExp(prosp)
      setStep(2)
    } catch (err: any) {
      console.error('Approval failed:', err)
      setError(err?.message || 'Failed to approve prediction for laboratory experiment.')
    } finally {
      setLoading(false)
    }
  }

  // Step 2 -> Step 3: Link Physical Characterization Result
  const handleLinkResult = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prospectiveExp || !labExpId || !sampleId) return
    setLoading(true)
    setError(null)

    try {
      const vr = await validationService.linkProspectiveResult(
        prospectiveExp.id,
        labExpId,
        sampleId,
        selectedCritId || undefined,
        measUncertainty ? parseFloat(measUncertainty) : undefined,
        'Linked physical lab result'
      )
      setValResult(vr)
      setStep(3)
    } catch (err: any) {
      console.error('Link result failed:', err)
      setError(err?.message || 'Failed to link laboratory result. Ensure target characterization exists.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="gs-page">
      {/* Header */}
      <div className="gs-page-header">
        <div>
          <div className="gs-page-title">
            <div className="gs-page-title-icon emerald">
              <FlaskConical className="w-5 h-5" />
            </div>
            <span>Prospective Experimental Validation</span>
          </div>
          <div className="gs-page-subtitle">
            Bridge Model Predictions with Physical Laboratory Characterization Results (Level 3 Validation).
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Progress Steps */}
      <div className="card" style={{ padding: '16px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', fontSize: '0.8125rem', fontWeight: 600 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: step >= 1 ? 'var(--color-primary)' : 'var(--color-text-secondary)' }}>
            <span style={{ width: 24, height: 24, borderRadius: '50%', background: step >= 1 ? 'var(--color-primary)' : 'var(--color-border)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem' }}>1</span>
            Select & Review Prediction
          </div>
          <ArrowRight className="w-4 h-4 text-muted" />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: step >= 2 ? 'var(--color-primary)' : 'var(--color-text-secondary)' }}>
            <span style={{ width: 24, height: 24, borderRadius: '50%', background: step >= 2 ? 'var(--color-primary)' : 'var(--color-border)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem' }}>2</span>
            Link Lab Experiment
          </div>
          <ArrowRight className="w-4 h-4 text-muted" />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: step >= 3 ? 'var(--color-primary)' : 'var(--color-text-secondary)' }}>
            <span style={{ width: 24, height: 24, borderRadius: '50%', background: step >= 3 ? 'var(--color-primary)' : 'var(--color-border)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem' }}>3</span>
            Validation Result
          </div>
        </div>
      </div>

      {/* STEP 1: Select & Approve Prediction */}
      {step === 1 && (
        <div className="card">
          <div className="card-header">
            <h2>Step 1: Select Model Prediction</h2>
          </div>

          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="form-group">
              <label className="form-label required">Select Prediction Record</label>
              <select
                value={selectedPredId}
                onChange={(e) => setSelectedPredId(e.target.value)}
                className="form-control"
              >
                {predictions.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.predicted_property}: {p.predicted_value} {p.unit} [{p.applicability_status}]
                  </option>
                ))}
              </select>
            </div>

            {selectedPred && (
              <div style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border-light)', borderRadius: 'var(--radius-lg)', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="detail-label">Target Property</span>
                  <span style={{ fontWeight: 700, fontSize: '0.9375rem' }}>{selectedPred.predicted_property}</span>
                </div>

                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">Predicted Value</span>
                    <span className="detail-value" style={{ fontWeight: 700, color: 'var(--color-primary)', fontSize: '1.25rem' }}>
                      {selectedPred.predicted_value} {selectedPred.unit}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">95% Uncertainty Bounds</span>
                    <span className="detail-value code">
                      {selectedPred.uncertainty_lower !== undefined ? `[${selectedPred.uncertainty_lower}, ${selectedPred.uncertainty_upper}]` : 'N/A'}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Applicability Domain</span>
                    <span className="badge badge-active" style={{ alignSelf: 'flex-start' }}>
                      {selectedPred.applicability_status}
                    </span>
                  </div>
                </div>

                <div>
                  <span className="detail-label" style={{ marginBottom: 8, display: 'block' }}>Input Synthesis Parameters</span>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 8 }}>
                    {Object.entries(selectedPred.input_parameters).map(([k, v]) => (
                      <div key={k} style={{ background: 'white', padding: '8px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', fontSize: '0.8125rem' }}>
                        <span className="text-muted">{k}: </span>
                        <strong style={{ color: 'var(--color-primary)' }}>{v}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <div style={{ borderTop: '1px solid var(--color-border-light)', paddingTop: 16 }}>
              <button
                onClick={handleApproveProspective}
                disabled={loading || !selectedPred}
                className="btn btn-primary w-full"
                style={{ justifyContent: 'center', padding: '12px' }}
              >
                {loading ? 'Approving...' : 'Approve Prediction for Physical Lab Synthesis'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: Link Physical Characterization */}
      {step === 2 && prospectiveExp && (
        <form onSubmit={handleLinkResult} className="card">
          <div className="card-header">
            <h2>Step 2: Link Laboratory Experiment & Characterization</h2>
          </div>

          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="alert alert-success">
              <CheckCircle className="w-5 h-5 shrink-0" />
              <span>Prospective Experiment Approved (ID: {prospectiveExp.id.slice(0, 8)}...). Enter laboratory execution details.</span>
            </div>

            <div className="form-grid">
              <div className="form-group">
                <label className="form-label required">Laboratory Experiment UUID</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 84c2e37a-e483-4fc8-b9dd-147e91c01738"
                  value={labExpId}
                  onChange={(e) => setLabExpId(e.target.value)}
                  className="form-control text-mono"
                />
              </div>

              <div className="form-group">
                <label className="form-label required">Characterized Sample UUID</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. c0ca9240-2e5d-4733-9ce6-0b9062f90687"
                  value={sampleId}
                  onChange={(e) => setSampleId(e.target.value)}
                  className="form-control text-mono"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Validation Criterion (Optional)</label>
                <select
                  value={selectedCritId}
                  onChange={(e) => setSelectedCritId(e.target.value)}
                  className="form-control"
                >
                  <option value="">No criterion (Calculate raw errors only)</option>
                  {criteria.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.property_name}: {c.metric} {c.comparison_operator} {c.threshold} {c.unit}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Measurement Uncertainty (Optional)</label>
                <input
                  type="number"
                  step="0.001"
                  placeholder="0.05"
                  value={measUncertainty}
                  onChange={(e) => setMeasUncertainty(e.target.value)}
                  className="form-control text-mono"
                />
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--color-border-light)', paddingTop: 16 }}>
              <button
                type="submit"
                disabled={loading || !labExpId || !sampleId}
                className="btn btn-primary w-full"
                style={{ justifyContent: 'center', padding: '12px' }}
              >
                {loading ? 'Evaluating...' : 'Evaluate Physical Validation Result'}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* STEP 3: Validation Result Summary */}
      {step === 3 && valResult && (
        <div className="card">
          <div className="card-header">
            <h2 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileCheck className="w-5 h-5 text-emerald-600" />
              Experimental Validation Evaluation
            </h2>
            <span className="badge badge-planned">
              {valResult.validation_type} VALIDATION
            </span>
          </div>

          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="gs-metrics-row">
              <div className="gs-metric-card teal">
                <span className="gs-metric-label">Predicted Value</span>
                <span className="gs-metric-value" style={{ fontSize: '1.5rem' }}>{valResult.predicted_value} {valResult.unit}</span>
              </div>

              <div className="gs-metric-card emerald">
                <span className="gs-metric-label">Actual Lab Result</span>
                <span className="gs-metric-value" style={{ fontSize: '1.5rem' }}>{valResult.actual_value} {valResult.unit}</span>
              </div>

              <div className="gs-metric-card blue">
                <span className="gs-metric-label">Absolute Error</span>
                <span className="gs-metric-value" style={{ fontSize: '1.5rem' }}>{valResult.absolute_error}</span>
              </div>

              <div className="gs-metric-card amber">
                <span className="gs-metric-label">Criterion Evaluation</span>
                <span className="gs-metric-value" style={{ fontSize: '1rem', marginTop: 4 }}>
                  {valResult.criterion_result === 'SATISFIED' ? 'Satisfied' : 'Not Satisfied'}
                </span>
              </div>
            </div>

            {valResult.is_within_prediction_interval !== undefined && (
              <div className="alert alert-info">
                <strong>Prediction Interval Assessment: </strong>
                <span>
                  {valResult.is_within_prediction_interval
                    ? 'Actual lab result falls within the estimated prediction interval bounds.'
                    : 'Actual lab result falls outside the estimated prediction interval bounds.'}
                </span>
              </div>
            )}

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <Link
                to="/validation"
                className="btn btn-secondary"
                style={{ flex: 1, justifyContent: 'center' }}
              >
                Return to Validation Dashboard
              </Link>
              <button
                onClick={() => {
                  setStep(1)
                  setProspectiveExp(null)
                  setValResult(null)
                }}
                className="btn btn-primary"
                style={{ flex: 1, justifyContent: 'center' }}
              >
                Validate Another Prediction
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
