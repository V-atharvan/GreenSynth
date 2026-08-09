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
  Building2,
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
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <FlaskConical className="w-7 h-7 text-teal-400" />
          Prospective Experimental Validation
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Bridge Model Predictions with Physical Laboratory Characterization Results (Level 3 Validation).
        </p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          {error}
        </div>
      )}

      {/* Progress Steps */}
      <div className="flex items-center justify-between bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs font-semibold text-slate-400">
        <div className={`flex items-center gap-2 ${step >= 1 ? 'text-teal-400' : ''}`}>
          <span className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">1</span>
          Select & Review Prediction
        </div>
        <ArrowRight className="w-4 h-4 text-slate-600" />
        <div className={`flex items-center gap-2 ${step >= 2 ? 'text-teal-400' : ''}`}>
          <span className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">2</span>
          Link Lab Experiment
        </div>
        <ArrowRight className="w-4 h-4 text-slate-600" />
        <div className={`flex items-center gap-2 ${step >= 3 ? 'text-teal-400' : ''}`}>
          <span className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">3</span>
          Validation Result
        </div>
      </div>

      {/* STEP 1: Select & Approve Prediction */}
      {step === 1 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <h2 className="text-lg font-semibold text-slate-100">Step 1: Select Model Prediction</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Select Prediction Record</label>
              <select
                value={selectedPredId}
                onChange={(e) => setSelectedPredId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg p-3"
              >
                {predictions.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.predicted_property}: {p.predicted_value} {p.unit} [{p.applicability_status}]
                  </option>
                ))}
              </select>
            </div>

            {selectedPred && (
              <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-400 uppercase">Target Property</span>
                  <span className="text-sm font-bold text-slate-100">{selectedPred.predicted_property}</span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-xs">
                  <div>
                    <span className="text-slate-400 block">Predicted Value</span>
                    <span className="text-lg font-bold text-teal-400">{selectedPred.predicted_value} {selectedPred.unit}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">95% Uncertainty Bounds</span>
                    <span className="text-sm font-semibold text-indigo-400">
                      {selectedPred.uncertainty_lower !== undefined ? `[${selectedPred.uncertainty_lower}, ${selectedPred.uncertainty_upper}]` : 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Applicability Domain</span>
                    <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {selectedPred.applicability_status}
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-xs font-semibold text-slate-400 uppercase block mb-2">Input Synthesis Parameters</span>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono text-slate-300">
                    {Object.entries(selectedPred.input_parameters).map(([k, v]) => (
                      <div key={k} className="bg-slate-900/60 px-3 py-2 rounded-lg border border-slate-800">
                        {k}: <span className="text-teal-400 font-bold">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <button
            onClick={handleApproveProspective}
            disabled={loading || !selectedPred}
            className="w-full py-3 bg-emerald-500 text-slate-950 font-bold rounded-lg hover:bg-emerald-400 transition-colors disabled:opacity-50"
          >
            {loading ? 'Approving...' : 'Approve Prediction for Physical Lab Synthesis'}
          </button>
        </div>
      )}

      {/* STEP 2: Link Physical Characterization */}
      {step === 2 && prospectiveExp && (
        <form onSubmit={handleLinkResult} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <h2 className="text-lg font-semibold text-slate-100">Step 2: Link Laboratory Experiment & Characterization</h2>

          <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-xl text-xs flex items-center gap-2">
            <CheckCircle className="w-4 h-4 shrink-0" />
            Prospective Experiment Approved (ID: {prospectiveExp.id.slice(0, 8)}...). Proceed to enter lab execution details.
          </div>

          <div className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-400 uppercase mb-1">Laboratory Experiment UUID</label>
              <input
                type="text"
                required
                placeholder="e.g. 84c2e37a-e483-4fc8-b9dd-147e91c01738"
                value={labExpId}
                onChange={(e) => setLabExpId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg p-3 font-mono"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-400 uppercase mb-1">Characterized Sample UUID</label>
              <input
                type="text"
                required
                placeholder="e.g. c0ca9240-2e5d-4733-9ce6-0b9062f90687"
                value={sampleId}
                onChange={(e) => setSampleId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg p-3 font-mono"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-400 uppercase mb-1">Validation Criterion (Optional)</label>
              <select
                value={selectedCritId}
                onChange={(e) => setSelectedCritId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-slate-200 rounded-lg p-3"
              >
                <option value="">No criterion (Calculate raw errors only)</option>
                {criteria.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.property_name}: {c.metric} {c.comparison_operator} {c.threshold} {c.unit}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-400 uppercase mb-1">Measurement Uncertainty (Optional)</label>
              <input
                type="number"
                step="0.001"
                placeholder="0.05"
                value={measUncertainty}
                onChange={(e) => setMeasUncertainty(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg p-3 font-mono"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !labExpId || !sampleId}
            className="w-full py-3 bg-indigo-500 text-white font-bold rounded-lg hover:bg-indigo-400 transition-colors disabled:opacity-50"
          >
            {loading ? 'Evaluating...' : 'Evaluate Physical Validation Result'}
          </button>
        </form>
      )}

      {/* STEP 3: Validation Result Summary */}
      {step === 3 && valResult && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-emerald-400" />
              Experimental Validation Evaluation
            </h2>
            <span className="px-3 py-1 text-xs font-bold rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              {valResult.validation_type} VALIDATION
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            <div className="bg-slate-800/60 p-4 rounded-xl">
              <span className="text-slate-400 block">Predicted Value</span>
              <span className="text-xl font-bold text-teal-400">{valResult.predicted_value} {valResult.unit}</span>
            </div>

            <div className="bg-slate-800/60 p-4 rounded-xl">
              <span className="text-slate-400 block">Actual Lab Result</span>
              <span className="text-xl font-bold text-emerald-400">{valResult.actual_value} {valResult.unit}</span>
            </div>

            <div className="bg-slate-800/60 p-4 rounded-xl">
              <span className="text-slate-400 block">Absolute Error</span>
              <span className="text-xl font-bold text-slate-200">{valResult.absolute_error}</span>
            </div>

            <div className="bg-slate-800/60 p-4 rounded-xl">
              <span className="text-slate-400 block">Criterion Evaluation</span>
              <span className={`text-sm font-bold mt-1 block ${
                valResult.criterion_result === 'SATISFIED' ? 'text-emerald-400' : 'text-amber-400'
              }`}>
                {valResult.criterion_result === 'SATISFIED' ? 'Criterion satisfied' : 'Criterion not satisfied'}
              </span>
            </div>
          </div>

          {valResult.is_within_prediction_interval !== undefined && (
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700 text-xs text-slate-300">
              <span className="font-bold text-slate-100">Prediction Interval Assessment: </span>
              {valResult.is_within_prediction_interval
                ? 'Actual lab result falls within the estimated prediction interval bounds.'
                : 'Actual lab result falls outside the estimated prediction interval bounds.'}
            </div>
          )}

          <div className="flex gap-4">
            <Link
              to="/validation"
              className="flex-1 py-3 bg-slate-800 text-slate-200 text-center font-semibold rounded-lg hover:bg-slate-700 transition-colors"
            >
              Return to Validation Dashboard
            </Link>
            <button
              onClick={() => {
                setStep(1)
                setProspectiveExp(null)
                setValResult(null)
              }}
              className="flex-1 py-3 bg-emerald-500 text-slate-950 font-bold rounded-lg hover:bg-emerald-400 transition-colors"
            >
              Validate Another Prediction
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
