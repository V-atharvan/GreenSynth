/**
 * GreenSynth Analytics — Loading Spinner Component
 */

import React from 'react'

interface LoadingSpinnerProps {
  message?: string
  size?: 'sm' | 'md' | 'lg'
}

export function LoadingSpinner({ message = 'Loading…', size = 'md' }: LoadingSpinnerProps) {
  const spinnerSize = size === 'sm' ? 16 : size === 'lg' ? 36 : 24
  return (
    <div className="loading-container" role="status" aria-live="polite">
      <div
        className="spinner"
        style={{ width: spinnerSize, height: spinnerSize }}
        aria-hidden="true"
      />
      {message && <span>{message}</span>}
    </div>
  )
}

/**
 * Inline loading indicator for buttons and small areas.
 */
export function InlineSpinner() {
  return (
    <div
      className="spinner"
      style={{ width: 16, height: 16, borderWidth: 1.5 }}
      role="status"
      aria-label="Loading"
    />
  )
}
