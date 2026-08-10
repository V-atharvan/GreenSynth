import React, { useEffect, useState } from 'react';
import {
  CorrelationMatrixResponse,
  DataQualityReportResponse,
  DatasetVersionResponse,
  DescriptiveStatsItem,
  EvidenceResponse,
  ModelDiagnosticsResponse,
  ReadinessGatesResponse,
  RegressionResponse,
  evidenceService,
} from '../services/evidenceService';
import { apiClient } from '../services/api';
import {
  BarChart2,
  TrendingUp,
  ShieldCheck,
  FileText,
  FolderKanban,
  AlertTriangle,
  Download,
  CheckCircle2,
} from 'lucide-react';
import axios from 'axios';

export const StatisticalAnalysisStudio: React.FC = () => {
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'descriptive' | 'correlation' | 'regression' | 'quality' | 'evidence'>('descriptive');

  // Simulated Dataset Version & Data
  const [datasetVersion] = useState<DatasetVersionResponse | null>({
    id: 'dv-proj7-v1',
    dataset_id: 'ds-proj7-001',
    project_id: 'proj-007',
    name: 'PROJECT7-SPRAY-PYROLYSIS-DATASET',
    version: 'v1.0',
    description: 'Project 7 CuO Spray Pyrolysis synthesis dataset snapshot.',
    included_sample_ids: ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8'],
    included_experiment_ids: ['exp1', 'exp2'],
    included_factors: ['substrate_temperature', 'spray_rate', 'precursor_concentration'],
    included_responses: ['conductivity_s_cm', 'band_gap_ev'],
    summary_json: {
      total_samples: 8,
      included_samples_count: 8,
      missing_responses_count: { conductivity_s_cm: 0, band_gap_ev: 0 },
    },
    status: 'ACTIVE',
    created_at: new Date().toISOString(),
  });

  const [descriptiveItems] = useState<DescriptiveStatsItem[]>([
    {
      variable: 'substrate_temperature',
      sample_size_n: 8,
      unit: '°C',
      mean: 350.0,
      median: 350.0,
      std_dev: 40.82,
      variance: 1666.67,
      min_val: 300.0,
      max_val: 400.0,
      val_range: 100.0,
      q1: 325.0,
      q3: 375.0,
      iqr: 50.0,
      cv: 11.66,
      missing_count: 0,
    },
    {
      variable: 'conductivity_s_cm',
      sample_size_n: 8,
      unit: 'S/cm',
      mean: 3.4,
      median: 3.35,
      std_dev: 1.85,
      variance: 3.42,
      min_val: 1.2,
      max_val: 5.8,
      val_range: 4.6,
      q1: 1.88,
      q3: 4.98,
      iqr: 3.1,
      cv: 54.41,
      missing_count: 0,
    },
    {
      variable: 'band_gap_ev',
      sample_size_n: 8,
      unit: 'eV',
      mean: 1.52,
      median: 1.51,
      std_dev: 0.08,
      variance: 0.006,
      min_val: 1.42,
      max_val: 1.65,
      val_range: 0.23,
      q1: 1.45,
      q3: 1.58,
      iqr: 0.13,
      cv: 5.26,
      missing_count: 0,
    },
  ]);

  const [correlationMethod, setCorrelationMethod] = useState<'PEARSON' | 'SPEARMAN'>('PEARSON');
  const [correlationData] = useState<CorrelationMatrixResponse>({
    method: 'Pearson Correlation Matrix',
    variables: ['substrate_temperature', 'spray_rate', 'conductivity_s_cm', 'band_gap_ev'],
    matrix: {
      substrate_temperature: { substrate_temperature: 1.0, spray_rate: 0.0, conductivity_s_cm: 0.89, band_gap_ev: -0.74 },
      spray_rate: { substrate_temperature: 0.0, spray_rate: 1.0, conductivity_s_cm: 0.31, band_gap_ev: -0.15 },
      conductivity_s_cm: { substrate_temperature: 0.89, spray_rate: 0.31, conductivity_s_cm: 1.0, band_gap_ev: -0.81 },
      band_gap_ev: { substrate_temperature: -0.74, spray_rate: -0.15, conductivity_s_cm: -0.81, band_gap_ev: 1.0 },
    },
    sample_size_n: 8,
    warnings: ['Correlation estimate is based on limited observations (N < 10).'],
  });

  const [regressionModel] = useState<RegressionResponse>({
    y_variable: 'conductivity_s_cm',
    x_variables: ['substrate_temperature', 'spray_rate'],
    model_type: 'INTERACTION',
    method: 'Ordinary Least Squares Regression',
    formula: 'conductivity_s_cm = -9.2 + 0.035 * substrate_temperature + 0.42 * spray_rate + 0.001 * substrate_temperature:spray_rate',
    coefficients: {
      substrate_temperature: 0.035,
      spray_rate: 0.42,
      'substrate_temperature:spray_rate': 0.001,
    },
    intercept: -9.2,
    r_squared: 0.9412,
    adjusted_r_squared: 0.8971,
    rmse: 0.32,
    mae: 0.25,
    aic: 12.4,
    bic: 14.8,
    confidence_interval: { slope: [0.022, 0.048] },
    prediction_interval: { y_pred: [1.1, 5.9] },
    sample_size_n: 8,
    interpretation: 'Statistically fitted model for conductivity_s_cm using 3 predictors (R² = 0.9412, Adj R² = 0.8971, RMSE = 0.32, N = 8).',
    warnings: ['Model complexity (p=3) is high relative to available observations (N=8). Model may be overfitted.'],
  });

  const [diagnostics] = useState<ModelDiagnosticsResponse>({
    residuals: [-0.15, 0.22, -0.08, 0.12, -0.25, 0.18, -0.04, 0.10],
    fitted_values: [1.35, 1.88, 4.58, 5.68, 1.45, 2.12, 4.32, 5.72],
    qq_sample_quantiles: [-1.42, -0.85, -0.45, -0.12, 0.25, 0.65, 0.95, 1.38],
    qq_theoretical_quantiles: [-1.53, -0.89, -0.49, -0.16, 0.16, 0.49, 0.89, 1.53],
    heteroscedasticity_warning: false,
    normality_warning: false,
    diagnostic_summary: 'Residual diagnostics evaluated on N=8 observations. Residual diagnostics help assess whether the chosen statistical model assumptions are appropriate.',
  });

  const [qualityReport] = useState<DataQualityReportResponse>({
    total_samples: 8,
    variables_evaluated: ['substrate_temperature', 'spray_rate', 'conductivity_s_cm', 'band_gap_ev'],
    missing_counts: { substrate_temperature: 0, spray_rate: 0, conductivity_s_cm: 0, band_gap_ev: 0 },
    duplicate_count: 0,
    outlier_count: 0,
    unit_consistency: 'PASS',
    quality_status: 'PASS',
    warnings: [],
  });

  const [readinessGates] = useState<ReadinessGatesResponse>({
    dataset_version_id: 'dv-proj7-v1',
    is_ml_ready: true,
    ml_ready_criteria: {
      sufficient_sample_size: true,
      acceptable_missing_rate: true,
      quality_status_pass_or_warning: true,
      dataset_version_locked: true,
    },
    is_optimization_ready: true,
    optimization_ready_criteria: {
      is_ml_ready: true,
      has_validated_statistical_model: true,
      sample_size_sufficient_for_optimization: true,
    },
    disclaimer: 'ML_READY / OPTIMIZATION_READY indicates compliance with software validation quality gates; it does not constitute peer-reviewed scientific proof.',
  });

  const [evidenceList] = useState<EvidenceResponse[]>([
    {
      id: 'ev-001',
      dataset_version_id: 'dv-proj7-v1',
      statement: 'Within the analyzed Project 7 dataset (N=8), electrical conductivity showed a statistically detectable positive association with substrate temperature using Pearson Correlation (r = 0.89, p = 0.003).',
      evidence_type: 'ASSOCIATION',
      variables: ['substrate_temperature', 'conductivity_s_cm'],
      sample_size: 8,
      statistical_method: 'Pearson Correlation',
      effect_estimate: 0.89,
      uncertainty: 0.05,
      confidence_interval: { lower: 0.55, upper: 0.97 },
      evidence_score: 82.5,
      scoring_criteria: { sample_size_points: 24, replicate_points: 20, completeness_points: 20, diagnostics_points: 18.5, total_score: 82.5, quality_category: 'HIGH' },
      limitations: ['Limited temperature range (300°C - 400°C)', 'Small sample size N=8'],
      status: 'APPROVED',
      created_at: new Date().toISOString(),
    },
  ]);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await apiClient.get('/projects');
        setProjects(res.data);
        if (res.data.length > 0) setSelectedProjectId(res.data[0].id);
      } catch (err) {
        console.log('Failed to fetch projects:', err);
      }
    };
    fetchProjects();
  }, []);

  return (
    <div className="gs-page">

      {/* Page Header */}
      <div className="gs-page-header">
        <div>
          <div style={{ marginBottom: 4 }}>
            <span className="gs-badge teal">Phase 15 — Advanced Statistical Analysis &amp; Evidence Layer</span>
            <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginLeft: 10 }}>Scientific Evidence &amp; Provenance Framework</span>
          </div>
          <div className="gs-page-title">
            <div className="gs-page-title-icon emerald">
              <BarChart2 className="w-5 h-5 text-emerald-600" />
            </div>
            Statistical Analysis &amp; Evidence Studio
          </div>
          <p className="gs-page-subtitle">
            Convert raw &amp; validated experimental data into formal statistical evidence. Enforce dataset snapshot versioning (V1 &rarr; V2), cautious scientific statements (no automatic causality claims), outlier flagging without raw data deletion, regression diagnostics, and ML-Ready quality gates.
          </p>
        </div>

        <div className="gs-header-actions">
          <div style={{ padding: '8px 14px', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
            <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: '#065f46', textTransform: 'uppercase', letterSpacing: '0.05em' }}>ML-Ready Quality Gate</div>
            <div style={{ fontSize: '0.875rem', fontWeight: 800, color: '#047857', marginTop: 2, display: 'flex', alignItems: 'center', gap: 4, justifyContent: 'center' }}>
              <ShieldCheck className="w-4 h-4 text-emerald-600" /> {readinessGates.is_ml_ready ? 'ML_READY (PASS)' : 'NOT_READY'}
            </div>
          </div>

          <div className="gs-field">
            <label className="gs-label">Active Project</label>
            <select
              className="gs-select"
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Dataset Version Banner */}
      {datasetVersion && (
        <div className="gs-panel">
          <div className="gs-panel-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <FolderKanban className="w-6 h-6 text-indigo-500" />
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--color-text)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>{datasetVersion.name}</span>
                  <span className="gs-badge indigo">{datasetVersion.version}</span>
                </div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>{datasetVersion.description}</div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 20, fontFamily: 'var(--font-mono)' }}>
              <div>
                <div style={{ fontSize: '0.6875rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Included Samples</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#059669' }}>{datasetVersion.summary_json.total_samples}</div>
              </div>
              <div style={{ width: 1, background: 'var(--color-border)' }} />
              <div>
                <div style={{ fontSize: '0.6875rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Factors</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-text)' }}>{datasetVersion.included_factors.length}</div>
              </div>
              <div style={{ width: 1, background: 'var(--color-border)' }} />
              <div>
                <div style={{ fontSize: '0.6875rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Responses</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-text)' }}>{datasetVersion.included_responses.length}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, borderBottom: '2px solid var(--color-border)', paddingBottom: 2 }}>
        {[
          { key: 'descriptive', label: 'Descriptive & Grouped Stats' },
          { key: 'correlation', label: 'Correlation Matrix' },
          { key: 'regression', label: 'Regression & Q-Q Diagnostics' },
          { key: 'quality', label: 'Data Quality Dashboard' },
          { key: 'evidence', label: `Evidence Records (${evidenceList.length})` },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key as any)}
            className="gs-btn"
            style={{
              background: activeTab === key ? 'var(--color-primary)' : 'transparent',
              color: activeTab === key ? 'white' : 'var(--color-text-secondary)',
              border: 'none',
              borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
              fontWeight: activeTab === key ? 700 : 500,
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* TAB 1: DESCRIPTIVE */}
      {activeTab === 'descriptive' && (
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">Comprehensive Variable Summary (Always Displays N)</span>
          </div>
          <div className="gs-table-wrapper">
            <table className="gs-table">
              <thead>
                <tr>
                  <th>Variable</th>
                  <th>Unit</th>
                  <th>N (Observed)</th>
                  <th style={{ color: '#059669' }}>Mean</th>
                  <th>Median</th>
                  <th>SD</th>
                  <th>Min</th>
                  <th>Max</th>
                  <th>IQR</th>
                  <th>CV (%)</th>
                </tr>
              </thead>
              <tbody>
                {descriptiveItems.map((item, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 700 }}>{item.variable}</td>
                    <td style={{ color: 'var(--color-text-secondary)' }}>{item.unit || '—'}</td>
                    <td style={{ fontWeight: 700, color: '#4f46e5', fontFamily: 'var(--font-mono)' }}>{item.sample_size_n}</td>
                    <td style={{ fontWeight: 800, color: '#059669', fontFamily: 'var(--font-mono)' }}>{item.mean}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{item.median}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{item.std_dev}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{item.min_val}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{item.max_val}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: '#b45309' }}>{item.iqr}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{item.cv !== null ? `${item.cv}%` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: CORRELATION MATRIX */}
      {activeTab === 'correlation' && (
        <div className="gs-panel">
          <div className="gs-panel-header">
            <div>
              <span className="gs-panel-title">Correlation Matrix Analysis</span>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
                Evaluates monotonic (Spearman) or linear (Pearson) statistical associations without inferring causation.
              </p>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              {['PEARSON', 'SPEARMAN'].map((m) => (
                <button
                  key={m}
                  onClick={() => setCorrelationMethod(m as any)}
                  className="gs-btn gs-btn-sm"
                  style={{
                    background: correlationMethod === m ? 'var(--color-primary)' : 'var(--color-bg)',
                    color: correlationMethod === m ? 'white' : 'var(--color-text-secondary)',
                  }}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>
          <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {correlationData.warnings.map((w, idx) => (
              <div key={idx} className="gs-alert warning" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>{w}</span>
              </div>
            ))}

            <div className="gs-table-wrapper">
              <table className="gs-table" style={{ textAlign: 'center' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Variable</th>
                    {correlationData.variables.map((v) => (
                      <th key={v} style={{ fontFamily: 'var(--font-mono)' }}>{v}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {correlationData.variables.map((v1) => (
                    <tr key={v1}>
                      <td style={{ textAlign: 'left', fontWeight: 700 }}>{v1}</td>
                      {correlationData.variables.map((v2) => {
                        const val = correlationData.matrix[v1]?.[v2] ?? 0.0;
                        const isSelf = v1 === v2;
                        const cellStyle: React.CSSProperties = isSelf
                          ? { background: 'var(--color-bg)', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }
                          : val > 0.5
                          ? { background: '#d1fae5', color: '#065f46', fontWeight: 700, fontFamily: 'var(--font-mono)' }
                          : val < -0.5
                          ? { background: '#ffe4e6', color: '#9f1239', fontWeight: 700, fontFamily: 'var(--font-mono)' }
                          : { fontFamily: 'var(--font-mono)' };
                        return (
                          <td key={v2} style={cellStyle}>
                            {val.toFixed(2)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: REGRESSION MODELS */}
      {activeTab === 'regression' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="gs-panel">
            <div className="gs-panel-header">
              <span className="gs-panel-title">Polynomial Regression Fit &amp; Model Selection</span>
            </div>
            <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ background: '#f8fafc', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '14px 16px', fontFamily: 'var(--font-mono)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', marginBottom: 4 }}>Fitted Model Formula:</div>
                <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0d9488' }}>{regressionModel.formula}</div>
              </div>

              <div className="gs-metrics-row">
                <div className="gs-metric-card emerald">
                  <div className="gs-metric-value">{regressionModel.r_squared}</div>
                  <div className="gs-metric-label">R² Fit</div>
                </div>
                <div className="gs-metric-card indigo">
                  <div className="gs-metric-value">{regressionModel.adjusted_r_squared}</div>
                  <div className="gs-metric-label">Adj R²</div>
                </div>
                <div className="gs-metric-card amber">
                  <div className="gs-metric-value">{regressionModel.rmse}</div>
                  <div className="gs-metric-label">RMSE Error</div>
                </div>
                <div className="gs-metric-card teal">
                  <div className="gs-metric-value">{regressionModel.mae}</div>
                  <div className="gs-metric-label">MAE</div>
                </div>
              </div>

              {regressionModel.warnings.map((w, idx) => (
                <div key={idx} className="gs-alert warning" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>{w}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="gs-panel">
            <div className="gs-panel-header">
              <span className="gs-panel-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <TrendingUp className="w-4 h-4 text-emerald-600" /> Normal Q-Q Residual Diagnostic Plot
              </span>
            </div>
            <div className="gs-panel-body">
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: 16 }}>
                {diagnostics.diagnostic_summary}
              </p>
              <div style={{ height: 240, background: '#f8fafc', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
                <svg width="100%" height="100%" viewBox="-2 -2 4 4">
                  <line x1="-1.8" y1="-1.8" x2="1.8" y2="1.8" stroke="#94a3b8" strokeDasharray="0.05" strokeWidth="0.02" />
                  {diagnostics.qq_theoretical_quantiles.map((t, idx) => {
                    const s = diagnostics.qq_sample_quantiles[idx] ?? 0;
                    return <circle key={idx} cx={t * 0.8} cy={s * 0.8} r="0.04" fill="#0d9488" />;
                  })}
                </svg>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: QUALITY DASHBOARD */}
      {activeTab === 'quality' && (
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">Data Quality Dashboard Checks</span>
            <span className="gs-chip stable">Status: {qualityReport.quality_status}</span>
          </div>
          <div className="gs-panel-body">
            <div className="gs-metrics-row">
              <div className="gs-metric-card emerald">
                <div className="gs-metric-value" style={{ fontSize: '1.25rem' }}>0 Missing</div>
                <div className="gs-metric-label">Missing Measurements</div>
              </div>
              <div className="gs-metric-card indigo">
                <div className="gs-metric-value" style={{ fontSize: '1.25rem' }}>0 Duplicates</div>
                <div className="gs-metric-label">Duplicate Records</div>
              </div>
              <div className="gs-metric-card amber">
                <div className="gs-metric-value" style={{ fontSize: '1.25rem' }}>0 Flagged</div>
                <div className="gs-metric-label">Flagged Outliers</div>
              </div>
              <div className="gs-metric-card teal">
                <div className="gs-metric-value" style={{ fontSize: '1.25rem' }}>PASS</div>
                <div className="gs-metric-label">Unit Consistency</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: EVIDENCE RECORD MANAGER */}
      {activeTab === 'evidence' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {evidenceList.map((ev) => (
            <div key={ev.id} className="gs-panel">
              <div className="gs-panel-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className="gs-chip info">{ev.evidence_type}</span>
                  <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>N = {ev.sample_size} | {ev.statistical_method}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontWeight: 700, color: '#059669', fontFamily: 'var(--font-mono)', fontSize: '0.875rem' }}>
                    Score: {ev.evidence_score} / 100
                  </span>
                  <a
                    href={evidenceService.exportEvidenceReportUrl(ev.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="gs-btn gs-btn-outline gs-btn-sm"
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                  >
                    <Download className="w-3.5 h-3.5" /> Export Report
                  </a>
                </div>
              </div>
              <div className="gs-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div className="gs-info-banner blue">
                  <div className="gs-info-banner-icon">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <div className="gs-info-banner-title">Conservative Scientific Statement</div>
                    <div className="gs-info-banner-text" style={{ fontSize: '0.875rem', fontWeight: 600 }}>&ldquo;{ev.statement}&rdquo;</div>
                  </div>
                </div>

                {ev.limitations && ev.limitations.length > 0 && (
                  <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                    <strong style={{ color: 'var(--color-text)' }}>Known Limitations:</strong>
                    <ul style={{ paddingLeft: 18, marginTop: 4 }}>
                      {ev.limitations.map((lim, idx) => (
                        <li key={idx}>{lim}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
