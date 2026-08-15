/**
 * GreenSynth Analytics — Confirm Modal Component
 */

import React from 'react'
import { X } from 'lucide-react'
import { InlineSpinner } from './LoadingSpinner'

interface ConfirmModalProps {
  isOpen: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'primary'
  isLoading?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmModal({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  isLoading = false,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  if (!isOpen) return null

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
      <div className="modal" style={{ maxWidth: 440 }}>
        <div className="modal-header">
          <h2 className="modal-title" id="confirm-title">{title}</h2>
          <button className="modal-close" onClick={onCancel} aria-label="Close dialog"><X size={18} /></button>
        </div>
        <div className="modal-body">
          <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>{message}</p>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onCancel} disabled={isLoading}>
            {cancelLabel}
          </button>
          <button
            className={`btn btn-${variant}`}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? <InlineSpinner /> : null}
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
