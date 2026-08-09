/**
 * GreenSynth Analytics — ML Dataset Builder Page
 */

import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Database, Plus, Trash2, CheckCircle2, AlertCircle, ArrowLeft } from 'lucide-react'
import { projectService } from '@/services/projectService'
import type { ProjectSummary } from '@/types'
import { mlService, MLDataset, MLDatasetFeatureSpec, MLDatasetRecord } from '@/services/mlService'

export default function MLDatasetBuilder() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [datasetName, setDatasetName] = useState<string>('CuO Conductivity Dataset')
  const [description, setDescription] = useState<string>('Training dataset for CuO semiconductor conductivity')
  const [targetProperty, setTargetProperty] = useState<string>('Electrical Conductivity')
  const [targetUnit, setTargetUnit] = useState<string>('S/cm')
  const [targetType, setTargetType] = useState<string>('CALCULATED')

  const [features, setFeatures] = useState<MLDatasetFeatureSpec[]>([
    { feature_name: 'substrate_temperature', source_parameter: 'substrate_temperature', unit: '°C', data_type: 'NUMBER' },
    { feature_name: 'spray_rate', source_parameter: 'spray_rate', unit: 'mL/min', data_type: 'NUMBER' },
  ])

  const [building, setBuilding] = useState<boolean>(false)
  const [createdDataset, setCreatedDataset] = useState<MLDataset | null>(null)
  const [datasetRecords, setDatasetRecords] = useState<MLDatasetRecord[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadProjects() {
      try {
        const projs = await projectService.getAll()
        setProjects(projs)
        if (projs.length > 0) {
          setSelectedProject(projs[0].id)
        }
      } catch (err) {
        console.error('Failed to load projects:', err)
      }
    }
    loadProjects()
  }, [])

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
    if (!selectedProject) return
    setBuilding(true)
    setError(null)

    try {
      const ds = await mlService.createDataset({
        project_id: selectedProject,
        name: datasetName,
        description,
        target_property: targetProperty,
        target_type: targetType,
        target_unit: targetUnit,
        features,
      })
      setCreatedDataset(ds)

      const recs = await mlService.getDatasetRecords(ds.id)
      setDatasetRecords(recs)
    } catch (err: any) {
      console.error('Build dataset error:', err)
      setError(err?.message || 'Failed to assemble dataset.')
    } finally {
      setBuilding(false)
    }
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/ml')}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Database className="w-6 h-6 text-teal-400" />
            Dataset Builder Wizard
          </h1>
          <p className="text-slate-400 text-sm">
            Formulate an immutable ML dataset from completed experimental observations.
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          {error}
        </div>
      )}

      {/* Dataset Form */}
      <form onSubmit={handleBuildDataset} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
        <h2 className="text-lg font-semibold text-slate-100 border-b border-slate-800 pb-3">
          1. Target & Project Configuration
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Target Project</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.project_code} — {p.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Dataset Name</label>
            <input
              type="text"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              required
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Target Property</label>
            <input
              type="text"
              value={targetProperty}
              onChange={(e) => setTargetProperty(e.target.value)}
              required
              placeholder="e.g. Electrical Conductivity"
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Target Unit</label>
            <input
              type="text"
              value={targetUnit}
              onChange={(e) => setTargetUnit(e.target.value)}
              required
              placeholder="e.g. S/cm"
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2"
            />
          </div>
        </div>

        <h2 className="text-lg font-semibold text-slate-100 border-b border-slate-800 pb-3 pt-2">
          2. Input Feature Definitions
        </h2>

        <div className="space-y-3">
          {features.map((feat, idx) => (
            <div key={idx} className="flex items-center gap-3 bg-slate-800/40 p-3 rounded-lg border border-slate-700/50">
              <input
                type="text"
                value={feat.feature_name}
                onChange={(e) => handleFeatureChange(idx, 'feature_name', e.target.value)}
                placeholder="Feature Name"
                className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-1.5"
              />
              <input
                type="text"
                value={feat.source_parameter}
                onChange={(e) => handleFeatureChange(idx, 'source_parameter', e.target.value)}
                placeholder="Source Parameter Code"
                className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-1.5"
              />
              <input
                type="text"
                value={feat.unit}
                onChange={(e) => handleFeatureChange(idx, 'unit', e.target.value)}
                placeholder="Unit"
                className="w-24 bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-1.5"
              />
              {features.length > 1 && (
                <button
                  type="button"
                  onClick={() => handleRemoveFeature(idx)}
                  className="text-red-400 hover:text-red-300 p-1.5"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}

          <button
            type="button"
            onClick={handleAddFeature}
            className="flex items-center gap-1.5 text-xs font-semibold text-teal-400 hover:text-teal-300 py-1"
          >
            <Plus className="w-4 h-4" /> Add Input Feature
          </button>
        </div>

        <div className="pt-4 flex justify-end">
          <button
            type="submit"
            disabled={building}
            className="px-6 py-2.5 bg-teal-400 text-slate-900 font-semibold rounded-lg hover:bg-teal-300 transition-colors disabled:opacity-50"
          >
            {building ? 'Assembling Dataset...' : 'Build & Validate Dataset'}
          </button>
        </div>
      </form>

      {/* Dataset Preview */}
      {createdDataset && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                Dataset Created: {createdDataset.name} (v{createdDataset.version})
              </h2>
              <p className="text-sm text-slate-400 mt-1">
                Target: <span className="text-teal-400 font-medium">{createdDataset.target_property}</span> ({createdDataset.target_unit})
              </p>
            </div>
            <button
              onClick={() => navigate('/ml/training')}
              className="px-4 py-2 bg-indigo-500 hover:bg-indigo-400 text-white font-semibold text-sm rounded-lg transition-colors"
            >
              Proceed to Model Training →
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="bg-slate-800/40 p-4 rounded-lg border border-slate-700/50">
              <p className="text-xs font-semibold text-slate-400 uppercase">Eligible Records</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">{createdDataset.eligible_count}</p>
            </div>
            <div className="bg-slate-800/40 p-4 rounded-lg border border-slate-700/50">
              <p className="text-xs font-semibold text-slate-400 uppercase">Excluded Records</p>
              <p className="text-2xl font-bold text-amber-400 mt-1">{createdDataset.excluded_count}</p>
            </div>
            <div className="bg-slate-800/40 p-4 rounded-lg border border-slate-700/50">
              <p className="text-xs font-semibold text-slate-400 uppercase">Dataset Status</p>
              <p className="text-2xl font-bold text-teal-400 mt-1">{createdDataset.status}</p>
            </div>
          </div>

          {/* Record Preview Table */}
          <div>
            <h3 className="text-md font-semibold text-slate-200 mb-3">Record Preview & Eligibility</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800 text-slate-400 uppercase">
                  <tr>
                    <th className="px-3 py-2">Experiment ID</th>
                    <th className="px-3 py-2">Sample ID</th>
                    {features.map((f) => (
                      <th key={f.feature_name} className="px-3 py-2">{f.feature_name}</th>
                    ))}
                    <th className="px-3 py-2">Target ({createdDataset.target_unit})</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Exclusion Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {datasetRecords.map((r) => (
                    <tr key={r.id} className={r.is_eligible ? 'hover:bg-slate-800/30' : 'bg-red-500/5 hover:bg-red-500/10'}>
                      <td className="px-3 py-2 font-mono">{r.experiment_id.substring(0, 8)}...</td>
                      <td className="px-3 py-2 font-mono">{r.sample_id.substring(0, 8)}...</td>
                      {features.map((f) => (
                        <td key={f.feature_name} className="px-3 py-2">
                          {r.feature_values[f.feature_name] ?? 'N/A'}
                        </td>
                      ))}
                      <td className="px-3 py-2 font-semibold text-teal-400">{r.target_value ?? 'N/A'}</td>
                      <td className="px-3 py-2">
                        {r.is_eligible ? (
                          <span className="text-emerald-400 font-semibold">Eligible</span>
                        ) : (
                          <span className="text-red-400 font-semibold">Excluded</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-slate-400">{r.exclusion_reason ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
