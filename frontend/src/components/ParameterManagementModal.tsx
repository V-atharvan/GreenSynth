/**
 * GreenSynth Analytics — Parameter Management Modal
 *
 * Allows researchers to view, add, edit, or deactivate parameter definitions
 * for a research project.
 */

import React, { useState } from 'react'
import { X } from 'lucide-react'
import type {
  ParameterDataType,
  ParameterDefinition,
  ParameterDefinitionCreate,
} from '@/types'
import { parameterService } from '@/services/parameterService'
import { ErrorMessage } from '@/components/ErrorMessage'
import { InlineSpinner } from '@/components/LoadingSpinner'
import type { ApiError } from '@/types'

interface ParameterManagementModalProps {
  projectId: string
  definitions: ParameterDefinition[]
  onClose: () => void
  onUpdated: () => void
}

const EMPTY_DEF: ParameterDefinitionCreate = {
  parameter_name: '',
  parameter_code: '',
  description: '',
  data_type: 'NUMBER',
  unit: '',
  required: false,
  minimum_value: undefined,
  maximum_value: undefined,
  allowed_values: [],
  status: 'ACTIVE',
}

export function ParameterManagementModal({
  projectId,
  definitions,
  onClose,
  onUpdated,
}: ParameterManagementModalProps) {
  const [showAddForm, setShowAddForm] = useState(false)
  const [form, setForm] = useState<ParameterDefinitionCreate>(EMPTY_DEF)
  const [enumInput, setEnumInput] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [deactivatingId, setDeactivatingId] = useState<string | null>(null)

  const handleAddEnumOption = () => {
    if (!enumInput.trim()) return
    const current = form.allowed_values ?? []
    if (!current.includes(enumInput.trim())) {
      setForm({ ...form, allowed_values: [...current, enumInput.trim()] })
    }
    setEnumInput('')
  }

  const handleRemoveEnumOption = (opt: string) => {
    const current = form.allowed_values ?? []
    setForm({ ...form, allowed_values: current.filter((o) => o !== opt) })
  }

  const handleNameChange = (name: string) => {
    // Auto generate parameter_code if user hasn't explicitly customized it
    const code = name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
    setForm((prev) => ({
      ...prev,
      parameter_name: name,
      parameter_code: code,
    }))
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await parameterService.createProjectParameter(projectId, form)
      setShowAddForm(false)
      setForm(EMPTY_DEF)
      onUpdated()
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Failed to add parameter definition.')
    } finally {
      setSaving(false)
    }
  }

  const handleDeactivate = async (paramId: string) => {
    setDeactivatingId(paramId)
    setError(null)
    try {
      await parameterService.deactivateProjectParameter(projectId, paramId)
      onUpdated()
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Failed to deactivate parameter.')
    } finally {
      setDeactivatingId(null)
    }
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="param-mgmt-title">
      <div className="modal" style={{ maxWidth: 680 }}>
        <div className="modal-header">
          <h2 className="modal-title" id="param-mgmt-title">
            Manage Synthesis Parameter Definitions
          </h2>
          <button className="modal-close" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>

        <div className="modal-body">
          {error && <ErrorMessage error={error} />}

          {!showAddForm ? (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                  Definitions specify required fields, data types, units, and ranges for experiments in this project.
                </p>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => setShowAddForm(true)}
                >
                  + Add Parameter Definition
                </button>
              </div>

              <div className="table-container" style={{ maxHeight: 360, overflowY: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Name / Code</th>
                      <th>Type</th>
                      <th>Unit</th>
                      <th>Required</th>
                      <th>Range / Options</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {definitions.map((d) => (
                      <tr key={d.id} style={{ opacity: d.status === 'INACTIVE' ? 0.5 : 1 }}>
                        <td>
                          <div style={{ fontWeight: 600 }}>{d.parameter_name}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }} className="text-mono">
                            {d.parameter_code}
                          </div>
                        </td>
                        <td>
                          <span className="badge badge-planned" style={{ fontSize: '0.65rem' }}>
                            {d.data_type}
                          </span>
                        </td>
                        <td>{d.unit ?? '—'}</td>
                        <td>
                          {d.required ? (
                            <span style={{ color: 'var(--color-danger)', fontWeight: 600 }}>Yes</span>
                          ) : (
                            <span style={{ color: 'var(--color-text-secondary)' }}>No</span>
                          )}
                        </td>
                        <td style={{ fontSize: '0.75rem' }}>
                          {d.data_type === 'NUMBER' && (d.minimum_value !== null || d.maximum_value !== null)
                            ? `${d.minimum_value ?? '—'} to ${d.maximum_value ?? '—'}`
                            : d.data_type === 'ENUM' && d.allowed_values
                            ? d.allowed_values.join(', ')
                            : '—'}
                        </td>
                        <td>
                          <span className={`badge ${d.status === 'ACTIVE' ? 'badge-active' : 'badge-archived'}`}>
                            {d.status}
                          </span>
                        </td>
                        <td>
                          {d.status === 'ACTIVE' && (
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => handleDeactivate(d.id)}
                              disabled={deactivatingId === d.id}
                            >
                              {deactivatingId === d.id ? <InlineSpinner /> : 'Deactivate'}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <form onSubmit={handleCreate}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 12 }}>
                New Synthesis Parameter Definition
              </h3>

              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label required">Parameter Name</label>
                  <input
                    className="form-control"
                    placeholder="e.g. Substrate Temperature"
                    value={form.parameter_name}
                    onChange={(e) => handleNameChange(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label required">Parameter Code</label>
                  <input
                    className="form-control text-mono"
                    placeholder="e.g. substrate_temperature_c"
                    value={form.parameter_code}
                    onChange={(e) => setForm({ ...form, parameter_code: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label required">Data Type</label>
                  <select
                    className="form-control"
                    value={form.data_type}
                    onChange={(e) => setForm({ ...form, data_type: e.target.value as ParameterDataType })}
                  >
                    <option value="NUMBER">NUMBER (Numeric)</option>
                    <option value="TEXT">TEXT (Free text)</option>
                    <option value="BOOLEAN">BOOLEAN (Yes/No)</option>
                    <option value="ENUM">ENUM (Dropdown list)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Unit (where applicable)</label>
                  <input
                    className="form-control"
                    placeholder="e.g. °C, mL/min, mol/L"
                    value={form.unit ?? ''}
                    onChange={(e) => setForm({ ...form, unit: e.target.value })}
                  />
                </div>

                {form.data_type === 'NUMBER' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Minimum Allowed Value</label>
                      <input
                        type="number"
                        step="any"
                        className="form-control"
                        placeholder="Optional min limit"
                        value={form.minimum_value ?? ''}
                        onChange={(e) =>
                          setForm({
                            ...form,
                            minimum_value: e.target.value ? parseFloat(e.target.value) : undefined,
                          })
                        }
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Maximum Allowed Value</label>
                      <input
                        type="number"
                        step="any"
                        className="form-control"
                        placeholder="Optional max limit"
                        value={form.maximum_value ?? ''}
                        onChange={(e) =>
                          setForm({
                            ...form,
                            maximum_value: e.target.value ? parseFloat(e.target.value) : undefined,
                          })
                        }
                      />
                    </div>
                  </>
                )}

                {form.data_type === 'ENUM' && (
                  <div className="form-group span-2">
                    <label className="form-label required">Allowed Options (Dropdown items)</label>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                      <input
                        className="form-control"
                        placeholder="Type option and click Add"
                        value={enumInput}
                        onChange={(e) => setEnumInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault()
                            handleAddEnumOption()
                          }
                        }}
                      />
                      <button type="button" className="btn btn-secondary" onClick={handleAddEnumOption}>
                        Add Option
                      </button>
                    </div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {(form.allowed_values ?? []).map((opt) => (
                        <span
                          key={opt}
                          className="badge badge-planned"
                          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 8px' }}
                        >
                          {opt}
                          <button
                            type="button"
                            onClick={() => handleRemoveEnumOption(opt)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'red', display: 'inline-flex', alignItems: 'center' }}
                          >
                            <X size={12} />
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="form-group span-2" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                  <input
                    type="checkbox"
                    id="is-required"
                    checked={form.required}
                    onChange={(e) => setForm({ ...form, required: e.target.checked })}
                  />
                  <label htmlFor="is-required" style={{ fontWeight: 600, cursor: 'pointer' }}>
                    Required Parameter (Must be recorded for every experiment in this project)
                  </label>
                </div>

                <div className="form-group span-2">
                  <label className="form-label">Description / Instructions for Researcher</label>
                  <textarea
                    className="form-control"
                    rows={2}
                    placeholder="Instructions on how to measure or set this parameter"
                    value={form.description ?? ''}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 16 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowAddForm(false)}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? <InlineSpinner /> : 'Save Parameter Definition'}
                </button>
              </div>
            </form>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
