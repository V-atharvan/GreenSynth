import React, { useEffect, useState } from 'react';
import { DOEAnalysisResponse, DOEResponse, doeService } from '../../services/doeService';

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
    <div className="space-y-6">
      {/* Target Selector & Status */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex justify-between items-center text-slate-100">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">DOE Factor Effects & Response Surface Fit</h3>
          <p className="text-xs text-slate-400 mt-0.5">Statistical estimation of main factor effects and interaction models</p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 uppercase font-semibold">Response Property:</label>
          <select
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-medium"
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
        <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-200 rounded-lg text-xs">
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading && (
        <div className="p-8 text-center text-slate-400 text-xs animate-pulse">
          Computing Main Effects & Polynomial Response Surface Regression...
        </div>
      )}

      {analysis && !loading && (
        <div className="space-y-6">
          {/* Main Effects SVG Visualization */}
          <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-4 shadow-lg">
            <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
              <span>📈</span> Factor Main Effects Plot (E_A = Y_high - Y_low)
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {mainEffectsKeys.map((key) => {
                const item = analysis.main_effects[key];
                const effect = item.estimated_main_effect;
                const isPos = effect >= 0;
                return (
                  <div key={key} className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-200 capitalize">{key.replace('_', ' ')}</span>
                      <span
                        className={`text-xs font-extrabold font-mono px-2 py-0.5 rounded ${
                          isPos
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : 'bg-rose-950 text-rose-300 border border-rose-800'
                        }`}
                      >
                        {isPos ? `+${effect}` : effect}
                      </span>
                    </div>

                    {/* SVG Effect Bar */}
                    <div className="h-16 bg-slate-900 rounded-lg p-2 relative flex items-center justify-center border border-slate-800">
                      <svg className="w-full h-full" viewBox="0 0 200 40">
                        {/* Zero Line */}
                        <line x1="100" y1="5" x2="100" y2="35" stroke="#475569" strokeDasharray="3 3" strokeWidth="1.5" />
                        {/* Bar */}
                        {isPos ? (
                          <rect
                            x="100"
                            y="12"
                            width={Math.min(Math.abs(effect) * 20, 85)}
                            height="16"
                            fill="#10b981"
                            rx="3"
                          />
                        ) : (
                          <rect
                            x={100 - Math.min(Math.abs(effect) * 20, 85)}
                            y="12"
                            width={Math.min(Math.abs(effect) * 20, 85)}
                            height="16"
                            fill="#f43f5e"
                            rx="3"
                          />
                        )}
                      </svg>
                    </div>

                    <div className="text-[10px] text-slate-400 flex justify-between">
                      <span>Observed count: {item.n_observations}</span>
                      <span>Level Means: {Object.keys(item.level_means).length} levels</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Response Surface Fit Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-center">
              <div className="text-xs text-slate-400 uppercase font-medium">Sample Size (n)</div>
              <div className="text-xl font-extrabold text-white mt-1 font-mono">{analysis.sample_count}</div>
            </div>
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-center">
              <div className="text-xs text-slate-400 uppercase font-medium">R² Fit Metric</div>
              <div className="text-xl font-extrabold text-emerald-400 mt-1 font-mono">
                {analysis.fit_metrics.r2 !== undefined && analysis.fit_metrics.r2 !== null
                  ? analysis.fit_metrics.r2
                  : 'N/A'}
              </div>
            </div>
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-center">
              <div className="text-xs text-slate-400 uppercase font-medium">Adjusted R²</div>
              <div className="text-xl font-extrabold text-indigo-400 mt-1 font-mono">
                {analysis.fit_metrics.adjusted_r2 !== undefined && analysis.fit_metrics.adjusted_r2 !== null
                  ? analysis.fit_metrics.adjusted_r2
                  : 'N/A'}
              </div>
            </div>
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-center">
              <div className="text-xs text-slate-400 uppercase font-medium">RMSE Residual Error</div>
              <div className="text-xl font-extrabold text-amber-400 mt-1 font-mono">
                {analysis.fit_metrics.rmse !== undefined && analysis.fit_metrics.rmse !== null
                  ? analysis.fit_metrics.rmse
                  : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
