/**
 * GreenSynth Analytics — Add Characterization Modal
 *
 * Modal form for creating a new laboratory characterization run (XRD, UV-Vis, FTIR, SEM, Electrical).
 */

import React, { useState } from 'react'
import { X } from 'lucide-react'
import type { CharacterizationCreate, TechniqueType } from '@/types'
import { characterizationService } from '@/services/characterizationService'
import { ErrorMessage } from '@/components/ErrorMessage'
import type { ApiError } from '@/types'

const TECHNIQUE_OPTIONS: { value: TechniqueType; label: string }[] = [
  { value: 'XRD', label: 'X-Ray Diffraction (XRD)' },
  { value: 'UV_VIS', label: 'UV-Vis Spectroscopy' },
  { value: 'FTIR', label: 'FTIR Spectroscopy' },
  { value: 'SEM', label: 'Scanning Electron Microscopy (SEM)' },
  { value: 'ELECTRICAL', label: 'Electrical I-V Measurement' },
]

interface AddCharacterizationModalProps {
  sampleId: string
  isOpen?: boolean
  onClose: () => void
  onSuccess: () => void
}

export function AddCharacterizationModal({
  sampleId,
  isOpen = true,
  onClose,
  onSuccess,
}: AddCharacterizationModalProps) {
  if (!isOpen) return null

  const [technique, setTechnique] = useState<TechniqueType>('XRD')
  const [instrumentName, setInstrumentName] = useState('')
  const [operator, setOperator] = useState('')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)

    try {
      const payload: CharacterizationCreate = {
        sample_id: sampleId,
        technique,
        instrument_name: instrumentName.trim() || undefined,
        operator: operator.trim() || undefined,
        notes: notes.trim() || undefined,
      }
      await characterizationService.createCharacterization(payload)
      onSuccess()
      onClose()
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Failed to record characterization run.')
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
          <button className="modal-close" onClick={onClose} aria-label="Close"><X size={18} /></button>
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
                  value={technique}
                  onChange={(e) => setTechnique(e.target.value as TechniqueType)}
                  required
                >
                  {TECHNIQUE_OPTIONS.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="char-op">Operator / Analyst</label>
                <input
                  id="char-op"
                  className="form-control"
                  placeholder="e.g. Dr. Jane Doe"
                  value={operator}
                  onChange={(e) => setOperator(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="inst-name">Instrument Name</label>
                <input
                  id="inst-name"
                  className="form-control"
                  placeholder="e.g. Rigaku SmartLab"
                  value={instrumentName}
                  onChange={(e) => setInstrumentName(e.target.value)}
                />
              </div>

              <div className="form-group span-2">
                <label className="form-label" htmlFor="char-notes">Measurement Conditions / Notes</label>
                <textarea
                  id="char-notes"
                  className="form-control"
                  rows={3}
                  placeholder="Scan range, radiation wavelength, voltage, current, atmosphere, etc."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
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
              {saving ? 'Saving...' : 'Create Characterization Record'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
