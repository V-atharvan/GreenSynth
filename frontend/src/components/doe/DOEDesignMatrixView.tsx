import React, { useState } from 'react';
import { DOEResponse, ProposedExperiment, doeService } from '../../services/doeService';
import { Download, CheckCircle2, FlaskConical, ArrowRight, Check } from 'lucide-react';

interface DOEDesignMatrixViewProps {
  doe: DOEResponse;
  proposedRuns: ProposedExperiment[];
  onRefresh: () => void;
}

interface ToastMessage {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  title: string;
  message: string;
}

const FACTOR_LABELS: Record<string, { label: string; unit?: string }> = {
  substrate_temperature_c: { label: 'Substrate Temp', unit: '°C' },
  substrate_temperature: { label: 'Substrate Temp', unit: '°C' },
  precursor_concentration: { label: 'Precursor Conc', unit: 'M' },
  spray_rate_ml_min: { label: 'Spray Rate', unit: 'mL/min' },
  spray_rate: { label: 'Spray Rate', unit: 'mL/min' },
  spray_duration_min: { label: 'Spray Duration', unit: 'min' },
  spray_duration: { label: 'Spray Duration', unit: 'min' },
  spray_cycles: { label: 'Spray Cycles', unit: 'cycles' },
  nozzle_substrate_distance_cm: { label: 'Nozzle Distance', unit: 'cm' },
  nozzle_distance: { label: 'Nozzle Distance', unit: 'cm' },
  carrier_gas_pressure_kpa: { label: 'Carrier Gas Pres', unit: 'kPa' },
  carrier_gas_pressure: { label: 'Carrier Gas Pres', unit: 'kPa' },
  mulberry_extract_volume: { label: 'Extract Vol', unit: 'mL' },
  mulberry_extract_concentration: { label: 'Extract Conc', unit: 'wt%' },
  precursor_solution_volume: { label: 'Precursor Vol', unit: 'mL' },
  ethanol_volume: { label: 'Ethanol Vol', unit: 'mL' },
  ambient_temperature_c: { label: 'Ambient Temp', unit: '°C' },
  ambient_relative_humidity: { label: 'Ambient Humidity', unit: '%' },
};

function formatFactorHeader(code: string): { label: string; unit?: string } {
  const norm = code.toLowerCase().trim();
  if (FACTOR_LABELS[norm]) {
    return FACTOR_LABELS[norm];
  }
  const clean = code.replace(/_/g, ' ').toLowerCase();
  const label = clean.charAt(0).toUpperCase() + clean.slice(1);
  return { label };
}

