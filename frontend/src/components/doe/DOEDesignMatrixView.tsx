import React, { useState } from 'react';
import { DOEResponse, ProposedExperiment, doeService } from '../../services/doeService';

interface DOEDesignMatrixViewProps {
  doe: DOEResponse;
  proposedRuns: ProposedExperiment[];
  onRefresh: () => void;
}

export const DOEDesignMatrixView: React.FC<DOEDesignMatrixViewProps> = ({ doe, proposedRuns, onRefresh }) => {
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const factorKeys = doe.factors ? doe.factors.map((f) => f.parameter_code) : [];

  const handleApproveStudy = async () => {
    try {
      setLoadingId('approve_study');
      setError(null);
      await doeService.approveDOEStudy(doe.id);
      onRefresh();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to approve DOE study.');
    } finally { setLoadingId(null); }
  };

  const handleConvertRun = async (proposedId: string) => {
    try {
      setLoadingId(proposedId);
      setError(null);
      await doeService.convertRunToPlannedExperiment(proposedId);
      onRefresh();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to convert proposed run.');
    } finally { setLoadingId(null); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Header */}
      <div className="gs-panel">
        <div className="gs-panel-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--color-text)' }}>{doe.name}</span>
            <span className="gs-badge teal">{doe.version}</span>
            <span className={`gs-chip ${doe.status === 'APPROVED' ? 'stable' : 'warning'}`}>{doe.status}</span>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <a
              href={doeService.exportDOECSVUrl(doe.id)}
              target="_blank"
              rel="noreferrer"
              className="gs-btn gs-btn-outline gs-btn-sm"
            >
              📥 Export CSV
            </a>
            {doe.status !== 'APPROVED' && (
              <button
                onClick={handleApproveStudy}
                disabled={loadingId === 'approve_study'}
                className="gs-btn gs-btn-emerald gs-btn-sm"
              >
                {loadingId === 'approve_study' ? '⏳ Approving…' : '🔒 Approve Study & Lock V1'}
              </button>
            )}
          </div>
        </div>
        <div style={{ padding: '8px 24px', fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
          {doe.research_question || doe.description}
        </div>
      </div>

      {error && <div className="gs-alert error">⚠️ {error}</div>}

      {/* Design Matrix Table */}
      <div className="gs-panel">
        <div className="gs-panel-header">
          <span className="gs-panel-title">🧪 Design Matrix Runs ({proposedRuns.length})</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
            Replicates: {doe.replicates} | Seed: {doe.random_seed} · PROPOSED conditions await researcher approval
          </span>
        </div>
        <div className="gs-table-wrapper">
          <table className="gs-table">
            <thead>
              <tr>
                <th>Run #</th>
                <th>Condition ID</th>
                <th>Replicate</th>
                <th>Type</th>
                {factorKeys.map((fk) => (
                  <th key={fk} style={{ color: '#059669' }}>{fk}</th>
                ))}
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {proposedRuns.map((r) => (
                <tr key={r.id}>
                  <td style={{ fontWeight: 700 }}>#{r.run_order}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem' }}>{r.design_condition_id}</td>
                  <td style={{ color: '#4f46e5' }}>Rep {r.replicate_number}</td>
                  <td>
                    {r.is_center_point
                      ? <span className="gs-badge indigo">Center Point</span>
                      : <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem' }}>Factorial</span>}
                  </td>
                  {factorKeys.map((fk) => (
                    <td key={fk} style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#059669' }}>
                      {r.factor_values[fk] !== undefined ? String(r.factor_values[fk]) : '—'}
                    </td>
                  ))}
                  <td>
                    <span className={`gs-chip ${r.status === 'PLANNED' ? 'info' : r.status === 'APPROVED' ? 'stable' : 'warning'}`}>
                      {r.status}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    {r.status === 'PLANNED' ? (
                      <span style={{ fontSize: '0.75rem', color: '#2563eb', fontStyle: 'italic' }}>Converted to PLANNED</span>
                    ) : (
                      <button
                        onClick={() => handleConvertRun(r.id)}
                        disabled={loadingId === r.id}
                        className="gs-btn gs-btn-indigo gs-btn-sm"
                      >
                        {loadingId === r.id ? '⏳ Converting…' : '🔬 Convert to Experiment'}
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
