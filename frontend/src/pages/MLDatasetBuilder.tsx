/**
 * GreenSynth Analytics — ML Dataset Builder Page
 */

import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Database, Plus, Trash2, CheckCircle2, AlertCircle, ArrowLeft, FolderKanban } from 'lucide-react'
import { parameterService } from '@/services/parameterService'
import { mlService, MLDataset, MLDatasetFeatureSpec, MLDatasetRecord } from '@/services/mlService'
import { useProjectContext } from '@/context/ProjectContext'

export default function MLDatasetBuilder() {
  const navigate = useNavigate()
  const { projectId, projectCode, projectName } = useProjectContext()
  const [datasetName, setDatasetName] = useState<string>('Synthesis Conductivity Dataset')
  const [description, setDescription] = useState<string>('Training dataset for semiconductor conductivity prediction')
  const [targetProperty, setTargetProperty] = useState<string>('Electrical Conductivity')
  const [targetUnit, setTargetUnit] = useState<string>('S/cm')
  const [targetType, setTargetType] = useState<string>('CALCULATED')

  const [features, setFeatures] = useState<MLDatasetFeatureSpec[]>([
    { feature_name: 'precursor_concentration', source_parameter: 'precursor_concentration', unit: 'mol/L', data_type: 'NUMBER' },
    { feature_name: 'substrate_temperature_c', source_parameter: 'substrate_temperature_c', unit: '°C', data_type: 'NUMBER' },
    { feature_name: 'spray_rate_ml_min', source_parameter: 'spray_rate_ml_min', unit: 'mL/min', data_type: 'NUMBER' },
    { feature_name: 'spray_duration_min', source_parameter: 'spray_duration_min', unit: 'min', data_type: 'NUMBER' },
  ])

  const [building, setBuilding] = useState<boolean>(false)
  const [createdDataset, setCreatedDataset] = useState<MLDataset | null>(null)
  const [datasetRecords, setDatasetRecords] = useState<MLDatasetRecord[]>([])
  const [error, setError] = useState<string | null>(null)

  const syncProjectFeatures = useCallback(async () => {
    if (!projectId) return
    try {
      const defs = await parameterService.getProjectParameters(projectId)
      const numDefs = defs.filter((d) => d.data_type === 'NUMBER')
      if (numDefs.length > 0) {
        setFeatures(
          numDefs.map((d) => ({
            feature_name: d.parameter_code,
            source_parameter: d.parameter_code,
            unit: d.unit ?? '',
            data_type: 'NUMBER',
          }))
        )
      }
    } catch (err) {
      console.error('Failed to sync project parameter features:', err)
    }
  }, [projectId])

  useEffect(() => {
    syncProjectFeatures()
  }, [syncProjectFeatures])

  const handleAddFeature = () => {
    setFeatures([
      ...features,
      { feature_name: `feature_${features.length + 1}`, source_parameter: `param_${features.length + 1}`, unit: 'a.u.', data_type: 'NUMBER' },
    ])
  }

  const handleRemoveFeature = (index: number) => {
    setFeatures(features.filter((_, i) => i !== index))
  }

  const handleFeatureChange = (index: number, field: keyof MLDatasetFeatureSpec, value: string) => {
    const updated = [...features]
    updated[index] = { ...updated[index], [field]: value }
    setFeatures(updated)
  }

  const handleBuildDataset = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectId) {
      setError('Assigned project context is missing. Please ensure your research group is active.')
      return
    }

    if (features.length === 0) {
      setError('At least one numeric feature must be included in the dataset.')
      return
    }

    setBuilding(true)
    setError(null)
    setCreatedDataset(null)

    try {
      const dataset = await mlService.createDataset({
        project_id: projectId,
        name: datasetName,
        description,
        target_property: targetProperty,
        target_type: targetType,
        target_unit: targetUnit,
        features,
      })

      setCreatedDataset(dataset)
      const records = await mlService.getDatasetRecords(dataset.id)
      setDatasetRecords(records)
    } catch (err: any) {
      setError(err?.message || 'Failed to construct dataset. Ensure eligible experiments exist.')
    } finally {
      setBuilding(false)
    }
  }

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            onClick={() => navigate('/ml')}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 36,
              height: 36,
              borderRadius: '50%',
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              cursor: 'pointer',
            }}
          >
            <ArrowLeft className="w-5 h-5 text-slate-600" />
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Database className="w-6 h-6 text-emerald-600" style={{ color: '#0f766e' }} />
              <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0, color: '#1e3a5f' }}>
                Multi-Modal ML Dataset Builder
              </h1>
            </div>
            <p style={{ color: '#64748b', fontSize: '0.875rem', margin: '4px 0 0 0' }}>
              Assemble synthesis parameter vectors and characterization target measurements for model training.
            </p>
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 14px',
            background: '#f8fafc',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 600,
            color: '#0f766e',
          }}
        >
          <FolderKanban size={15} />
          <span>{projectCode ? `${projectCode} — ${projectName || projectCode}` : 'Loading project...'}</span>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px', background: '#fee2e2', borderRadius: '8px', color: '#991b1b' }}>
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Dataset Form Card */}
      <form onSubmit={handleBuildDataset} className="card" style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
        <div className="card-header" style={{ marginBottom: '16px' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#1e3a5f', margin: 0 }}>1. Target &amp; Project Configuration</h2>
        </div>

        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
            <div className="form-group">
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>Assigned Project</label>
              <div
                style={{
                  padding: '10px 12px',
                  background: '#f1f5f9',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: 600,
                  color: '#0f766e',
                }}
              >
                {projectCode ? `${projectCode} — ${projectName || projectCode}` : 'Resolving project...'}
              </div>
            </div>

            <div className="form-group">
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>Dataset Name</label>
              <input
                type="text"
                value={datasetName}
                onChange={(e) => setDatasetName(e.target.value)}
                required
                style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
              />
            </div>

            <div className="form-group">
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>Target Property</label>
              <input
                type="text"
                value={targetProperty}
                onChange={(e) => setTargetProperty(e.target.value)}
                required
                style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
              />
            </div>

            <div className="form-group">
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>Target Unit</label>
              <input
                type="text"
                value={targetUnit}
                onChange={(e) => setTargetUnit(e.target.value)}
                required
                style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
            />
          </div>

          {/* Features Table */}
          <div style={{ marginTop: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#1e3a5f', margin: 0 }}>2. Parameter Feature Schema ({features.length} Features)</h3>
              <button
                type="button"
                onClick={handleAddFeature}
                style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#f8fafc', border: '1px solid #cbd5e1', padding: '6px 12px', borderRadius: '6px', fontSize: '13px', cursor: 'pointer' }}
              >
                <Plus className="w-4 h-4" /> Add Custom Feature
              </button>
            </div>

            <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                  <tr>
                    <th style={{ padding: '10px 12px', textAlign: 'left' }}>Feature Code</th>
                    <th style={{ padding: '10px 12px', textAlign: 'left' }}>Source Parameter</th>
                    <th style={{ padding: '10px 12px', textAlign: 'left' }}>Unit</th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', width: '60px' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {features.map((feat, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '8px 12px' }}>
                        <input
                          type="text"
                          value={feat.feature_name}
                          onChange={(e) => handleFeatureChange(idx, 'feature_name', e.target.value)}
                          style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                        />
                      </td>
                      <td style={{ padding: '8px 12px' }}>
                        <input
                          type="text"
                          value={feat.source_parameter}
                          onChange={(e) => handleFeatureChange(idx, 'source_parameter', e.target.value)}
                          style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                        />
                      </td>
                      <td style={{ padding: '8px 12px' }}>
                        <input
                          type="text"
                          value={feat.unit}
                          onChange={(e) => handleFeatureChange(idx, 'unit', e.target.value)}
                          style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '13px' }}
                        />
                      </td>
                      <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                        <button
                          type="button"
                          onClick={() => handleRemoveFeature(idx)}
                          style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '4px' }}
                          title="Remove feature"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
            <button
              type="submit"
              disabled={building || !projectId}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 24px',
                background: '#0f766e',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: building || !projectId ? 'not-allowed' : 'pointer',
                opacity: building || !projectId ? 0.7 : 1,
              }}
            >
              <Database className="w-4 h-4" />
              <span>{building ? 'Constructing Feature Vectors...' : 'Build ML Dataset'}</span>
            </button>
          </div>
        </div>
      </form>

      {/* Dataset Success View */}
      {createdDataset && (
        <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '12px', padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#16a34a', marginBottom: '12px' }}>
            <CheckCircle2 className="w-6 h-6" />
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>Dataset Constructed Successfully</h3>
          </div>
          <p style={{ color: '#334155', fontSize: '14px', margin: '0 0 16px 0' }}>
            <strong>{createdDataset.name}</strong> (v{createdDataset.version}) assembled with <strong>{createdDataset.eligible_count}</strong> eligible training records ({createdDataset.excluded_count} excluded due to quality/completeness criteria).
          </p>

          <button
            onClick={() => navigate('/ml/training')}
            style={{
              padding: '10px 20px',
              background: '#0f766e',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Proceed to Model Training &rarr;
          </button>
        </div>
      )}
    </div>
  )
}
