/**
 * GreenSynth Analytics — Dataset Builder Modal
 *
 * Wizard for creating logical comparison datasets referencing selected project samples & variables.
 */

import React, { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import type { DatasetCreateInput, ProjectSummary, SampleSummary } from '@/types'
import { experimentService } from '@/services/experimentService'
import { projectService } from '@/services/projectService'
import { sampleService } from '@/services/sampleService'
import { analysisService } from '@/services/analysisService'
import { ErrorMessage } from '@/components/ErrorMessage'
import { InlineSpinner, LoadingSpinner } from '@/components/LoadingSpinner'
import type { ApiError } from '@/types'

interface DatasetBuilderModalProps {
  onClose: () => void
  onDatasetCreated: (datasetId: string) => void
}

const DEFAULT_VARIABLES = [
  'substrate_temperature',
  'spray_rate',
  'extract_concentration',
  'Electrical Conductivity',
  'Electrical Resistivity',
  'Optical Band Gap',
  'Crystallite Size',
]

export function DatasetBuilderModal({ onClose, onDatasetCreated }: DatasetBuilderModalProps) {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProjId, setSelectedProjId] = useState('')
  const [samples, setSamples] = useState<SampleSummary[]>([])
  const [selectedSampleIds, setSelectedSampleIds] = useState<string[]>([])
  const [selectedVars, setSelectedVars] = useState<string[]>([
    'substrate_temperature',
    'Electrical Conductivity',
  ])
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    projectService.getAll()
      .then((projs) => {
        setProjects(projs)
        if (projs.length > 0) {
          setSelectedProjId(projs[0].id)
        }
      })
      .catch((err: unknown) => setError((err as ApiError)?.message ?? 'Failed to load projects.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selectedProjId) return
    sampleService.getAll()
      .then((sList) => {
        setSamples(sList)
        setSelectedSampleIds(sList.map((s) => s.id))
      })
      .catch((err: unknown) => setError((err as ApiError)?.message ?? 'Failed to load samples.'))
  }, [selectedProjId])

  const handleToggleSample = (id: string) => {
    if (selectedSampleIds.includes(id)) {
      setSelectedSampleIds(selectedSampleIds.filter((sid) => sid !== id))
    } else {
      setSelectedSampleIds([...selectedSampleIds, id])
    }
  }

  const handleToggleVar = (v: string) => {
    if (selectedVars.includes(v)) {
      setSelectedVars(selectedVars.filter((item) => item !== v))
    } else {
      setSelectedVars([...selectedVars, v])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedProjId || selectedSampleIds.length === 0 || selectedVars.length === 0 || !name.trim()) return
    setError(null)
    setSubmitting(true)
    try {
      const payload: DatasetCreateInput = {
        project_id: selectedProjId,
        name: name.trim(),
        description: description.trim() || undefined,
        sample_ids: selectedSampleIds,
        variables: selectedVars,
      }
      const ds = await analysisService.createDataset(payload)
      onDatasetCreated(ds.id)
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Failed to create dataset.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="dataset-builder-title">
      <div className="modal" style={{ maxWidth: 800, maxHeight: '90vh', overflowY: 'auto' }}>
        <div className="modal-header">
          <h2 className="modal-title" id="dataset-builder-title">
            Dataset Builder (Sample & Variable Selection)
          </h2>
          <button className="modal-close" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>

        <div className="modal-body">
          {error && <ErrorMessage error={error} />}

          {loading ? (
            <LoadingSpinner message="Loading research projects..." />
          ) : (
            <form onSubmit={handleSubmit}>
              {/* Step 1: Select Project */}
              <div className="form-group" style={{ marginBottom: 16 }}>
                <label className="form-label">Research Project</label>
                <select
                  className="form-control"
                  value={selectedProjId}
                  onChange={(e) => setSelectedProjId(e.target.value)}
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.project_code} — {p.name} ({p.material})
                    </option>
                  ))}
                </select>
              </div>

              {/* Step 2: Select Name & Description */}
              <div className="form-grid" style={{ marginBottom: 16 }}>
                <div className="form-group">
                  <label className="form-label">Dataset Name</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    placeholder="e.g. Temp vs Conductivity Study"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Description (Optional)</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Comparing 300C vs 400C ZnO thin films"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
              </div>

              {/* Step 3: Select Variables */}
              <div style={{ marginBottom: 16, background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid #e2e8f0' }}>
                <label className="form-label" style={{ fontWeight: 700, marginBottom: 8 }}>
                  Select Synthesis Parameters & Material Properties ({selectedVars.length} selected)
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8 }}>
                  {DEFAULT_VARIABLES.map((v) => (
                    <label key={v} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8125rem', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={selectedVars.includes(v)}
                        onChange={() => handleToggleVar(v)}
                      />
                      {v}
                    </label>
                  ))}
                </div>
              </div>

              {/* Step 4: Select Samples */}
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <label className="form-label" style={{ fontWeight: 700, margin: 0 }}>
                    Select Project Samples ({selectedSampleIds.length} of {samples.length} selected)
                  </label>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      if (selectedSampleIds.length === samples.length) {
                        setSelectedSampleIds([])
                      } else {
                        setSelectedSampleIds(samples.map((s) => s.id))
                      }
                    }}
                  >
                    {selectedSampleIds.length === samples.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>

                <div style={{ maxHeight: 200, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: 6, padding: 8 }}>
                  {samples.length === 0 ? (
                    <div style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem', padding: 12, textAlign: 'center' }}>
                      No samples recorded under this project yet.
                    </div>
                  ) : (
                    samples.map((s) => (
                      <label key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 6px', borderBottom: '1px solid #f1f5f9', fontSize: '0.8125rem', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={selectedSampleIds.includes(s.id)}
                          onChange={() => handleToggleSample(s.id)}
                        />
                        <strong style={{ minWidth: 100 }}>{s.sample_code}</strong>
                        <span>{s.name}</span>
                      </label>
                    ))
                  )}
                </div>
              </div>

              <div className="modal-footer" style={{ padding: '12px 0 0 0', margin: 0 }}>
                <button type="button" className="btn btn-secondary" onClick={onClose}>
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitting || selectedSampleIds.length === 0 || selectedVars.length === 0 || !name.trim()}
                >
                  {submitting ? <InlineSpinner /> : 'Create Comparison Dataset'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
