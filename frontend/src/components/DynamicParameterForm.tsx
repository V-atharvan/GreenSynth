/**
 * GreenSynth Analytics — Dynamic Parameter Form Component
 *
 * Dynamically generates form input fields from a project's ParameterDefinition[].
 * Does NOT hard-code parameter names in React code.
 * Displays units, required badges, range hints, and allowed ENUM dropdowns.
 */

import React from 'react'
import type { ExperimentParameterCreate, ParameterDefinition } from '@/types'

interface DynamicParameterFormProps {
  definitions: ParameterDefinition[]
  values: Record<string, { value: string; notes?: string }>
  onChange: (paramDefId: string, value: string, notes?: string) => void
  disabled?: boolean
}

const SECTION_MAP: Record<string, { title: string; icon: string }> = {
  copper_precursor_salt: { title: 'A. Precursor & Extract', icon: '🧪' },
  copper_precursor: { title: 'A. Precursor & Extract', icon: '🧪' },
  precursor_concentration: { title: 'A. Precursor & Extract', icon: '🧪' },
  precursor_solution_volume: { title: 'A. Precursor & Extract', icon: '🧪' },
  precursor_volume: { title: 'A. Precursor & Extract', icon: '🧪' },
  mulberry_extract_concentration: { title: 'A. Precursor & Extract', icon: '🧪' },
  extract_concentration: { title: 'A. Precursor & Extract', icon: '🧪' },
  mulberry_extract_volume: { title: 'A. Precursor & Extract', icon: '🧪' },
  extract_volume: { title: 'A. Precursor & Extract', icon: '🧪' },
  biomass_source_mass_g: { title: 'A. Precursor & Extract', icon: '🧪' },

  ethanol_volume: { title: 'B. Solvent', icon: '💧' },
  solvent_volume: { title: 'B. Solvent', icon: '💧' },
  pretreatment_acid_concentration: { title: 'B. Solvent', icon: '💧' },

  substrate_type: { title: 'C. Deposition Conditions', icon: '🔥' },
  substrate_temperature_c: { title: 'C. Deposition Conditions', icon: '🔥' },
  substrate_temperature: { title: 'C. Deposition Conditions', icon: '🔥' },
  spray_duration_min: { title: 'C. Deposition Conditions', icon: '🔥' },
  nozzle_substrate_distance_cm: { title: 'C. Deposition Conditions', icon: '🔥' },
  sol_gel_aging_temperature_c: { title: 'C. Deposition Conditions', icon: '🔥' },
  sol_gel_aging_time_h: { title: 'C. Deposition Conditions', icon: '🔥' },
  hydrothermal_temperature_c: { title: 'C. Deposition Conditions', icon: '🔥' },
  hydrothermal_reaction_time_h: { title: 'C. Deposition Conditions', icon: '🔥' },
  autoclave_fill_factor_pct: { title: 'C. Deposition Conditions', icon: '🔥' },
  calcination_temperature_c: { title: 'C. Deposition Conditions', icon: '🔥' },
  calcination_duration_h: { title: 'C. Deposition Conditions', icon: '🔥' },

  spray_rate_ml_min: { title: 'D. Spray System', icon: '⚙️' },
  spray_rate: { title: 'D. Spray System', icon: '⚙️' },
  carrier_gas_pressure_kpa: { title: 'D. Spray System', icon: '⚙️' },
  spray_cycles: { title: 'D. Spray System', icon: '⚙️' },

  ambient_temperature_c: { title: 'E. Ambient Conditions', icon: '🌡️' },
  ambient_relative_humidity: { title: 'E. Ambient Conditions', icon: '🌡️' },
}

