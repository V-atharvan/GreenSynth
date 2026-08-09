/**
 * GreenSynth Analytics — Sample Comparison & Statistical Analysis Page
 *
 * Provides:
 *  1. Dataset selector & version badge
 *  2. Data Quality Banner (missing variables, unit consistency)
 *  3. Multi-Sample Comparison Table with provenance badges (MEASURED, CALCULATED, MISSING)
 *  4. Descriptive Statistics Cards (n, mean, median, std_dev, min, max)
 *  5. Statistical Analysis Engine (Correlation, Linear Regression, Group Comparison, Outlier Report)
 *  6. Scatter plot & trend line visualizer
 *  7. Export to CSV button
 */

import React, { useEffect, useState } from 'react'
import type {
  ComparisonTableResponse,
  CorrelationResponse,
  DatasetResponse,
  DescriptiveStatsItem,
  GroupComparisonResponse,
  OutlierReportResponse,
  ProjectSummary,
  RegressionResponse,
  StatisticalAnalysisResponse,
} from '@/types'
import { projectService } from '@/services/projectService'
import { analysisService } from '@/services/analysisService'
import { ErrorMessage } from '@/components/ErrorMessage'
import { InlineSpinner, LoadingSpinner } from '@/components/LoadingSpinner'
import { DatasetBuilderModal } from '@/components/DatasetBuilderModal'
import { ComparisonPlotChart } from '@/components/ComparisonPlotChart'
import type { ApiError } from '@/types'

