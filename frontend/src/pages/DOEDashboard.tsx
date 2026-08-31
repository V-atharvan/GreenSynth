import React, { useEffect, useState, useCallback } from 'react';
import { Ruler, AlertTriangle, FolderKanban } from 'lucide-react';
import { DOEResponse, ProposedExperiment, doeService } from '../services/doeService';
import { DOEDesignMatrixView } from '../components/doe/DOEDesignMatrixView';
import { DOEAnalysisView } from '../components/doe/DOEAnalysisView';
import { DOEWizardModal } from '../components/doe/DOEWizardModal';
import { useProjectContext } from '../context/ProjectContext';

export const DOEDashboard: React.FC = () => {
  const { projectId, projectCode, projectName } = useProjectContext();
  const [doeList, setDoeList] = useState<DOEResponse[]>([]);
  const [activeDOE, setActiveDOE] = useState<DOEResponse | null>(null);
  const [proposedRuns, setProposedRuns] = useState<ProposedExperiment[]>([]);
  const [activeTab, setActiveTab] = useState<'matrix' | 'analysis'>('matrix');
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDOEs = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await doeService.listProjectDOEs(projectId);
      setDoeList(data);
      setActiveDOE(data.length > 0 ? data[0] : null);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch DOE studies.');
    } finally { setLoading(false); }
  }, [projectId]);

  useEffect(() => {
    fetchDOEs();
  }, [fetchDOEs]);

  const fetchProposedRuns = useCallback(async () => {
    if (!activeDOE) return;
    try {
      const runs = await doeService.listProposedExperiments(activeDOE.id);
      setProposedRuns(runs);
    } catch (err) { console.error('Failed to fetch proposed runs:', err); }
  }, [activeDOE]);

  useEffect(() => {
    fetchProposedRuns();
  }, [fetchProposedRuns]);

  const handleWizardSuccess = async (doeId: string) => {
    await fetchDOEs();
    const created = await doeService.getDOE(doeId);
    setActiveDOE(created);
  };

  return (
    <div className="gs-page">

      {/* Header */}
      <div className="gs-page-header">
        <div>
          <div style={{ marginBottom: 4 }}>
            <span className="gs-badge blue">Phase 14 — Design of Experiments</span>
            <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginLeft: 10 }}>Structured Experimental Exploration</span>
          </div>
          <div className="gs-page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className="gs-page-title-icon amber" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Ruler size={20} />
            </div>
            Design of Experiments (DOE) Studio
          </div>
          <p className="gs-page-subtitle">
            Systematically formulate research questions, select controllable factors &amp; ranges, set constraints, generate seed-reproducible design matrices (Full Factorial, Fractional, CCD, Box-Behnken), approve PROPOSED runs, and analyze main factor effects.
          </p>
        </div>
        <div className="gs-header-actions" style={{ display: 'flex', alignItems: 'flex-end', gap: '16px' }}>
          <div className="gs-field" style={{ margin: 0 }}>
            <label className="gs-label">Assigned Research Project</label>
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
                whiteSpace: 'nowrap',
              }}
            >
              <FolderKanban size={15} />
              <span>{projectCode ? `${projectCode} — ${projectName || projectCode}` : 'Loading project...'}</span>
            </div>
          </div>
          <button
            onClick={() => setIsWizardOpen(true)}
            disabled={!projectId}
            className="gs-btn gs-btn-emerald"
            style={{ padding: '9px 16px', fontWeight: 600, cursor: !projectId ? 'not-allowed' : 'pointer' }}
          >
            + Create New DOE Study
          </button>
        </div>
      </div>

      {error && (
        <div className="gs-alert error" style={{ display: 'flex', gap: 8, alignItems: 'center', margin: '16px 0' }}>
          <AlertTriangle size={18} />
          <div>{error}</div>
        </div>
      )}

      {loading ? (
        <div className="gs-loading-state" style={{ padding: '40px 0', textAlign: 'center' }}>
          <div className="gs-spinner" />
          <div style={{ marginTop: 8, color: 'var(--color-text-secondary)' }}>Loading DOE configurations...</div>
        </div>
      ) : doeList.length === 0 ? (
        <div className="gs-card" style={{ textAlign: 'center', padding: '60px 20px', border: '1px dashed var(--color-border)' }}>
          <Ruler size={48} style={{ color: 'var(--color-text-secondary)', margin: '0 auto 16px auto', opacity: 0.5 }} />
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: 8 }}>No DOE Studies Found</h3>
          <p style={{ color: 'var(--color-text-secondary)', maxWidth: 460, margin: '0 auto 20px auto', fontSize: '0.875rem' }}>
            No Design of Experiments campaigns have been created for this project yet. Use the wizard to configure a factorial or response surface design.
          </p>
          <button onClick={() => setIsWizardOpen(true)} disabled={!projectId} className="gs-btn gs-btn-emerald">
            Create First DOE Campaign
          </button>
        </div>
      ) : (
        <div>
          {/* Active DOE Selector bar */}
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', margin: '16px 0', overflowX: 'auto', paddingBottom: 4 }}>
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-secondary)', flexShrink: 0 }}>
              DOE Campaign:
            </span>
            {doeList.map((doe) => (
              <button
                key={doe.id}
                onClick={() => setActiveDOE(doe)}
                className={`gs-btn ${activeDOE?.id === doe.id ? 'gs-btn-emerald' : 'gs-btn-secondary'}`}
                style={{ fontSize: '0.8125rem', padding: '6px 12px', flexShrink: 0 }}
              >
                {doe.name} ({doe.design_method})
              </button>
            ))}
          </div>

          {activeDOE && (
            <div>
              {/* Campaign summary card */}
              <div className="gs-card" style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span className="gs-badge purple">{activeDOE.design_method}</span>
                      <span className="gs-badge green">{activeDOE.status}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>Seed: {activeDOE.random_seed}</span>
                    </div>
                    <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '4px 0' }}>{activeDOE.name}</h2>
                    {activeDOE.research_question && (
                      <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', margin: '4px 0 0 0' }}>
                        <strong>Question:</strong> {activeDOE.research_question}
                      </p>
                    )}
                  </div>
                  <div style={{ textAlign: 'right', fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                    <div>Requested Runs: <strong>{activeDOE.requested_runs}</strong></div>
                    <div>Center Points: <strong>{activeDOE.center_points}</strong></div>
                    <div>Created: {new Date(activeDOE.created_at).toLocaleDateString()}</div>
                  </div>
                </div>
              </div>

              {/* Tab Navigation */}
              <div className="gs-tabs-header" style={{ display: 'flex', borderBottom: '1px solid var(--color-border)', marginBottom: 16 }}>
                <button
                  onClick={() => setActiveTab('matrix')}
                  className={`gs-tab-btn ${activeTab === 'matrix' ? 'active' : ''}`}
                  style={{
                    padding: '8px 16px',
                    fontWeight: activeTab === 'matrix' ? 600 : 400,
                    borderBottom: activeTab === 'matrix' ? '2px solid var(--color-accent)' : 'none',
                    color: activeTab === 'matrix' ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer'
                  }}
                >
                  Design Matrix &amp; Proposed Runs
                </button>
                <button
                  onClick={() => setActiveTab('analysis')}
                  className={`gs-tab-btn ${activeTab === 'analysis' ? 'active' : ''}`}
                  style={{
                    padding: '8px 16px',
                    fontWeight: activeTab === 'analysis' ? 600 : 400,
                    borderBottom: activeTab === 'analysis' ? '2px solid var(--color-accent)' : 'none',
                    color: activeTab === 'analysis' ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer'
                  }}
                >
                  Factor Effects &amp; Analysis
                </button>
              </div>

              {/* Tab Content */}
              {activeTab === 'matrix' && (
                <DOEDesignMatrixView
                  doe={activeDOE}
                  proposedRuns={proposedRuns}
                  onRefresh={fetchProposedRuns}
                />
              )}

              {activeTab === 'analysis' && (
                <DOEAnalysisView doe={activeDOE} />
              )}
            </div>
          )}
        </div>
      )}

      {/* Wizard Modal */}
      {isWizardOpen && projectId && (
        <DOEWizardModal
          projectId={projectId}
          onClose={() => setIsWizardOpen(false)}
          onSuccess={handleWizardSuccess}
        />
      )}
    </div>
  );
};
