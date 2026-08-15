/**
 * GreenSynth Analytics — Error Message Component
 */

import React from 'react'
import { AlertTriangle } from 'lucide-react'
import type { ApiError } from '@/types'

interface ErrorMessageProps {
  error: ApiError | string | null | undefined
  onRetry?: () => void
}

export function ErrorMessage({ error, onRetry }: ErrorMessageProps) {
  if (!error) return null

  const message = typeof error === 'string'
    ? error
    : error.message

  return (
    <div className="alert alert-error" role="alert">
      <AlertTriangle size={18} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} />
      <div style={{ flex: 1 }}>
        <strong>Error: </strong>{message}
        {onRetry && (
          <button
            className="btn btn-sm btn-secondary"
            onClick={onRetry}
            style={{ marginLeft: 12, marginTop: 4 }}
          >
            Retry
          </button>
        )}
      </div>
    </div>
  )
}