export function SampleComparison() {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProjId, setSelectedProjId] = useState<string>('')
  const [datasets, setDatasets] = useState<DatasetResponse[]>([])
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('')

  const [tableData, setTableData] = useState<ComparisonTableResponse | null>(null)
  const [descStats, setDescStats] = useState<DescriptiveStatsItem[]>([])
  const [statResult, setStatResult] = useState<StatisticalAnalysisResponse | null>(null)

  // Analysis Control Form State
  const [analysisType, setAnalysisType] = useState<string>('REGRESSION')
  const [xVar, setXVar] = useState<string>('')
  const [yVar, setYVar] = useState<string>('')
  const [groupVar, setGroupVar] = useState<string>('solvent')

  const [loading, setLoading] = useState(true)
  const [loadingTable, setLoadingTable] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [showBuilderModal, setShowBuilderModal] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load Projects
  useEffect(() => {
    projectService.getAll()
      .then((projs: ProjectSummary[]) => {
        setProjects(projs)
        if (projs.length > 0) {
          setSelectedProjId(projs[0].id)
        }
      })
      .catch((err: unknown) => setError((err as ApiError)?.message ?? 'Failed to load projects.'))
      .finally(() => setLoading(false))
  }, [])

  // Load Datasets when project changes
  useEffect(() => {
    if (!selectedProjId) return
    analysisService.listDatasets(selectedProjId)
      .then((dsList) => {
        setDatasets(dsList)
        if (dsList.length > 0) {
          setSelectedDatasetId(dsList[0].id)
        } else {
          setSelectedDatasetId('')
          setTableData(null)
          setDescStats([])
        }
      })
      .catch((err: unknown) => setError((err as ApiError)?.message ?? 'Failed to load datasets.'))
  }, [selectedProjId])

  // Load Comparison Table & Auto Run Descriptive Stats when dataset changes
  const loadDatasetDetails = async (dsId: string) => {
    if (!dsId) return
    setLoadingTable(true)
    setError(null)
    try {
      const tbl = await analysisService.getComparisonTable(dsId)
      setTableData(tbl)
      if (tbl.variables.length >= 2) {
        setXVar(tbl.variables[0])
        setYVar(tbl.variables[1])
      } else if (tbl.variables.length === 1) {
        setXVar(tbl.variables[0])
        setYVar(tbl.variables[0])
      }

      // Run Descriptive Stats by default
      const descRes = await analysisService.runStatisticalAnalysis(dsId, { analysis_type: 'DESCRIPTIVE' })
      if (descRes.results_json && Array.isArray((descRes.results_json as any).descriptive_statistics)) {
        setDescStats((descRes.results_json as any).descriptive_statistics)
      }
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Failed to load dataset details.')
    } finally {
      setLoadingTable(false)
    }
  }

  useEffect(() => {
    if (selectedDatasetId) {
      loadDatasetDetails(selectedDatasetId)
    }
  }, [selectedDatasetId])

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedDatasetId) return
    setError(null)
    setAnalyzing(true)
    try {
      const res = await analysisService.runStatisticalAnalysis(selectedDatasetId, {
        analysis_type: analysisType,
        x_variable: xVar || undefined,
        y_variable: yVar || undefined,
        group_variable: groupVar || undefined,
      })
      setStatResult(res)
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'Statistical analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleExportCsv = async () => {
    if (!selectedDatasetId) return
    try {
      const blob = await analysisService.exportDatasetCsv(selectedDatasetId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `dataset_${selectedDatasetId}.csv`
      document.body.appendChild(a)
      a.click()
      a.remove()
    } catch (err: unknown) {
      setError((err as ApiError)?.message ?? 'CSV export failed.')
    }
  }

  // Build Scatter plot paired points
  const scatterPoints = (tableData && xVar && yVar)
    ? tableData.rows
        .filter(
          (r) =>
            r.cells[xVar]?.value !== undefined &&
            r.cells[xVar]?.value !== null &&
            r.cells[yVar]?.value !== undefined &&
            r.cells[yVar]?.value !== null &&
            typeof r.cells[xVar].value === 'number' &&
            typeof r.cells[yVar].value === 'number'
        )
        .map((r) => ({
          sampleCode: r.sample_code,
          x: Number(r.cells[xVar].value),
          y: Number(r.cells[yVar].value),
        }))
    : []

  const regressionData = (statResult && statResult.analysis_type === 'REGRESSION' && statResult.results_json)
    ? {
        slope: Number((statResult.results_json as any).slope ?? 0),
        intercept: Number((statResult.results_json as any).intercept ?? 0),
        rSquared: Number((statResult.results_json as any).r_squared ?? (statResult.results_json as any).rSquared ?? 0),
        formula: String((statResult.results_json as any).formula ?? ''),
      }
    : null

  return (
    <div style={{ padding: '24px 32px', maxWidth: 1280, margin: '0 auto' }}>
      {/* Header & Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--color-heading)', margin: 0 }}>
            📊 Sample Comparison & Statistical Analysis
          </h1>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', marginTop: 4 }}>
            Multi-sample dataset evaluation, synthesis parameter correlations, linear regression fits, and descriptive statistics.
          </p>
        </div>

        <button className="btn btn-primary" onClick={() => setShowBuilderModal(true)}>
          + Create Comparison Dataset
        </button>
      </div>

      {error && <ErrorMessage error={error} />}

      {/* Selectors Bar */}
      <div style={{
        background: 'white',
        padding: '14px 20px',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        marginBottom: 20,
      }}>
        <div>
          <label className="form-label" style={{ fontSize: '0.75rem', marginBottom: 2 }}>Project</label>
          <select
            className="form-control"
            style={{ width: 'auto', fontSize: '0.875rem' }}
            value={selectedProjId}
            onChange={(e) => setSelectedProjId(e.target.value)}
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.project_code} — {p.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="form-label" style={{ fontSize: '0.75rem', marginBottom: 2 }}>Comparison Dataset</label>
          <select
            className="form-control"
            style={{ width: 'auto', fontSize: '0.875rem', minWidth: 260 }}
            value={selectedDatasetId}
            onChange={(e) => setSelectedDatasetId(e.target.value)}
          >
            {datasets.length === 0 ? (
              <option value="">No datasets created yet</option>
            ) : (
              datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.version}) — {d.sample_ids.length} samples
                </option>
              ))
            )}
          </select>
        </div>

        {selectedDatasetId && (
          <button className="btn btn-secondary btn-sm" onClick={handleExportCsv} style={{ marginLeft: 'auto' }}>
            📥 Export Dataset CSV
          </button>
        )}
      </div>

      {/* Loading state */}
      {loadingTable ? (
        <LoadingSpinner message="Loading multi-sample comparison table..." />
      ) : tableData ? (
        <div>
          {/* Data Quality Banner */}
          {tableData.quality_report.warnings.length > 0 && (
            <div style={{
              background: '#fffbeb',
              borderLeft: '4px solid #f59e0b',
              padding: '10px 16px',
              borderRadius: 6,
              fontSize: '0.8125rem',
              color: '#92400e',
              marginBottom: 16,
            }}>
              ⚠️ <strong>Data Quality Report ({tableData.quality_report.status}):</strong>
              <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                {tableData.quality_report.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Multi-Sample Comparison Table */}
          <div style={{ background: 'white', borderRadius: 8, padding: 16, border: '1px solid var(--color-border)', marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                📋 Multi-Sample Comparison Table ({tableData.total_samples} Samples)
              </h3>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                Provenance: <span style={{ color: '#047857', fontWeight: 600 }}>MEASURED</span> · <span style={{ color: '#2563eb', fontWeight: 600 }}>CALCULATED</span> · <span style={{ color: '#dc2626', fontWeight: 600 }}>MISSING</span>
              </div>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table className="table" style={{ fontSize: '0.8125rem' }}>
                <thead>
                  <tr>
                    <th>Sample Code</th>
                    <th>Sample Name</th>
                    <th>Experiment</th>
                    {tableData.variables.map((v) => (
                      <th key={v}>{v}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tableData.rows.map((row) => (
                    <tr key={row.sample_id}>
                      <td style={{ fontWeight: 700 }}>{row.sample_code}</td>
                      <td>{row.sample_name}</td>
                      <td>{row.experiment_code}</td>
                      {tableData.variables.map((v) => {
                        const cell = row.cells[v]
                        if (!cell || cell.value === null || cell.value === undefined) {
                          return (
                            <td key={v} style={{ color: '#dc2626', fontStyle: 'italic' }}>
                              Missing
                            </td>
                          )
                        }
                        return (
                          <td key={v}>
                            <span style={{ fontWeight: 600 }}>
                              {typeof cell.value === 'number' ? cell.value.toFixed(3) : cell.value}
                            </span>
                            {cell.unit && <span style={{ fontSize: '0.75rem', color: '#64748b', marginLeft: 4 }}>{cell.unit}</span>}
                            <span style={{
                              marginLeft: 6,
                              fontSize: '0.6875rem',
                              padding: '1px 5px',
                              borderRadius: 3,
                              background: cell.status === 'MEASURED' ? '#ecfdf5' : '#eff6ff',
                              color: cell.status === 'MEASURED' ? '#047857' : '#1e40af',
                              fontWeight: 600,
                            }}>
                              {cell.status}
                            </span>
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Descriptive Statistics Summary Grid */}
          {descStats.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 12 }}>
                📐 Summary Descriptive Statistics
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 14 }}>
                {descStats.map((st) => (
                  <div key={st.variable} style={{ background: 'white', padding: 14, borderRadius: 8, border: '1px solid var(--color-border)' }}>
                    <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#1e293b', marginBottom: 6 }}>
                      {st.variable} (n = {st.sample_size_n})
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: '0.75rem' }}>
                      <div>Mean: <strong>{st.mean ?? 'N/A'}</strong></div>
                      <div>Median: <strong>{st.median ?? 'N/A'}</strong></div>
                      <div>Std Dev: <strong>{st.std_dev ?? 'N/A'}</strong></div>
                      <div>Range: <strong>{st.val_range ?? 'N/A'}</strong></div>
                      <div>Min: <strong>{st.min_val ?? 'N/A'}</strong></div>
                      <div>Max: <strong>{st.max_val ?? 'N/A'}</strong></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Statistical Analysis Control & Chart Section */}
          <div style={{ background: '#f8fafc', padding: 16, borderRadius: 8, border: '1px solid #e2e8f0', marginBottom: 24 }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 12 }}>
              ⚙ Statistical Analysis & Relationship Visualizer
            </h3>

            <form onSubmit={handleRunAnalysis} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 12, alignItems: 'end', marginBottom: 16 }}>
              <div>
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Analysis Method</label>
                <select
                  className="form-control"
                  value={analysisType}
                  onChange={(e) => setAnalysisType(e.target.value)}
                >
                  <option value="REGRESSION">OLS Linear Regression</option>
                  <option value="CORRELATION">Pearson Correlation</option>
                  <option value="GROUP_COMPARISON">Group Factor Comparison</option>
                  <option value="OUTLIERS">Outlier Detection (1.5 * IQR)</option>
                </select>
              </div>

              <div>
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Independent Variable (X)</label>
                <select
                  className="form-control"
                  value={xVar}
                  onChange={(e) => setXVar(e.target.value)}
                >
                  {tableData.variables.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Dependent Variable (Y)</label>
                <select
                  className="form-control"
                  value={yVar}
                  onChange={(e) => setYVar(e.target.value)}
                >
                  {tableData.variables.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
              </div>

              <button type="submit" className="btn btn-primary" disabled={analyzing}>
                {analyzing ? <InlineSpinner /> : '▶ Run Analysis'}
              </button>
            </form>

            {/* Statistical Results Card */}
            {statResult && (
              <div style={{ background: '#f0f9ff', padding: 14, borderRadius: 6, border: '1px solid #bae6fd', marginBottom: 16 }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0369a1', margin: '0 0 6px 0' }}>
                  📌 {statResult.method} Results (n = {statResult.sample_size})
                </h4>

                {statResult.analysis_type === 'REGRESSION' && regressionData && (
                  <div style={{ fontSize: '0.8125rem' }}>
                    <div>Formula: <strong>{regressionData.formula}</strong></div>
                    <div>R²: <strong>{regressionData.rSquared}</strong> · Slope: <strong>{regressionData.slope}</strong></div>
                    <div style={{ marginTop: 4, color: '#0c4a6e' }}>{(statResult.results_json as any).interpretation}</div>
                  </div>
                )}

                {statResult.analysis_type === 'CORRELATION' && (
                  <div style={{ fontSize: '0.8125rem' }}>
                    <div>Pearson r: <strong>{(statResult.results_json as any).pearson_r}</strong> · p-value: <strong>{(statResult.results_json as any).p_value ?? 'N/A'}</strong></div>
                    <div style={{ marginTop: 4, color: '#0c4a6e' }}>{(statResult.results_json as any).interpretation}</div>
                  </div>
                )}

                {(statResult.warnings_json as any)?.warnings && Array.isArray((statResult.warnings_json as any).warnings) && (
                  <div style={{ marginTop: 8, fontSize: '0.75rem', color: '#92400e', background: '#fef3c7', padding: '6px 10px', borderRadius: 4 }}>
                    ⚠️ {((statResult.warnings_json as any)?.warnings as string[])?.join(' ')}
                  </div>
                )}
              </div>
            )}

            {/* Comparison Plot Chart */}
            <ComparisonPlotChart
              xLabel={xVar}
              yLabel={yVar}
              points={scatterPoints}
              regression={regressionData}
            />
          </div>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)', background: 'white', borderRadius: 8, border: '1px solid var(--color-border)' }}>
          No comparison dataset selected. Click "+ Create Comparison Dataset" above to begin.
        </div>
      )}

      {/* Dataset Builder Modal */}
      {showBuilderModal && (
        <DatasetBuilderModal
          onClose={() => setShowBuilderModal(false)}
          onDatasetCreated={(newId) => {
            setShowBuilderModal(false)
            if (selectedProjId) {
              analysisService.listDatasets(selectedProjId).then((dsList) => {
                setDatasets(dsList)
                setSelectedDatasetId(newId)
              })
            }
          }}
        />
      )}
    </div>
  )
}
