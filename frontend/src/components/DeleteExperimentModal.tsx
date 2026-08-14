/**
 * GreenSynth Analytics — Delete Experiment Double-Safety Confirmation Modal
 */

import React, { useState, useEffect } from 'react'
import { InlineSpinner } from './LoadingSpinner'
import { ErrorMessage } from './ErrorMessage'

interface DeleteExperimentModalProps {
  isOpen: boolean
  experimentCode: string
  experimentTitle: string
  isDeleting: boolean
  error: string | null
  onConfirm: () => void
  onCancel: () => void
}

export function DeleteExperimentModal({
  isOpen,
  experimentCode,
  experimentTitle,
  isDeleting,
  error,
  onConfirm,
  onCancel,
}: DeleteExperimentModalProps) {
  const [confirmCode, setConfirmCode] = useState('')

  // Reset input code when modal opens or experiment changes
  useEffect(() => {
    if (isOpen) {
      setConfirmCode('')
    }
  }, [isOpen, experimentCode])

  if (!isOpen) return null

  const isCodeMatched = confirmCode.trim() === experimentCode.trim()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isCodeMatched && !isDeleting) {
      onConfirm()
    }
  }

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-modal-title"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem',
      }}
    >
      <div
        className="modal"
        style={{
          width: '100%',
          maxWidth: '520px',
          background: '#ffffff',
          borderRadius: '8px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          className="modal-header"
          style={{
            padding: '1rem 1.25rem',
            borderBottom: '1px solid var(--color-border, #e5e7eb)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <h2
            id="delete-modal-title"
            className="modal-title"
            style={{
              fontSize: '1.25rem',
              fontWeight: 600,
              color: 'var(--color-danger, #c0392b)',
              margin: 0,
            }}
          >
            Delete Experiment?
          </h2>
          <button
            type="button"
            className="modal-close"
            onClick={onCancel}
            disabled={isDeleting}
            aria-label="Close modal"
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.25rem',
              cursor: isDeleting ? 'not-allowed' : 'pointer',
              color: '#6b7280',
            }}
          >
            ✕
          </button>
        </div>

        {/* Body Form */}
        <form onSubmit={handleSubmit}>
          <div
            className="modal-body"
            style={{
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            {error && <ErrorMessage error={error} />}

            <p style={{ margin: 0, fontWeight: 500, color: 'var(--color-text, #1f2937)' }}>
              Are you sure you want to delete{' '}
              <span className="text-mono" style={{ fontWeight: 700, color: '#111827' }}>
                {experimentCode}
              </span>
              ?
            </p>

            <div
              style={{
                background: 'var(--color-bg, #f9fafb)',
                border: '1px solid var(--color-border, #e5e7eb)',
                borderRadius: '6px',
                padding: '0.75rem 1rem',
                fontSize: '0.9rem',
                color: 'var(--color-text-secondary, #4b5563)',
                fontWeight: 500,
              }}
            >
              {experimentTitle}
            </div>

            {/* Warning Banner */}
            <div
              style={{
                backgroundColor: 'var(--color-danger-bg, #fde8e6)',
                borderLeft: '4px solid var(--color-danger, #c0392b)',
                padding: '0.85rem 1rem',
                borderRadius: '4px',
                color: '#991b1b',
                fontSize: '0.875rem',
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
                ⚠️ Permanent Action Warning
              </div>
              <div>This will permanently delete the experiment and its associated data:</div>
              <ul
                style={{
                  margin: '0.5rem 0 0 1.25rem',
                  padding: 0,
                  fontSize: '0.85rem',
                  lineHeight: '1.5',
                }}
              >
                <li>Experiment information</li>
                <li>Synthesis parameters</li>
                <li>Samples</li>
                <li>Characterization records</li>
                <li>Analysis results</li>
                <li>Uploaded raw files</li>
              </ul>
            </div>

            {/* Double Safety Confirmation Input */}
            <div className="form-group" style={{ marginTop: '0.25rem' }}>
              <label
                htmlFor="confirm-experiment-code"
                className="form-label required"
                style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.35rem', display: 'block' }}
              >
                To confirm, type{' '}
                <span className="text-mono" style={{ background: '#f3f4f6', padding: '1px 4px', borderRadius: '3px' }}>
                  {experimentCode}
                </span>{' '}
                below:
              </label>
              <input
                id="confirm-experiment-code"
                type="text"
                className="form-control text-mono"
                placeholder={`Type ${experimentCode}`}
                value={confirmCode}
                onChange={(e) => setConfirmCode(e.target.value)}
                disabled={isDeleting}
                autoComplete="off"
                required
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  fontSize: '0.9rem',
                  borderRadius: '6px',
                  border: '1px solid var(--color-border, #d1d5db)',
                }}
              />
            </div>
          </div>

          {/* Footer */}
          <div
            className="modal-footer"
            style={{
              padding: '1rem 1.25rem',
              borderTop: '1px solid var(--color-border, #e5e7eb)',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '0.75rem',
              background: '#f9fafb',
            }}
          >
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
              disabled={isDeleting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-danger-filled"
              disabled={!isCodeMatched || isDeleting}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              {isDeleting ? (
                <>
                  <InlineSpinner />
                  <span>Deleting...</span>
                </>
              ) : (
                'Delete Experiment'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
