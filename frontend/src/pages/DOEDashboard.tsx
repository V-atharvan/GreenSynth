import React, { useEffect, useState, useCallback } from 'react';
import { Ruler, AlertTriangle, FolderKanban, FlaskConical, BarChart3, Table, Plus } from 'lucide-react';
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
      if (data.length > 0) {
        setActiveDOE((prev) => {
          if (!prev) return data[0];
          const match = data.find((d) => d.id === prev.id);
          return match || data[0];
        });
      } else {
        setActiveDOE(null);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch DOE studies.');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchDOEs();
  }, [fetchDOEs]);

  const fetchProposedRuns = useCallback(async () => {
    if (!activeDOE) return;
    try {
      const runs = await doeService.listProposedExperiments(activeDOE.id);
      setProposedRuns(runs);
    } catch (err) {
      console.error('Failed to fetch proposed runs:', err);
    }
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
      {/* Page Header */}
      <div className="gs-page-header" style={{ marginBottom: 20 }}>
        <div>
          <div style={{ marginBottom: 4 }}>
            <span className="gs-badge blue">Phase 14 — Design of Experiments</span>
            <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginLeft: 10 }}>
              Structured Experimental Exploration
            </span>
          </div>
          <div className="gs-page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className="gs-page-title-icon amber" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Ruler size={20} />
            </div>
            Design of Experiments (DOE) Studio
          </div>
          <p className="gs-page-subtitle" style={{ maxWidth: 780 }}>
            Systematically formulate research questions, select controllable factors &amp; ranges, set constraints, generate seed-reproducible design matrices (Full Factorial, Fractional, CCD, Box-Behnken), approve PROPOSED runs, and analyze main factor effects.
          </p>
        </div>

        <div className="gs-header-actions" style={{ display: 'flex', alignItems: 'flex-end', gap: '14px', flexWrap: 'wrap' }}>
          <div className="gs-field" style={{ margin: 0 }}>
            <label className="gs-label" style={{ fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Assigned Research Project
            </label>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                background: '#f8fafc',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 600,
                color: '#0f766e',
                maxWidth: '380px',
              }}
              title={projectCode ? `${projectCode} — ${projectName || projectCode}` : ''}
            >
              <FolderKanban size={15} style={{ flexShrink: 0 }} />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {projectCode ? `${projectCode} — ${projectName || projectCode}` : 'Loading project...'}
              </span>
            </div>
          </div>
          <button
            onClick={() => setIsWizardOpen(true)}
            disabled={!projectId}
            className="gs-btn gs-btn-emerald"
            style={{ padding: '8px 16px', fontWeight: 600, cursor: !projectId ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <Plus size={16} />
            <span>Create New DOE Study</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="gs-alert error" style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 16 }}>
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Active DOE Selector Bar */}
          <div
            className="gs-panel"
            style={{
              padding: '10px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 10,
              background: '#ffffff',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-lg)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                <FlaskConical size={14} /> Campaign:
              </span>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                {doeList.map((doe, idx) => {
                  const isActive = activeDOE?.id === doe.id;
                  return (
                    <button
                      key={doe.id}
                      onClick={() => setActiveDOE(doe)}
                      className={`gs-btn ${isActive ? 'gs-btn-emerald' : 'gs-btn-secondary'}`}
                      style={{
                        fontSize: '0.8125rem',
                        padding: '5px 12px',
                        borderRadius: '20px',
                        fontWeight: isActive ? 600 : 500,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        maxWidth: '320px',
                      }}
                      title={`${doe.name} (${doe.design_method}, v${doe.version})`}
                    >
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {doe.name}
                      </span>
                      <span style={{ opacity: 0.75, fontSize: '0.6875rem' }}>
                        #{idx + 1}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
              Showing {activeDOE ? activeDOE.name : ''}
            </div>
          </div>

          {activeDOE && (
            <div>
              {/* Unified Study Overview Card */}
              <div
                className="gs-card"
                style={{
                  marginBottom: 16,
                  padding: '18px 22px',
                  background: '#ffffff',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-lg)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
                  <div style={{ flex: 1, minWidth: '320px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
                      <span className="gs-badge purple" style={{ fontSize: '0.6875rem', fontWeight: 600 }}>
                        {activeDOE.design_method}
                      </span>
                      <span className="gs-badge teal" style={{ fontSize: '0.6875rem', fontWeight: 600 }}>
                        {activeDOE.version.toLowerCase().startsWith('v') ? activeDOE.version : `v${activeDOE.version}`}
                      </span>
                      <span className={`gs-chip ${activeDOE.status === 'APPROVED' ? 'stable' : 'warning'}`} style={{ fontSize: '0.6875rem' }}>
                        {activeDOE.status}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}>
                        Random Seed: {activeDOE.random_seed}
                      </span>
                    </div>
                    <h2 style={{ fontSize: '1.1875rem', fontWeight: 700, margin: '2px 0 8px 0', color: 'var(--color-text)' }}>
                      {activeDOE.name}
                    </h2>
                    {activeDOE.research_question && (
                      <div
                        style={{
                          fontSize: '0.8125rem',
                          color: '#1e293b',
                          background: '#f8fafc',
                          borderLeft: '3px solid #0f766e',
                          padding: '8px 12px',
                          borderRadius: '0 6px 6px 0',
                          lineHeight: 1.4,
                        }}
                      >
                        <strong style={{ color: '#0f766e' }}>Research Question:</strong> {activeDOE.research_question}
                      </div>
                    )}
                  </div>

                  {/* Summary KPI Badges */}
                  <div
                    style={{
                      display: 'flex',
                      gap: 16,
                      alignItems: 'center',
                      background: '#f8fafc',
                      padding: '10px 16px',
                      borderRadius: '8px',
                      border: '1px solid var(--color-border-light)',
                    }}
                  >
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.6875rem', textTransform: 'uppercase', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                        Requested Runs
                      </div>
                      <div style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-text)', fontFamily: 'var(--font-mono)' }}>
                        {activeDOE.requested_runs}
                      </div>
                    </div>
                    <div style={{ width: 1, height: 28, background: 'var(--color-border)' }} />
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.6875rem', textTransform: 'uppercase', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                        Center Points
                      </div>
                      <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#4f46e5', fontFamily: 'var(--font-mono)' }}>
                        {activeDOE.center_points}
                      </div>
                    </div>
                    <div style={{ width: 1, height: 28, background: 'var(--color-border)' }} />
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.6875rem', textTransform: 'uppercase', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                        Created Date
                      </div>
                      <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)', marginTop: 2 }}>
                        {new Date(activeDOE.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tab Navigation */}
              <div
                className="gs-tabs-header"
                style={{
                  display: 'flex',
                  gap: 8,
                  borderBottom: '1px solid var(--color-border)',
                  marginBottom: 16,
                  paddingBottom: 2,
                }}
              >
                <button
                  onClick={() => setActiveTab('matrix')}
                  className={`gs-tab-btn ${activeTab === 'matrix' ? 'active' : ''}`}
                  style={{
                    padding: '8px 16px',
                    fontWeight: activeTab === 'matrix' ? 700 : 500,
                    fontSize: '0.875rem',
                    borderBottom: activeTab === 'matrix' ? '3px solid #0f766e' : '3px solid transparent',
                    color: activeTab === 'matrix' ? '#0f766e' : 'var(--color-text-secondary)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <Table size={15} />
                  <span>Design Matrix &amp; Proposed Runs</span>
                  <span
                    style={{
                      background: activeTab === 'matrix' ? '#ccfbf1' : 'var(--color-bg)',
                      color: activeTab === 'matrix' ? '#0f766e' : 'var(--color-text-secondary)',
                      fontSize: '0.6875rem',
                      fontWeight: 700,
                      padding: '2px 7px',
                      borderRadius: '10px',
                    }}
                  >
                    {proposedRuns.length}
                  </span>
                </button>
                <button
                  onClick={() => setActiveTab('analysis')}
                  className={`gs-tab-btn ${activeTab === 'analysis' ? 'active' : ''}`}
                  style={{
                    padding: '8px 16px',
                    fontWeight: activeTab === 'analysis' ? 700 : 500,
                    fontSize: '0.875rem',
                    borderBottom: activeTab === 'analysis' ? '3px solid #0f766e' : '3px solid transparent',
                    color: activeTab === 'analysis' ? '#0f766e' : 'var(--color-text-secondary)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <BarChart3 size={15} />
                  <span>Factor Effects &amp; Analysis</span>
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
