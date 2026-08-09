import React, { useEffect, useState } from 'react';
import { DOEResponse, ProposedExperiment, doeService } from '../services/doeService';
import { DOEDesignMatrixView } from '../components/doe/DOEDesignMatrixView';
import { DOEAnalysisView } from '../components/doe/DOEAnalysisView';
import { DOEWizardModal } from '../components/doe/DOEWizardModal';
import axios from 'axios';

export const DOEDashboard: React.FC = () => {
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [doeList, setDoeList] = useState<DOEResponse[]>([]);
  const [activeDOE, setActiveDOE] = useState<DOEResponse | null>(null);
  const [proposedRuns, setProposedRuns] = useState<ProposedExperiment[]>([]);
  const [activeTab, setActiveTab] = useState<'matrix' | 'analysis'>('matrix');
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await axios.get('http://127.0.0.1:8000/api/v1/projects');
        setProjects(res.data);
        if (res.data.length > 0) setSelectedProjectId(res.data[0].id);
      } catch (err) { console.error('Failed to fetch projects:', err); }
    };
    fetchProjects();
  }, []);

  const fetchDOEs = async () => {
    if (!selectedProjectId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await doeService.listProjectDOEs(selectedProjectId);
      setDoeList(data);
      setActiveDOE(data.length > 0 ? data[0] : null);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch DOE studies.');
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchDOEs(); }, [selectedProjectId]);

  const fetchProposedRuns = async () => {
    if (!activeDOE) return;
    try {
      const runs = await doeService.listProposedExperiments(activeDOE.id);
      setProposedRuns(runs);
    } catch (err) { console.error('Failed to fetch proposed runs:', err); }
  };

  useEffect(() => { fetchProposedRuns(); }, [activeDOE?.id]);

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
          <div className="gs-page-title">
            <div className="gs-page-title-icon amber">📐</div>
            Design of Experiments (DOE) Studio
          </div>
          <p className="gs-page-subtitle">
            Systematically formulate research questions, select controllable factors &amp; ranges, set constraints, generate seed-reproducible design matrices (Full Factorial, Fractional, CCD, Box-Behnken), approve PROPOSED runs, and analyze main factor effects.
          </p>
        </div>
        <div className="gs-header-actions">
          <div className="gs-field">
            <label className="gs-label">Select Active Project</label>
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
          <button
            onClick={() => setIsWizardOpen(true)}
            className="gs-btn gs-btn-emerald"
          >
            + Create New DOE Study
          </button>
        </div>
      </div>

      {error && <div className="gs-alert error">⚠️ {error}</div>}

      {/* Main layout: sidebar + content */}
      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 20, alignItems: 'start' }}>

        {/* Sidebar: DOE List */}
        <div className="gs-panel">
          <div className="gs-panel-header">
            <span className="gs-panel-title">Project DOE Studies ({doeList.length})</span>
          </div>
          <div className="gs-panel-body" style={{ padding: '12px' }}>
            {loading ? (
              <div className="gs-loading" style={{ padding: '20px 0' }}>
                <div className="gs-spinner" /> Loading…
              </div>
            ) : doeList.length === 0 ? (
              <div className="gs-empty" style={{ padding: '24px 0' }}>
                <div className="gs-empty-icon" style={{ fontSize: '2rem' }}>📐</div>
                <div className="gs-empty-text">No DOE studies created yet for this project.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {doeList.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => setActiveDOE(d)}
                    style={{
                      width: '100%',
                      padding: '12px',
                      borderRadius: 'var(--radius-lg)',
                      border: activeDOE?.id === d.id ? '2px solid #0d9488' : '1px solid var(--color-border)',
                      background: activeDOE?.id === d.id ? '#f0fdf4' : 'var(--color-surface)',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all var(--transition)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontWeight: 600, fontSize: '0.8125rem', color: 'var(--color-text)' }}>{d.name}</span>
                      <span className="gs-badge teal">{d.version}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: '#4f46e5', fontWeight: 600 }}>{d.design_method}</span>
                      <span style={{ color: '#b45309', fontWeight: 600 }}>{d.requested_runs} runs</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Main panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {activeDOE ? (
            <>
              {/* Tabs */}
              <div style={{ display: 'flex', gap: 8, borderBottom: '2px solid var(--color-border)', paddingBottom: 2 }}>
                {[
                  { key: 'matrix', label: `🧪 Design Matrix Runs (${proposedRuns.length})` },
                  { key: 'analysis', label: '📊 Statistical Effect & Response Surface' },
                ].map(({ key, label }) => (
                  <button
                    key={key}
                    onClick={() => setActiveTab(key as any)}
                    className="gs-btn"
                    style={{
                      background: activeTab === key ? 'var(--color-primary)' : 'transparent',
                      color: activeTab === key ? 'white' : 'var(--color-text-secondary)',
                      border: activeTab === key ? 'none' : '1px solid transparent',
                      marginBottom: -2,
                      borderBottom: activeTab === key ? '2px solid var(--color-primary)' : '2px solid transparent',
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {activeTab === 'matrix' && (
                <DOEDesignMatrixView doe={activeDOE} proposedRuns={proposedRuns} onRefresh={fetchProposedRuns} />
              )}
              {activeTab === 'analysis' && <DOEAnalysisView doe={activeDOE} />}
            </>
          ) : (
            <div className="gs-panel">
              <div className="gs-empty" style={{ padding: '80px 40px' }}>
                <div className="gs-empty-icon">🧪</div>
                <div className="gs-empty-title">No Active DOE Study Selected</div>
                <div className="gs-empty-text">
                  Create a new DOE study using the configurator wizard to generate structured experimental conditions.
                </div>
                <button
                  onClick={() => setIsWizardOpen(true)}
                  className="gs-btn gs-btn-emerald"
                  style={{ marginTop: 20 }}
                >
                  + Create First DOE Study
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {selectedProjectId && (
        <DOEWizardModal
          projectId={selectedProjectId}
          isOpen={isWizardOpen}
          onClose={() => setIsWizardOpen(false)}
          onSuccess={handleWizardSuccess}
        />
      )}
    </div>
  );
};
