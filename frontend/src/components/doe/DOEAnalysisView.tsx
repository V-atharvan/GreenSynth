/**
 * GreenSynth Analytics — DOE Factor Effects & Response Surface View Component
 * Theme-aligned light-mode UI/UX for statistical main effects and response surface fit metrics.
 */

import React, { useEffect, useState } from 'react';
import { DOEAnalysisResponse, DOEResponse, doeService } from '../../services/doeService';
import { BarChart3, Info, AlertTriangle, Layers } from 'lucide-react';

interface DOEAnalysisViewProps {
  doe: DOEResponse;
}

export const DOEAnalysisView: React.FC<DOEAnalysisViewProps> = ({ doe }) => {
  const [targetProperty, setTargetProperty] = useState<string>('Electrical Conductivity');
  const [analysis, setAnalysis] = useState<DOEAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await doeService.analyzeDOE(doe.id, targetProperty);
      setAnalysis(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to compute DOE analysis.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalysis();
  }, [doe.id, targetProperty]);

  const mainEffectsKeys = analysis?.main_effects ? Object.keys(analysis.main_effects) : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Target Selector & Header Banner */}
      <div
        className="gs-panel"
        style={{
          padding: '18px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 16,
          background: '#ffffff',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-bg)',
              color: 'var(--color-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid var(--color-border)',
            }}
          >
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--color-text)' }}>
              DOE Factor Main Effects &amp; Response Surface Fit
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', margin: '2px 0 0 0' }}>
              Statistical estimation of main factor effects and response surface models for {doe.name}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <label className="form-label" style={{ fontSize: '0.8125rem', fontWeight: 600, margin: 0 }}>
            Response Property:
          </label>
          <select
            className="form-control"
            style={{ width: 'auto', fontSize: '0.8125rem', fontWeight: 600, padding: '6px 12px' }}
            value={targetProperty}
            onChange={(e) => setTargetProperty(e.target.value)}
          >
            <option value="Electrical Conductivity">Electrical Conductivity (S/cm)</option>
            <option value="Band Gap">Band Gap (eV)</option>
            <option value="Crystallite Size">Crystallite Size (nm)</option>
          </select>
        </div>
      </div>

      {error && (
        <div
          style={{
            padding: '12px 16px',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#991b1b',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <AlertTriangle className="w-4 h-4" />
          <span><strong>Error:</strong> {error}</span>
        </div>
      )}

      {loading && (
        <div className="gs-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
          Computing main factor effects &amp; response surface regression model...
        </div>
      )}

      {analysis && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Main Effects Plot */}
          <div
            className="gs-panel"
            style={{
              padding: 24,
              background: '#ffffff',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border)',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--color-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0, display: 'flex', alignItems: 'center', gap: 6 }}>
                <span>📈</span> Factor Main Effects Plot (E_A = Y_high - Y_low)
              </h4>
              <span className="badge badge-planned font-mono">
                Sample Size N = {analysis.sample_count}
              </span>
            </div>

            {mainEffectsKeys.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
                {mainEffectsKeys.map((key) => {
                  const item = analysis.main_effects[key];
                  const effect = item.estimated_main_effect;
                  const isPos = effect >= 0;
                  return (
                    <div
                      key={key}
                      style={{
                        background: 'var(--color-bg)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 'var(--radius-md)',
                        padding: 16,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 12,
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.875rem', fontWeight: 600, textTransform: 'capitalize', color: 'var(--color-text)' }}>
                          {key.replace(/_/g, ' ')}
                        </span>
                        <span
                          className={`badge ${isPos ? 'badge-completed' : 'badge-failed'}`}
                          style={{ fontFamily: 'monospace', fontWeight: 700 }}
                        >
                          {isPos ? `+${effect}` : effect}
                        </span>
                      </div>

                      {/* SVG Bar Representation */}
                      <div
                        style={{
                          height: 44,
                          background: '#ffffff',
                          borderRadius: 'var(--radius-sm)',
                          border: '1px solid var(--color-border-light)',
                          padding: '4px 8px',
                          position: 'relative',
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        <svg className="w-full h-full" viewBox="0 0 200 40">
                          <line x1="100" y1="4" x2="100" y2="36" stroke="var(--color-border-dark)" strokeDasharray="3 3" strokeWidth="1.5" />
                          {isPos ? (
                            <rect
                              x="100"
                              y="12"
                              width={Math.min(Math.abs(effect) * 20, 85)}
                              height="16"
                              fill="var(--color-success)"
                              rx="3"
                            />
                          ) : (
                            <rect
                              x={100 - Math.min(Math.abs(effect) * 20, 85)}
                              y="12"
                              width={Math.min(Math.abs(effect) * 20, 85)}
                              height="16"
                              fill="var(--color-danger)"
                              rx="3"
                            />
                          )}
                        </svg>
                      </div>

                      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                        <span>Observations: {item.n_observations}</span>
                        <span>Level Means: {Object.keys(item.level_means).length}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-secondary)', background: 'var(--color-bg)', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
                <Info className="w-5 h-5 mx-auto mb-2 text-slate-400" />
                No measured response data recorded yet for {targetProperty}. Complete proposed DOE experiments to calculate factor main effects.
              </div>
            )}
          </div>

          {/* Response Surface Fit Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
            <div style={{ background: '#ffffff', padding: 16, borderRadius: 'var(--radius-lg)', border: '1px solid var(--color-border)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Sample Size (n)
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, marginTop: 4, fontFamily: 'monospace', color: 'var(--color-text)' }}>
                {analysis.sample_count}
              </div>
            </div>

            <div style={{ background: '#ffffff', padding: 16, borderRadius: 'var(--radius-lg)', border: '1px solid var(--color-border)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
                R² Fit Metric
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, marginTop: 4, fontFamily: 'monospace', color: 'var(--color-primary)' }}>
                {analysis.fit_metrics.r2 !== undefined && analysis.fit_metrics.r2 !== null ? analysis.fit_metrics.r2 : 'N/A'}
              </div>
            </div>

            <div style={{ background: '#ffffff', padding: 16, borderRadius: 'var(--radius-lg)', border: '1px solid var(--color-border)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Adjusted R²
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, marginTop: 4, fontFamily: 'monospace', color: '#4f46e5' }}>
                {analysis.fit_metrics.adjusted_r2 !== undefined && analysis.fit_metrics.adjusted_r2 !== null ? analysis.fit_metrics.adjusted_r2 : 'N/A'}
              </div>
            </div>

            <div style={{ background: '#ffffff', padding: 16, borderRadius: 'var(--radius-lg)', border: '1px solid var(--color-border)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
                RMSE Residual Error
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, marginTop: 4, fontFamily: 'monospace', color: '#d97706' }}>
                {analysis.fit_metrics.rmse !== undefined && analysis.fit_metrics.rmse !== null ? analysis.fit_metrics.rmse : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