export function DynamicParameterForm({
  definitions,
  values,
  onChange,
  disabled = false,
}: DynamicParameterFormProps) {
  if (definitions.length === 0) {
    return (
      <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', fontStyle: 'italic' }}>
        No parameter definitions configured for this project.
      </div>
    )
  }

  // Group definitions by section
  const grouped: Record<string, { icon: string; items: ParameterDefinition[] }> = {}
  definitions.forEach((pdef) => {
    const sec = SECTION_MAP[pdef.parameter_code] ?? { title: 'General Parameters', icon: '🔬' }
    if (!grouped[sec.title]) {
      grouped[sec.title] = { icon: sec.icon, items: [] }
    }
    grouped[sec.title].items.push(pdef)
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {Object.entries(grouped).map(([sectionTitle, section]) => (
        <div
          key={sectionTitle}
          style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem 1.25rem',
          }}
        >
          <h4
            style={{
              margin: '0 0 0.875rem 0',
              fontSize: '0.875rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              color: 'var(--color-primary)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <span>{section.icon}</span>
            <span>{sectionTitle}</span>
          </h4>

          <div className="form-grid">
            {section.items.map((pdef) => {
              const current = values[pdef.id] ?? { value: '' }
              const fieldId = `param-${pdef.id}`

              return (
                <div
                  key={pdef.id}
                  className="form-group span-2"
                  style={{
                    background: 'var(--color-bg)',
                    padding: 'var(--space-3) var(--space-4)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--color-border-light)',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'baseline',
                      marginBottom: 4,
                    }}
                  >
                    <label
                      className={`form-label ${pdef.required ? 'required' : ''}`}
                      htmlFor={fieldId}
                      style={{ fontWeight: 600 }}
                    >
                      {pdef.parameter_name}
                    </label>

                    {pdef.unit && (
                      <span className="badge badge-planned" style={{ fontSize: '0.7rem' }}>
                        Unit: {pdef.unit}
                      </span>
                    )}
                  </div>

                  {/* Input field based on data_type */}
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {pdef.data_type === 'ENUM' && pdef.allowed_values ? (
                      <select
                        id={fieldId}
                        className="form-control"
                        value={current.value}
                        onChange={(e) => onChange(pdef.id, e.target.value, current.notes)}
                        disabled={disabled}
                        required={pdef.required}
                      >
                        <option value="">— Select {pdef.parameter_name} —</option>
                        {pdef.allowed_values.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    ) : pdef.data_type === 'BOOLEAN' ? (
                      <select
                        id={fieldId}
                        className="form-control"
                        value={current.value}
                        onChange={(e) => onChange(pdef.id, e.target.value, current.notes)}
                        disabled={disabled}
                        required={pdef.required}
                      >
                        <option value="">— Select —</option>
                        <option value="true">True / Yes</option>
                        <option value="false">False / No</option>
                      </select>
                    ) : (
                      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 6 }}>
                        <input
                          id={fieldId}
                          type={pdef.data_type === 'NUMBER' ? 'number' : 'text'}
                          step={pdef.data_type === 'NUMBER' ? 'any' : undefined}
                          className="form-control"
                          placeholder={
                            pdef.data_type === 'NUMBER'
                              ? `Enter numeric value${pdef.unit ? ` in ${pdef.unit}` : ''}`
                              : `Enter text value`
                          }
                          value={current.value}
                          onChange={(e) => onChange(pdef.id, e.target.value, current.notes)}
                          disabled={disabled}
                          required={pdef.required}
                          min={pdef.minimum_value ?? undefined}
                          max={pdef.maximum_value ?? undefined}
                        />
                        {pdef.unit && (
                          <span
                            style={{
                              fontSize: '0.8125rem',
                              fontWeight: 600,
                              color: 'var(--color-text-secondary)',
                              minWidth: 40,
                            }}
                          >
                            {pdef.unit}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Description & Range Hint */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginTop: 4,
                      flexWrap: 'wrap',
                      gap: 4,
                    }}
                  >
                    {pdef.description && (
                      <span className="form-hint" style={{ fontSize: '0.75rem' }}>
                        {pdef.description}
                      </span>
                    )}
                    {pdef.data_type === 'NUMBER' &&
                      (pdef.minimum_value !== null || pdef.maximum_value !== null) && (
                        <span
                          className="form-hint"
                          style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--color-info)' }}
                        >
                          Range: {pdef.minimum_value ?? '—'} to {pdef.maximum_value ?? '—'}{' '}
                          {pdef.unit ?? ''}
                        </span>
                      )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
