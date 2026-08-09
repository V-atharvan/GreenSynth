/**
 * GreenSynth Analytics — Add Characterization Modal
 *
 * Modal form for creating a new laboratory characterization run (XRD, UV-Vis, FTIR, SEM, Electrical).
 */

import React, { useState } from 'react'
import type { CharacterizationCreate, TechniqueType } from '@/types'
import { characterizationService } from '@/services/characterizationService'
import { ErrorMessage } from '@/components/ErrorMessage'
import { InlineSpinner } from '@/components/LoadingSpinner'
import type { ApiError } from '@/types'

interface AddCharacterizationModalProps {
  sampleId: string
  onClose: () => void
  onCreated: () => void
}

const TECHNIQUES: { value: TechniqueType; label: string; desc: string }[] = [
  { value: 'XRD', label: 'XRD (X-Ray Diffraction)', desc: 'Phase identification & crystal structure' },
  { value: 'UV_VIS', label: 'UV-Vis Spectroscopy', desc: 'Optical absorption & bandgap measurement' },
  { value: 'FTIR', label: 'FTIR Spectroscopy', desc: 'Functional groups & chemical bonding' },
  { value: 'SEM', label: 'SEM (Scanning Electron Microscopy)', desc: 'Surface morphology & microstructure' },
  { value: 'ELECTRICAL', label: 'Electrical Measurements', desc: 'IV curves, resistivity & conductivity' },
]

export function AddCharacterizationModal({
  sampleId,
  onClose,
  onCreated,
}: AddCharacterizationModalProps) {
  const [form, setForm] = useState<CharacterizationCreate>({
    sample_id: sampleId,
    technique: 'XRD',
    operator: '',
    instrument_name: '',
    instrument_model: '',
    notes: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await characterizationService.createCharacterization(form)
      onCreated()
      onClose()
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Failed to create characterization run.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="add-char-title">
      <div className="modal" style={{ maxWidth: 580 }}>
        <div className="modal-header">
          <h2 className="modal-title" id="add-char-title">
            Add Laboratory Characterization Run
          </h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && <ErrorMessage error={error} />}

            <div className="form-grid">
              <div className="form-group span-2">
                <label className="form-label required" htmlFor="tech-select">
                  Characterization Technique
                </label>
                <select
                  id="tech-select"
                  className="form-control"
                  value={form.technique}
                  onChange={(e) => setForm({ ...form, technique: e.target.value as TechniqueType })}
                  required
                >
                  {TECHNIQUES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label} — {t.desc}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="char-date">Characterization Date</label>
                <input
                  id="char-date"
                  type="date"
                  className="form-control"
                  value={form.characterization_date ?? ''}
                  onChange={(e) => setForm({ ...form, characterization_date: e.target.value || undefined })}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="char-op">Operator / Analyst</label>
                <input
                  id="char-op"
                  className="form-control"
                  placeholder="e.g. Dr. Jane Doe"
                  value={form.operator ?? ''}
                  onChange={(e) => setForm({ ...form, operator: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="inst-name">Instrument Name</label>
                <input
                  id="inst-name"
                  className="form-control"
                  placeholder="e.g. Rigaku SmartLab"
                  value={form.instrument_name ?? ''}
                  onChange={(e) => setForm({ ...form, instrument_name: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="inst-model">Instrument Model</label>
                <input
                  id="inst-model"
                  className="form-control"
                  placeholder="e.g. SmartLab SE 9kW"
                  value={form.instrument_model ?? ''}
                  onChange={(e) => setForm({ ...form, instrument_model: e.target.value })}
                />
              </div>

              <div className="form-group span-2">
                <label className="form-label" htmlFor="char-notes">Measurement Conditions / Notes</label>
                <textarea
                  id="char-notes"
                  className="form-control"
                  rows={3}
                  placeholder="Scan range, radiation wavelength, voltage, current, atmosphere, etc."
                  value={form.notes ?? ''}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                />
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? <InlineSpinner /> : 'Create Characterization Record'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
