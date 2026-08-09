/**
 * GreenSynth Analytics — Upload Raw File Modal
 *
 * Modal dialog for uploading immutable raw laboratory dataset files.
 * Displays technique file-format validation and SHA-256 integrity details.
 */

import React, { useState } from 'react'
import type { Characterization } from '@/types'
import { TECHNIQUE_ALLOWED_EXTENSIONS } from '@/types'
import { characterizationService } from '@/services/characterizationService'
import { ErrorMessage } from '@/components/ErrorMessage'
import { InlineSpinner } from '@/components/LoadingSpinner'
import type { ApiError } from '@/types'

interface UploadRawFileModalProps {
  characterization: Characterization
  onClose: () => void
  onUploaded: () => void
}

export function UploadRawFileModal({
  characterization,
  onClose,
  onUploaded,
}: UploadRawFileModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)

  const allowedExts = TECHNIQUE_ALLOWED_EXTENSIONS[characterization.technique] ?? []
  const acceptString = allowedExts.map((e) => `.${e}`).join(',')

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null)
    const file = e.target.files?.[0]
    if (!file) {
      setSelectedFile(null)
      return
    }

    const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
    if (!allowedExts.includes(ext)) {
      setError(
        `File format '.${ext}' is not supported for ${characterization.technique}. Allowed: ${allowedExts.join(', ')}`
      )
      setSelectedFile(null)
      return
    }

    if (file.size > 50 * 1024 * 1024) {
      setError('File size exceeds maximum allowed limit of 50 MB.')
      setSelectedFile(null)
      return
    }

    setSelectedFile(file)
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) return

    setError(null)
    setUploading(true)
    try {
      await characterizationService.uploadRawFile(characterization.id, selectedFile)
      onUploaded()
      onClose()
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="upload-modal-title">
      <div className="modal" style={{ maxWidth: 540 }}>
        <div className="modal-header">
          <h2 className="modal-title" id="upload-modal-title">
            Upload Raw File ({characterization.technique})
          </h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <form onSubmit={handleUpload}>
          <div className="modal-body">
            {error && <ErrorMessage error={error} />}

            <div style={{
              background: 'var(--color-bg)',
              padding: 'var(--space-4)',
              borderRadius: 'var(--radius-md)',
              border: '1px dashed var(--color-border)',
              textAlign: 'center',
              marginBottom: 16,
            }}>
              <div style={{ fontSize: '2rem', marginBottom: 8 }}>📁</div>
              <input
                type="file"
                id="raw-file-input"
                accept={acceptString}
                onChange={handleFileChange}
                disabled={uploading}
                style={{ display: 'none' }}
              />
              <label
                htmlFor="raw-file-input"
                className="btn btn-secondary btn-sm"
                style={{ cursor: 'pointer', display: 'inline-block' }}
              >
                Choose File
              </label>

              {selectedFile ? (
                <div style={{ marginTop: 12, textAlign: 'left', background: 'white', padding: 12, borderRadius: 6, border: '1px solid var(--color-border)' }}>
                  <div style={{ fontWeight: 600 }}>{selectedFile.name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
                    Size: {(selectedFile.size / 1024).toFixed(1)} KB · Format: .{selectedFile.name.split('.').pop()?.toUpperCase()}
                  </div>
                </div>
              ) : (
                <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 8 }}>
                  Click to select original laboratory file.<br />
                  Allowed formats for <strong>{characterization.technique}</strong>: {allowedExts.join(', ')} (Max: 50 MB)
                </p>
              )}
            </div>

            <div style={{
              fontSize: '0.75rem',
              color: 'var(--color-text-secondary)',
              background: 'var(--color-info-light, #eff6ff)',
              padding: 10,
              borderRadius: 6,
              borderLeft: '3px solid var(--color-info)',
            }}>
              🔒 <strong>Raw File Guarantee:</strong> Uploaded files are stored in immutable raw storage. SHA-256 integrity checksums are generated automatically upon upload.
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={uploading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!selectedFile || uploading}
            >
              {uploading ? <InlineSpinner /> : 'Upload Raw File'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
