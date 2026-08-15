/**
 * GreenSynth Analytics — Sample Detail Page (Phase 3 Update)
 *
 * Displays:
 *  A. Sample Metadata (Code, Name, Material, Status, Parent Experiment link)
 *  B. Characterization Data & Raw File Management (XRD, UV-Vis, FTIR, SEM, Electrical)
 *  C. Immutable raw file upload, SHA-256 checksum verification, and download access.
 */

import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import type {
  Characterization,
  RawFile,
  Sample,
  SampleStatus,
  SampleUpdate,
} from '@/types'
import { sampleService } from '@/services/sampleService'
import { characterizationService } from '@/services/characterizationService'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorMessage } from '@/components/ErrorMessage'
import { StatusBadge } from '@/components/StatusBadge'
import { PageHeader } from '@/components/PageHeader'
import { AddCharacterizationModal } from '@/components/AddCharacterizationModal'
import { UploadRawFileModal } from '@/components/UploadRawFileModal'
import { FileMetadataModal } from '@/components/FileMetadataModal'
import { XrdAnalysisModal } from '@/components/XrdAnalysisModal'
import { UvVisAnalysisModal } from '@/components/UvVisAnalysisModal'
import { ElectricalAnalysisModal } from '@/components/ElectricalAnalysisModal'
import { FtirAnalysisModal } from '@/components/FtirAnalysisModal'
import { SemAnalysisModal } from '@/components/SemAnalysisModal'
import type { ApiError } from '@/types'

const STATUSES: { value: SampleStatus; label: string }[] = [
  { value: 'PREPARED', label: 'Prepared' },
  { value: 'READY_FOR_CHARACTERIZATION', label: 'Ready for Characterization' },
  { value: 'UNDER_ANALYSIS', label: 'Under Analysis' },
  { value: 'COMPLETED', label: 'Completed' },
]

