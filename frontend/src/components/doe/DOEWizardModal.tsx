import React, { useState } from 'react';
import {
  DOECreateInput,
  DOEWorkloadPreview,
  FactorDefinition,
  ResponseDefinition,
  DOEConstraint,
  doeService,
} from '../../services/doeService';

interface DOEWizardModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (doeId: string) => void;
}

export const DOEWizardModal: React.FC<DOEWizardModalProps> = ({
  projectId,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [step, setStep] = useState<number>(1);
  const [name, setName] = useState('Spray Pyrolysis Factorial Study (CuO Thin Films)');
  const [description, setDescription] = useState(
    'Factorial study investigating substrate temperature, spray rate, and precursor concentration for Mulberry-synthesized CuO thin films.'
  );
  const [researchQuestion, setResearchQuestion] = useState(
    'How do substrate temperature and spray rate interact to determine the electrical conductivity and optical band gap of CuO thin films?'
  );
  const [designMethod, setDesignMethod] = useState('FULL_FACTORIAL');
  const [requestedRuns, setRequestedRuns] = useState(8);
  const [replicates, setReplicates] = useState(1);
  const [centerPoints, setCenterPoints] = useState(0);
  const [randomSeed, setRandomSeed] = useState(42);
  const [randomizeRunOrder, setRandomizeRunOrder] = useState(true);

  // Factors
  const [factors, setFactors] = useState<FactorDefinition[]>([
    {
      parameter_code: 'substrate_temperature',
      name: 'Substrate Temperature',
      factor_type: 'CONTINUOUS',
      role: 'CONTROLLABLE',
      lower_bound: 300,
      upper_bound: 400,
      center_value: 350,
      unit: '°C',
      levels: 2,
    },
    {
      parameter_code: 'spray_rate',
      name: 'Spray Rate',
      factor_type: 'CONTINUOUS',
      role: 'CONTROLLABLE',
      lower_bound: 2.0,
      upper_bound: 5.0,
      center_value: 3.5,
      unit: 'mL/min',
      levels: 2,
    },
    {
      parameter_code: 'precursor_concentration',
      name: 'Precursor Concentration',
      factor_type: 'CONTINUOUS',
      role: 'CONTROLLABLE',
      lower_bound: 0.05,
      upper_bound: 0.15,
      center_value: 0.1,
      unit: 'M',
      levels: 2,
    },
  ]);

  // Responses
  const [responses, setResponses] = useState<ResponseDefinition[]>([
    {
      property_name: 'Electrical Conductivity',
      unit: 'S/cm',
      direction: 'MAXIMIZE',
      weight: 1.0,
    },
    {
      property_name: 'Band Gap',
      unit: 'eV',
      direction: 'TARGET',
      target: 1.5,
      weight: 0.8,
    },
  ]);

  // Constraints
  const [constraints, setConstraints] = useState<DOEConstraint[]>([
    {
      parameter_code: 'substrate_temperature',
      operator: '>=',
      value: 250,
      unit: '°C',
    },
  ]);

  const [preview, setPreview] = useState<DOEWorkloadPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleAddFactor = () => {
    setFactors([
      ...factors,
      {
        parameter_code: `factor_${factors.length + 1}`,
        name: `New Factor ${factors.length + 1}`,
        factor_type: 'CONTINUOUS',
        role: 'CONTROLLABLE',
        lower_bound: 10,
        upper_bound: 100,
        center_value: 55,
        unit: 'units',
        levels: 2,
      },
    ]);
  };

  const handleUpdateFactor = (index: number, field: keyof FactorDefinition, value: any) => {
    const updated = [...factors];
    updated[index] = { ...updated[index], [field]: value };
    setFactors(updated);
  };

  const handleRemoveFactor = (index: number) => {
    setFactors(factors.filter((_, i) => i !== index));
  };

  const handleCalculatePreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload: DOECreateInput = {
        project_id: projectId,
        name,
        description,
        research_question: researchQuestion,
        design_method: designMethod,
        factors,
        responses,
        constraints,
        requested_runs: requestedRuns,
        replicates,
        center_points: centerPoints,
        random_seed: randomSeed,
        randomize_run_order: randomizeRunOrder,
      };
      const res = await doeService.previewWorkload(payload);
      setPreview(res);
      setStep(4);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to calculate workload preview.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDOE = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload: DOECreateInput = {
        project_id: projectId,
        name,
        description,
        research_question: researchQuestion,
        design_method: designMethod,
        factors,
        responses,
        constraints,
        requested_runs: requestedRuns,
        replicates,
        center_points: centerPoints,
        random_seed: randomSeed,
        randomize_run_order: randomizeRunOrder,
      };
      const result = await doeService.createDOEAndGenerate(payload);
      onSuccess(result.doe.id);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to generate DOE design.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col text-slate-100 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/80">
          <div>
            <div className="text-xs uppercase tracking-wider text-emerald-400 font-semibold">Phase 14 — Design of Experiments</div>
            <h2 className="text-xl font-bold text-white">DOE Study Configurator & Matrix Generator</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-2xl font-bold">
            &times;
          </button>
        </div>

        {/* Wizard Steps Navigation */}
        <div className="px-6 py-3 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between text-xs">
          <div className={`flex items-center gap-2 ${step >= 1 ? 'text-emerald-400 font-semibold' : 'text-slate-500'}`}>
            <span className="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">1</span>
            1. Study & Research Question
          </div>
          <div className="text-slate-700">&rarr;</div>
          <div className={`flex items-center gap-2 ${step >= 2 ? 'text-emerald-400 font-semibold' : 'text-slate-500'}`}>
            <span className="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">2</span>
            2. Factors & Ranges
          </div>
          <div className="text-slate-700">&rarr;</div>
          <div className={`flex items-center gap-2 ${step >= 3 ? 'text-emerald-400 font-semibold' : 'text-slate-500'}`}>
            <span className="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">3</span>
            3. Method & Parameters
          </div>
          <div className="text-slate-700">&rarr;</div>
          <div className={`flex items-center gap-2 ${step >= 4 ? 'text-emerald-400 font-semibold' : 'text-slate-500'}`}>
            <span className="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">4</span>
            4. Preview & Generate
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mx-6 mt-4 p-3 bg-rose-950/80 border border-rose-800 text-rose-200 rounded-lg text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Body Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* STEP 1: Study Info & Research Question */}
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">DOE Study Name</label>
                <input
                  type="text"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Research Question</label>
                <textarea
                  rows={2}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
                  value={researchQuestion}
                  onChange={(e) => setResearchQuestion(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Study Description & Objectives</label>
                <textarea
                  rows={2}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
            </div>
          )}

          {/* STEP 2: Controllable Factors & Ranges */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Controllable Experimental Factors ({factors.length})</h3>
                <button
                  onClick={handleAddFactor}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium"
                >
                  + Add Factor
                </button>
              </div>

              <div className="space-y-3">
                {factors.map((f, idx) => (
                  <div key={idx} className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
                    <div className="grid grid-cols-12 gap-3 items-center">
                      <div className="col-span-3">
                        <label className="block text-[10px] text-slate-400 uppercase">Parameter Code</label>
                        <input
                          type="text"
                          className="w-full bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-white"
                          value={f.parameter_code}
                          onChange={(e) => handleUpdateFactor(idx, 'parameter_code', e.target.value)}
                        />
                      </div>
                      <div className="col-span-4">
                        <label className="block text-[10px] text-slate-400 uppercase">Factor Name</label>
                        <input
                          type="text"
                          className="w-full bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-white"
                          value={f.name}
                          onChange={(e) => handleUpdateFactor(idx, 'name', e.target.value)}
                        />
                      </div>
                      <div className="col-span-2">
                        <label className="block text-[10px] text-slate-400 uppercase">Type</label>
                        <select
                          className="w-full bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-white"
                          value={f.factor_type}
                          onChange={(e) => handleUpdateFactor(idx, 'factor_type', e.target.value)}
                        >
                          <option value="CONTINUOUS">Continuous</option>
                          <option value="CATEGORICAL">Categorical</option>
                          <option value="DISCRETE">Discrete</option>
                        </select>
                      </div>
                      <div className="col-span-2">
                        <label className="block text-[10px] text-slate-400 uppercase">Unit</label>
                        <input
                          type="text"
                          className="w-full bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-white"
                          value={f.unit || ''}
                          onChange={(e) => handleUpdateFactor(idx, 'unit', e.target.value)}
                        />
                      </div>
                      <div className="col-span-1 text-right">
                        <button
                          onClick={() => handleRemoveFactor(idx)}
                          className="text-rose-400 hover:text-rose-300 text-xs font-bold"
                        >
                          &times;
                        </button>
                      </div>
                    </div>

                    {f.factor_type === 'CONTINUOUS' && (
                      <div className="grid grid-cols-3 gap-3 pt-2 border-t border-slate-900 text-xs">
                        <div>
                          <label className="text-[10px] text-slate-400">Lower Bound</label>
                          <input
                            type="number"
                            step="any"
                            className="w-full bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-white"
                            value={f.lower_bound ?? ''}
                            onChange={(e) => handleUpdateFactor(idx, 'lower_bound', parseFloat(e.target.value))}
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-400">Upper Bound</label>
                          <input
                            type="number"
                            step="any"
                            className="w-full bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-white"
                            value={f.upper_bound ?? ''}
                            onChange={(e) => handleUpdateFactor(idx, 'upper_bound', parseFloat(e.target.value))}
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-400">Levels Count</label>
                          <input
                            type="number"
                            className="w-full bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-white"
                            value={typeof f.levels === 'number' ? f.levels : 2}
                            onChange={(e) => handleUpdateFactor(idx, 'levels', parseInt(e.target.value))}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 3: DOE Method & Parameters */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Design Method</label>
                  <select
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
                    value={designMethod}
                    onChange={(e) => setDesignMethod(e.target.value)}
                  >
                    <option value="FULL_FACTORIAL">Full Factorial (2^k or 3^k)</option>
                    <option value="FRACTIONAL_FACTORIAL">Fractional Factorial (2^(k-1))</option>
                    <option value="CENTRAL_COMPOSITE">Central Composite Design (CCD)</option>
                    <option value="BOX_BEHNKEN">Box-Behnken Design</option>
                    <option value="RANDOMIZED_CANDIDATE">Randomized Candidate Design</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Replicate Runs</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
                    value={replicates}
                    onChange={(e) => setReplicates(parseInt(e.target.value))}
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Center Points Count</label>
                  <input
                    type="number"
                    min={0}
                    max={10}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
                    value={centerPoints}
                    onChange={(e) => setCenterPoints(parseInt(e.target.value))}
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Random Seed (Reproducibility)</label>
                  <input
                    type="number"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
                    value={randomSeed}
                    onChange={(e) => setRandomSeed(parseInt(e.target.value))}
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-slate-950 border border-slate-800 rounded-lg">
                <input
                  type="checkbox"
                  id="randomizeRunOrder"
                  checked={randomizeRunOrder}
                  onChange={(e) => setRandomizeRunOrder(e.target.checked)}
                  className="rounded bg-slate-900 border-slate-700 text-emerald-500"
                />
                <label htmlFor="randomizeRunOrder" className="text-xs text-slate-200 cursor-pointer">
                  Randomize run execution order using random seed
                </label>
              </div>
            </div>
          )}

          {/* STEP 4: Workload Preview & Quality Report */}
          {step === 4 && preview && (
            <div className="space-y-4">
              <div className="p-4 bg-slate-950 border border-emerald-950/80 rounded-xl space-y-3">
                <h3 className="text-sm font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                  <span>🧪</span> Workload Calculation & Design Resolution
                </h3>

                <div className="grid grid-cols-4 gap-4 text-center">
                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                    <div className="text-xs text-slate-400">Design Method</div>
                    <div className="text-sm font-bold text-white mt-0.5">{preview.design_method}</div>
                  </div>
                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                    <div className="text-xs text-slate-400">Base Runs</div>
                    <div className="text-sm font-bold text-emerald-400 mt-0.5">{preview.base_runs}</div>
                  </div>
                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                    <div className="text-xs text-slate-400">Replicates</div>
                    <div className="text-sm font-bold text-indigo-400 mt-0.5">&times; {preview.replicates}</div>
                  </div>
                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                    <div className="text-xs text-slate-400">Total Runs</div>
                    <div className="text-base font-extrabold text-amber-400 mt-0.5">{preview.total_runs}</div>
                  </div>
                </div>

                {preview.design_resolution && (
                  <div className="text-xs text-slate-300">
                    <strong>Design Resolution:</strong>{' '}
                    <span className="px-2 py-0.5 bg-emerald-950 text-emerald-300 rounded border border-emerald-800 font-mono">
                      {preview.design_resolution}
                    </span>
                  </div>
                )}

                {preview.requires_workload_warning && (
                  <div className="p-3 bg-amber-950/80 border border-amber-800 text-amber-200 rounded-lg text-xs flex items-center gap-2">
                    <span className="text-lg">⚠️</span>
                    <div>
                      <strong>Experimental Workload Warning:</strong> {preview.warning_message}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer Controls */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/80 flex justify-between items-center">
          {step > 1 ? (
            <button
              onClick={() => setStep(step - 1)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold"
            >
              &larr; Back
            </button>
          ) : (
            <div />
          )}

          {step < 3 && (
            <button
              onClick={() => setStep(step + 1)}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold"
            >
              Next Step &rarr;
            </button>
          )}

          {step === 3 && (
            <button
              onClick={handleCalculatePreview}
              disabled={loading}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold disabled:opacity-50"
            >
              {loading ? 'Calculating...' : 'Preview Workload & Design Matrix &rarr;'}
            </button>
          )}

          {step === 4 && (
            <button
              onClick={handleGenerateDOE}
              disabled={loading}
              className="px-6 py-2.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-bold tracking-wider uppercase shadow-lg shadow-amber-900/40 disabled:opacity-50"
            >
              {loading ? 'Generating Design Matrix...' : '🚀 Generate Proposed Design Matrix'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
