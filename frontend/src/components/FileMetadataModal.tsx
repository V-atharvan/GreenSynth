/**
 * GreenSynth Analytics — File Metadata Modal
 *
 * Displays full file metadata (SHA-256 checksum, size, storage path, upload timestamp)
 * and provides download access to the original raw laboratory file.
 */

import React, { useState } from 'react'
import { X } from 'lucide-react'
import type { RawFile } from '@/types'
import { characterizationService } from '@/services/characterizationService'

interface FileMetadataModalProps {
  file: RawFile
  isOpen?: boolean
  onClose: () => void
}

export function FileMetadataModal({ file, isOpen = true, onClose }: FileMetadataModalProps) {
  if (!isOpen) return null

  const [copied, setCopied] = useState(false)

  const downloadUrl = characterizationService.getDownloadUrl(file.id)

  const handleCopyChecksum = () => {
    navigator.clipboard.writeText(file.checksum)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const formatBytes = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="file-meta-title">
      <div className="modal" style={{ maxWidth: 620 }}>
        <div className="modal-header">
          <h2 className="modal-title" id="file-meta-title">
            Raw File Metadata
          </h2>
          <button className="modal-close" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>

        <div className="modal-body">
          <div className="detail-grid">
            <div className="detail-item" style={{ gridColumn: '1 / -1' }}>
              <span className="detail-label">Original Filename</span>
              <span className="detail-value" style={{ fontWeight: 600, fontSize: '1rem' }}>
                {file.original_filename}
              </span>
            </div>

            <div className="detail-item">
              <span className="detail-label">File Format / Extension</span>
              <span className="detail-value text-mono">
                .{file.file_extension.toUpperCase()} ({file.mime_type || 'binary'})
              </span>
            </div>

            <div className="detail-item">
              <span className="detail-label">File Size</span>
              <span className="detail-value">{formatBytes(file.file_size)}</span>
            </div>

            <div className="detail-item" style={{ gridColumn: '1 / -1' }}>
              <span className="detail-label">SHA-256 Checksum (Integrity Hash)</span>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span className="detail-value text-mono" style={{
                  fontSize: '0.8125rem',
                  background: 'var(--color-bg)',
                  padding: '4px 8px',
                  borderRadius: 4,
                  wordBreak: 'break-all',
                  flex: 1,
                }}>
                  {file.checksum}
                </span>
                <button className="btn btn-secondary btn-sm" onClick={handleCopyChecksum}>
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
            </div>

            <div className="detail-item" style={{ gridColumn: '1 / -1' }}>
              <span className="detail-label">Storage Path (Relative)</span>
              <span className="detail-value text-mono" style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                data/raw/{file.storage_path}
              </span>
            </div>

            <div className="detail-item">
              <span className="detail-label">Uploaded At</span>
              <span className="detail-value">
                {new Date(file.uploaded_at).toLocaleString()}
              </span>
            </div>

            <div className="detail-item">
              <span className="detail-label">Storage Integrity Status</span>
              <span className="badge badge-active">IMMUTABLE / ACTIVE</span>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
          <a
            href={downloadUrl}
            className="btn btn-primary"
            download={file.original_filename}
            target="_blank"
            rel="noopener noreferrer"
          >
            ⬇ Download Original File
          </a>
        </div>
      </div>
    </div>
  )
}