export default function SampleDetail() {
  const { id } = useParams<{ id: string }>()

  const [sample, setSample] = useState<Sample | null>(null)
  const [characterizations, setCharacterizations] = useState<Characterization[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState<SampleUpdate>({})
  const [saving, setSaving] = useState(false)
  const [editError, setEditError] = useState<string | null>(null)

  const [showAddCharModal, setShowAddCharModal] = useState(false)
  const [uploadingForChar, setUploadingForChar] = useState<Characterization | null>(null)
  const [selectedFileMeta, setSelectedFileMeta] = useState<RawFile | null>(null)
  const [analyzingXrdChar, setAnalyzingXrdChar] = useState<Characterization | null>(null)
  const [analyzingUvVisChar, setAnalyzingUvVisChar] = useState<Characterization | null>(null)
  const [analyzingElecChar, setAnalyzingElecChar] = useState<Characterization | null>(null)
  const [analyzingFtirChar, setAnalyzingFtirChar] = useState<Characterization | null>(null)
  const [inspectingSemChar, setInspectingSemChar] = useState<Characterization | null>(null)

  const fetchSampleAndChars = async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const [samp, chs] = await Promise.all([
        sampleService.getById(id),
        characterizationService.listSampleCharacterizations(id),
      ])
      setSample(samp)
      setCharacterizations(chs)
    } catch (e: unknown) {
      setError((e as ApiError)?.message ?? 'Failed to load sample.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSampleAndChars()
  }, [id])

  const startEdit = () => {
    if (!sample) return
    setEditForm({
      name: sample.name,
      material: sample.material ?? '',
      description: sample.description ?? '',
      notes: sample.notes ?? '',
      status: sample.status,
    })
    setEditing(true)
  }

  const handleSave = async () => {
    if (!id) return
    setSaving(true)
    setEditError(null)
    try {
      await sampleService.update(id, editForm)
      setEditing(false)
      await fetchSampleAndChars()
    } catch (e: unknown) {
      setEditError((e as ApiError)?.message ?? 'Failed to update sample.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <LoadingSpinner message="Loading sample and characterizations…" />
  if (error) return <ErrorMessage error={error} onRetry={fetchSampleAndChars} />
  if (!sample) return null

  return (
    <div>
      {/* Breadcrumb Traceability Navigation */}
      <div className="breadcrumb">
        <Link to="/experiments">Experiments</Link>
        <span className="breadcrumb-separator">›</span>
        <Link to={`/experiments/${sample.experiment_id}`}>Experiment</Link>
        <span className="breadcrumb-separator">›</span>
        <Link to="/samples">Samples</Link>
        <span className="breadcrumb-separator">›</span>
        <span className="breadcrumb-current">{sample.sample_code}</span>
      </div>

      <PageHeader
        title={sample.name}
        subtitle={`${sample.sample_code} · ${sample.material ?? 'Semiconductor Specimen'}`}
        actions={
          <div style={{ display: 'flex', gap: 8 }}>
            {!editing && (
              <button className="btn btn-secondary" onClick={startEdit}>
                Edit Metadata
              </button>
            )}
            <StatusBadge status={sample.status} />
          </div>
        }
      />

      {/* A. Sample Metadata Card */}
      <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
        <div className="card-header">
          <h2>A. Sample Metadata</h2>
        </div>
        <div className="card-body">
          {editing ? (
            <>
              {editError && <ErrorMessage error={editError} />}
              <div className="form-grid" style={{ marginBottom: 'var(--space-6)' }}>
                <div className="form-group span-2">
                  <label className="form-label required">Sample Name</label>
                  <input
                    className="form-control"
                    value={editForm.name ?? ''}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Material</label>
                  <input
                    className="form-control"
                    value={editForm.material ?? ''}
                    onChange={(e) => setEditForm({ ...editForm, material: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Status</label>
                  <select
                    className="form-control"
                    value={editForm.status}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value as SampleStatus })}
                  >
                    {STATUSES.map((st) => (
                      <option key={st.value} value={st.value}>{st.label}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group span-2">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-control"
                    rows={3}
                    value={editForm.description ?? ''}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  />
                </div>
                <div className="form-group span-2">
                  <label className="form-label">Notes</label>
                  <textarea
                    className="form-control"
                    rows={3}
                    value={editForm.notes ?? ''}
                    onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                  />
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                  {saving ? 'Saving…' : 'Save Changes'}
                </button>
                <button className="btn btn-secondary" onClick={() => setEditing(false)} disabled={saving}>
                  Cancel
                </button>
              </div>
            </>
          ) : (
            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Sample Code</span>
                <span className="detail-value code">{sample.sample_code}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Status</span>
                <StatusBadge status={sample.status} />
              </div>
              <div className="detail-item">
                <span className="detail-label">Material</span>
                <span className="detail-value">{sample.material ?? 'Not specified'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Parent Experiment</span>
                <span className="detail-value">
                  <Link to={`/experiments/${sample.experiment_id}`} className="table-link code">
                    {sample.experiment_id}
                  </Link>
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Created At</span>
                <span className="detail-value">
                  {new Date(sample.created_at).toLocaleString()}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Last Updated</span>
                <span className="detail-value">
                  {new Date(sample.updated_at).toLocaleString()}
                </span>
              </div>
              {sample.description && (
                <div className="detail-item" style={{ gridColumn: '1 / -1' }}>
                  <span className="detail-label">Description</span>
                  <span className="detail-value" style={{ lineHeight: 1.6 }}>
                    {sample.description}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* B. Laboratory Characterization Data & Raw File Management */}
      <div className="card">
        <div className="card-header">
          <h2>B. Laboratory Characterization Data ({characterizations.length})</h2>
          <button className="btn btn-primary btn-sm" onClick={() => setShowAddCharModal(true)}>
            + Add Characterization Run
          </button>
        </div>

        <div className="card-body">
          {characterizations.length === 0 ? (
            <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
              <p style={{ marginBottom: 12 }}>No characterization runs recorded for this sample yet.</p>
              <button className="btn btn-primary btn-sm" onClick={() => setShowAddCharModal(true)}>
                Record Characterization
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {characterizations.map((ch) => (
                <div
                  key={ch.id}
                  style={{
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    overflow: 'hidden',
                    background: 'white',
                  }}
                >
                  {/* Characterization Run Header */}
                  <div style={{
                    padding: 'var(--space-3) var(--space-4)',
                    background: 'var(--color-bg)',
                    borderBottom: '1px solid var(--color-border-light)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <span className="badge badge-active" style={{ fontSize: '0.8125rem', fontWeight: 700 }}>
                        {ch.technique}
                      </span>
                      <span style={{ fontWeight: 600, fontSize: '0.9375rem' }}>
                        {ch.instrument_name ?? ch.technique} {ch.instrument_model ? `(${ch.instrument_model})` : ''}
                      </span>
                      <span className="badge badge-planned" style={{ fontSize: '0.7rem' }}>
                        Status: {ch.status}
                      </span>
                    </div>

                    <div style={{ display: 'flex', gap: 8 }}>
                      {ch.technique === 'XRD' && ch.raw_files.length > 0 && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => setAnalyzingXrdChar(ch)}
                        >
                          Analyze XRD Pattern
                        </button>
                      )}
                      {ch.technique === 'UV_VIS' && ch.raw_files.length > 0 && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => setAnalyzingUvVisChar(ch)}
                        >
                          Analyze UV-Vis Spectrum
                        </button>
                      )}
                      {ch.technique === 'ELECTRICAL' && ch.raw_files.length > 0 && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => setAnalyzingElecChar(ch)}
                        >
                          Analyze Electrical Data
                        </button>
                      )}
                      {ch.technique === 'FTIR' && ch.raw_files.length > 0 && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => setAnalyzingFtirChar(ch)}
                        >
                          Analyze FTIR Spectrum
                        </button>
                      )}
                      {ch.technique === 'SEM' && ch.raw_files.length > 0 && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => setInspectingSemChar(ch)}
                        >
                          Inspect SEM Image & Measurements
                        </button>
                      )}
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => setUploadingForChar(ch)}
                      >
                        Upload Raw File
                      </button>
                    </div>
                  </div>

                  {/* Run Metadata Details */}
                  <div style={{ padding: 'var(--space-3) var(--space-4)', fontSize: '0.8125rem', color: 'var(--color-text-secondary)', borderBottom: '1px solid var(--color-border-light)' }}>
                    <span>Operator: <strong>{ch.operator ?? '—'}</strong></span> · {' '}
                    <span>Date: <strong>{ch.characterization_date ? new Date(ch.characterization_date).toLocaleDateString() : '—'}</strong></span>
                    {ch.notes && (
                      <div style={{ marginTop: 4, fontStyle: 'italic' }}>
                        Notes: {ch.notes}
                      </div>
                    )}
                  </div>

                  {/* Uploaded Raw Files Table */}
                  <div style={{ padding: 'var(--space-3) var(--space-4)' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: 8 }}>
                      Uploaded Raw Files ({ch.raw_files.length})
                    </div>

                    {ch.raw_files.length === 0 ? (
                      <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                        No raw files uploaded for this characterization run yet.{' '}
                        <button
                          style={{ background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}
                          onClick={() => setUploadingForChar(ch)}
                        >
                          Upload file now →
                        </button>
                      </div>
                    ) : (
                      <div className="table-container">
                        <table>
                          <thead>
                            <tr>
                              <th>Original Filename</th>
                              <th>Format</th>
                              <th>Size</th>
                              <th>SHA-256 Checksum</th>
                              <th>Uploaded At</th>
                              <th>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {ch.raw_files.map((file) => (
                              <tr key={file.id}>
                                <td style={{ fontWeight: 600 }}>{file.original_filename}</td>
                                <td>
                                  <span className="badge badge-planned" style={{ fontSize: '0.65rem' }}>
                                    .{file.file_extension.toUpperCase()}
                                  </span>
                                </td>
                                <td style={{ color: 'var(--color-text-secondary)' }}>
                                  {(file.file_size / 1024).toFixed(1)} KB
                                </td>
                                <td className="text-mono" style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                                  {file.checksum.slice(0, 12)}…
                                </td>
                                <td style={{ color: 'var(--color-text-secondary)' }}>
                                  {new Date(file.uploaded_at).toLocaleString()}
                                </td>
                                <td>
                                  <div style={{ display: 'flex', gap: 6 }}>
                                    <button
                                      className="btn btn-secondary btn-sm"
                                      onClick={() => setSelectedFileMeta(file)}
                                    >
                                      Metadata
                                    </button>
                                    <a
                                      href={characterizationService.getDownloadUrl(file.id)}
                                      className="btn btn-primary btn-sm"
                                      download={file.original_filename}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    >
                                      ⬇ Download
                                    </a>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add Characterization Modal */}
      {showAddCharModal && (
        <AddCharacterizationModal
          sampleId={sample.id}
          onClose={() => setShowAddCharModal(false)}
          onSuccess={fetchSampleAndChars}
        />
      )}

      {/* Upload Raw File Modal */}
      {uploadingForChar && (
        <UploadRawFileModal
          characterization={uploadingForChar}
          onClose={() => setUploadingForChar(null)}
          onUploaded={fetchSampleAndChars}
        />
      )}

      {/* File Metadata Modal */}
      {selectedFileMeta && (
        <FileMetadataModal
          file={selectedFileMeta}
          onClose={() => setSelectedFileMeta(null)}
        />
      )}

      {/* XRD Analysis Dashboard Modal */}
      {analyzingXrdChar && (
        <XrdAnalysisModal
          characterization={analyzingXrdChar}
          onClose={() => setAnalyzingXrdChar(null)}
        />
      )}

      {/* UV-Vis Tauc Analysis Dashboard Modal */}
      {analyzingUvVisChar && (
        <UvVisAnalysisModal
          characterization={analyzingUvVisChar}
          onClose={() => setAnalyzingUvVisChar(null)}
        />
      )}

      {/* Electrical Property Analysis Dashboard Modal */}
      {analyzingElecChar && (
        <ElectricalAnalysisModal
          characterization={analyzingElecChar}
          onClose={() => setAnalyzingElecChar(null)}
        />
      )}

      {/* FTIR Spectroscopy Analysis Dashboard Modal */}
      {analyzingFtirChar && (
        <FtirAnalysisModal
          characterization={analyzingFtirChar}
          onClose={() => setAnalyzingFtirChar(null)}
        />
      )}

      {/* SEM Micrograph & Measurement Modal */}
      {inspectingSemChar && inspectingSemChar.raw_files.length > 0 && (
        <SemAnalysisModal
          characterization={inspectingSemChar}
          file={inspectingSemChar.raw_files[inspectingSemChar.raw_files.length - 1]}
          onClose={() => setInspectingSemChar(null)}
        />
      )}
    </div>
  )
}