export const DOEDesignMatrixView: React.FC<DOEDesignMatrixViewProps> = ({ doe, proposedRuns, onRefresh }) => {
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = (type: 'success' | 'info' | 'warning' | 'error', title: string, message: string) => {
    const id = `${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    setToasts((prev) => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  };

  const factorKeys = doe.factors ? doe.factors.map((f) => f.parameter_code) : [];

  const handleApproveStudy = async () => {
    try {
      setLoadingId('approve_study');
      setError(null);
      await doeService.approveDOEStudy(doe.id);
      showToast('success', 'Study Approved & Locked', `DOE study "${doe.name}" has been marked as APPROVED (v${doe.version}).`);
      onRefresh();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to approve DOE study.';
      setError(msg);
      showToast('error', 'Approval Failed', msg);
    } finally {
      setLoadingId(null);
    }
  };

  const handleExportCsv = async () => {
    try {
      setLoadingId('export_csv');
      setError(null);
      const blob = await doeService.exportDOECSV(doe.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const safeName = doe.name.replace(/[^a-zA-Z0-9_-]/g, '_');
      a.download = `${safeName}_design_matrix.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showToast('success', 'CSV Export Ready', `Downloaded ${proposedRuns.length} experimental design runs to ${safeName}_design_matrix.csv.`);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to export DOE CSV.';
      setError(msg);
      showToast('error', 'Export Failed', msg);
    } finally {
      setLoadingId(null);
    }
  };

  const handleConvertRun = async (r: ProposedExperiment) => {
    try {
      setLoadingId(r.id);
      setError(null);
      await doeService.convertRunToPlannedExperiment(r.id);
      showToast('success', 'Experiment Planned', `Run #${r.run_order} (${r.design_condition_id}) converted to a PLANNED experiment.`);
      onRefresh();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to convert proposed run.';
      setError(msg);
      showToast('error', 'Conversion Failed', msg);
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Floating Top-Right Toast Notifications */}
      {toasts.length > 0 && (
        <div className="gs-toast-container" style={{ position: 'fixed', top: 24, right: 24, zIndex: 99999, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {toasts.map((toast) => (
            <div
              key={toast.id}
              className={`gs-toast-card ${toast.type}`}
              style={{
                background: '#ffffff',
                border: '1px solid var(--color-border)',
                borderLeft: `4px solid ${toast.type === 'success' ? '#059669' : toast.type === 'error' ? '#dc2626' : '#2563eb'}`,
                borderRadius: '8px',
                padding: '12px 16px',
                boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
                minWidth: 320,
                maxWidth: 420,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                <strong style={{ fontSize: '0.875rem', color: 'var(--color-text)' }}>{toast.title}</strong>
                <button
                  onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}
                >
                  ✕
                </button>
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>{toast.message}</div>
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="gs-alert error" style={{ margin: 0 }}>
          {error}
        </div>
      )}

      {/* Main Design Matrix Runs Card */}
      <div className="gs-panel" style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', border: '1px solid var(--color-border)', overflow: 'hidden' }}>
        <div
          className="gs-panel-header"
          style={{
            padding: '16px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 12,
            borderBottom: '1px solid var(--color-border)',
            background: '#fafbfc',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className="gs-panel-title" style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--color-text)' }}>
                Design Matrix Runs ({proposedRuns.length})
              </span>
              <span className="gs-badge teal" style={{ fontSize: '0.6875rem' }}>{doe.design_method}</span>
              <span className={`gs-chip ${doe.status === 'APPROVED' ? 'stable' : 'warning'}`} style={{ fontSize: '0.6875rem' }}>
                {doe.status}
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: 4 }}>
              Replicates: <strong>{doe.replicates}</strong> &nbsp;•&nbsp; Random Seed: <code style={{ fontFamily: 'var(--font-mono)' }}>{doe.random_seed}</code> &nbsp;•&nbsp; PROPOSED runs require approval before lab synthesis
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={handleExportCsv}
              disabled={loadingId === 'export_csv'}
              className="gs-btn gs-btn-outline gs-btn-sm"
              style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
              title="Download full design matrix as CSV file"
            >
              <Download size={14} />
              {loadingId === 'export_csv' ? 'Exporting…' : 'Export CSV'}
            </button>
            {doe.status !== 'APPROVED' && (
              <button
                onClick={handleApproveStudy}
                disabled={loadingId === 'approve_study'}
                className="gs-btn gs-btn-emerald gs-btn-sm"
                style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
              >
                <CheckCircle2 size={14} />
                {loadingId === 'approve_study' ? 'Approving…' : 'Approve Study & Lock V1'}
              </button>
            )}
          </div>
        </div>

        {/* Matrix Table */}
        <div className="gs-table-wrapper" style={{ overflowX: 'auto', width: '100%' }}>
          <table className="gs-table" style={{ width: '100%', minWidth: '920px', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid var(--color-border)' }}>
                <th style={{ width: 65, padding: '10px 14px', fontSize: '0.6875rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                  Run #
                </th>
                <th style={{ width: 95, padding: '10px 14px', fontSize: '0.6875rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                  Condition ID
                </th>
                <th style={{ width: 75, padding: '10px 14px', fontSize: '0.6875rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                  Replicate
                </th>
                <th style={{ width: 100, padding: '10px 14px', fontSize: '0.6875rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                  Type
                </th>
                {factorKeys.map((fk) => {
                  const { label, unit } = formatFactorHeader(fk);
                  return (
                    <th key={fk} style={{ padding: '10px 14px', textAlign: 'left', minWidth: 110 }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#0f766e', lineHeight: 1.2 }}>
                        {label}
                      </div>
                      {unit && (
                        <div style={{ fontSize: '0.6875rem', fontWeight: 500, color: 'var(--color-text-secondary)' }}>
                          ({unit})
                        </div>
                      )}
                    </th>
                  );
                })}
                <th style={{ width: 90, padding: '10px 14px', fontSize: '0.6875rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                  Status
                </th>
                <th style={{ width: 175, padding: '10px 16px', fontSize: '0.6875rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', textAlign: 'right' }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {proposedRuns.map((r) => (
                <tr key={r.id} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                  <td style={{ padding: '10px 14px', fontWeight: 700, color: 'var(--color-text)', fontSize: '0.8125rem' }}>
                    #{r.run_order}
                  </td>
                  <td style={{ padding: '10px 14px', fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: '#334155' }}>
                    {r.design_condition_id}
                  </td>
                  <td style={{ padding: '10px 14px', fontSize: '0.75rem', color: '#4f46e5', fontWeight: 600 }}>
                    Rep {r.replicate_number}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    {r.is_center_point ? (
                      <span className="gs-badge indigo" style={{ fontSize: '0.6875rem', fontWeight: 600 }}>Center Point</span>
                    ) : (
                      <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.75rem', fontWeight: 500 }}>Factorial</span>
                    )}
                  </td>
                  {factorKeys.map((fk) => (
                    <td key={fk} style={{ padding: '10px 14px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#0f766e', fontSize: '0.8125rem' }}>
                      {r.factor_values[fk] !== undefined ? String(r.factor_values[fk]) : '—'}
                    </td>
                  ))}
                  <td style={{ padding: '10px 14px' }}>
                    <span className={`gs-chip ${r.status === 'PLANNED' ? 'info' : r.status === 'APPROVED' ? 'stable' : 'warning'}`} style={{ fontSize: '0.6875rem' }}>
                      {r.status}
                    </span>
                  </td>
                  <td style={{ padding: '10px 16px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                    {r.status === 'PLANNED' ? (
                      <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        <Check size={13} /> PLANNED
                      </span>
                    ) : (
                      <button
                        onClick={() => handleConvertRun(r)}
                        disabled={loadingId === r.id}
                        className="gs-btn gs-btn-indigo gs-btn-sm"
                        style={{ fontSize: '0.75rem', padding: '4px 10px', display: 'inline-flex', alignItems: 'center', gap: 4 }}
                      >
                        <FlaskConical size={12} />
                        {loadingId === r.id ? 'Converting…' : 'Convert to Experiment'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
