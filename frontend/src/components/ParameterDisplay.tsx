/**
 * GreenSynth Analytics — Parameter Display Component
 *
 * Renders a clean table of recorded synthesis parameters for an experiment.
 */

import React from 'react'
import type { ExperimentParameter } from '@/types'
import { getDynamicParameterLabel } from '@/config/methodConfig'

interface ParameterDisplayProps {
  parameters: ExperimentParameter[]
  onEdit?: () => void
  projectCode?: string
}

export function ParameterDisplay({ parameters, onEdit, projectCode }: ParameterDisplayProps) {
  if (parameters.length === 0) {
    return (
      <div style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        <p style={{ marginBottom: 12 }}>No synthesis parameters recorded for this experiment yet.</p>
        {onEdit && (
          <button className="btn btn-primary btn-sm" onClick={onEdit}>
            + Record Parameters
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Parameter Name</th>
            <th>Recorded Value</th>
            <th>Unit</th>
            <th>Data Type / Constraints</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {parameters.map((param) => {
            const def = param.parameter_definition
            const hasValue = param.value !== null && param.value.trim() !== ''
            const displayLabel = getDynamicParameterLabel(def.parameter_code, projectCode) || def.parameter_name

            return (
              <tr key={param.id}>
                <td style={{ fontWeight: 600 }}>
                  {displayLabel}
                  {def.required && <span style={{ color: 'var(--color-danger)', marginLeft: 4 }}>*</span>}
                </td>
                <td className="text-mono" style={{
                  fontWeight: hasValue ? 600 : 400,
                  color: hasValue ? 'var(--color-text)' : 'var(--color-text-muted)',
                }}>
                  {hasValue ? param.value : '—'}
                </td>
                <td style={{ color: 'var(--color-text-secondary)' }}>
                  {param.unit ?? def.unit ?? '—'}
                </td>
                <td style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                  <span className="badge badge-planned" style={{ fontSize: '0.65rem', marginRight: 6 }}>
                    {def.data_type}
                  </span>
                  {def.data_type === 'NUMBER' && (def.minimum_value !== null || def.maximum_value !== null) && (
                    <span>[{def.minimum_value ?? '—'} to {def.maximum_value ?? '—'}]</span>
                  )}
                  {def.data_type === 'ENUM' && def.allowed_values && (
                    <span>({def.allowed_values.join(', ')})</span>
                  )}
                </td>
                <td style={{ color: 'var(--color-text-secondary)' }}>
                  {param.notes ?? '—'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
