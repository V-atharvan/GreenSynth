/**
 * GreenSynth Analytics — Design of Experiments (DOE) Wizard Modal
 * Uses GreenSynth native CSS design system (modal-overlay, modal, modal-header, modal-body, modal-footer, form-control).
 */

import React, { useState } from 'react';
import { X } from 'lucide-react';
import { doeService, FactorDefinition, DOEWorkloadPreview } from '@/services/doeService';

interface DOEWizardModalProps {
  projectId: string;
  isOpen?: boolean;
  onClose: () => void;
  onSuccess: (doeId: string) => void;
}

export const DOEWizardModal: React.FC<DOEWizardModalProps> = ({ projectId, isOpen, onClose, onSuccess }) => {
  if (isOpen === false) return null;

  const [step, setStep] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState<string>('Spray Pyrolysis Factorial Study (CuO Thin Films)');
  const [researchQuestion, setResearchQuestion] = useState<string>(
    'How do substrate temperature and spray rate interact to determine the electrical conductivity of CuO thin films?'
  );
  const [description, setDescription] = useState<string>(
    'Factorial study investigating substrate temperature, spray rate, and precursor concentration for Mulberry-synthesized CuO thin films.'
  );

  const [factors, setFactors] = useState<FactorDefinition[]>([
    {
      parameter_code: 'substrate_temperature_c',
      name: 'Substrate Temperature',
      role: 'CONTROLLABLE',
      factor_type: 'CONTINUOUS',
      lower_bound: 250,
      upper_bound: 450,
      unit: '°C',
      levels: 2,
    },
    {
      parameter_code: 'spray_rate_ml_min',
      name: 'Spray Rate',
      role: 'CONTROLLABLE',
      factor_type: 'CONTINUOUS',
      lower_bound: 1.0,
      upper_bound: 10.0,
      unit: 'mL/min',
      levels: 2,
    },
    {
      parameter_code: 'precursor_concentration',
      name: 'Precursor Concentration',
      role: 'CONTROLLABLE',
      factor_type: 'CONTINUOUS',
      lower_bound: 0.05,
      upper_bound: 0.2,
      unit: 'mol/L',
      levels: 2,
    },
  ]);

  const [designMethod, setDesignMethod] = useState<string>('FULL_FACTORIAL');
  const [replicates, setReplicates] = useState<number>(1);
  const [centerPoints, setCenterPoints] = useState<number>(3);
  const [randomSeed, setRandomSeed] = useState<number>(42);
  const [randomizeRunOrder, setRandomizeRunOrder] = useState<boolean>(true);

  // Workload Preview
  const [preview, setPreview] = useState<DOEWorkloadPreview | null>(null);

  const handleAddFactor = () => {
    const idx = factors.length + 1;
    setFactors([
      ...factors,
      {
        parameter_code: `param_${idx}`,
        name: `Factor ${idx}`,
        role: 'CONTROLLABLE',
        factor_type: 'CONTINUOUS',
        lower_bound: 0,
        upper_bound: 100,
        unit: 'a.u.',
        levels: 2,
      },
    ]);
  };

  const handleRemoveFactor = (index: number) => {
    setFactors(factors.filter((_, i) => i !== index));
  };

  const handleUpdateFactor = (index: number, field: keyof FactorDefinition, value: any) => {
    const updated = [...factors];
    updated[index] = { ...updated[index], [field]: value };
    setFactors(updated);
  };

  const handleCalculatePreview = async () => {
    try {
      setLoading(true);
      setError(null);
      const payload = {
        project_id: projectId,
        name,
        description,
        research_question: researchQuestion,
        design_method: designMethod,
        factors,
        responses: [
          { property_name: 'Electrical Conductivity', unit: 'S/cm', direction: 'MAXIMIZE', weight: 1.0 },
        ],
        replicates,
        center_points: centerPoints,
        random_seed: randomSeed,
        randomize_run_order: randomizeRunOrder,
      };
      const res = await doeService.previewWorkload(payload);
      setPreview(res);
      setStep(4);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to calculate DOE design workload preview.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDOE = async () => {
    try {
      setLoading(true);
      setError(null);
      const payload = {
        project_id: projectId,
        name,
        description,
        research_question: researchQuestion,
        design_method: designMethod,
        factors,
        responses: [
          { property_name: 'Electrical Conductivity', unit: 'S/cm', direction: 'MAXIMIZE', weight: 1.0 },
        ],
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
    <div className="modal-overlay" role="dialog" aria-modal="true" style={{ zIndex: 1100 }}>
      <div
        className="modal"
        style={{
          maxWidth: 820,
          width: '92%',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          overflow: 'hidden',
          background: '#ffffff',
        }}
      >
        {/* Header */}
        <div className="modal-header" style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-border)' }}>
          <div>
            <span className="badge badge-planned" style={{ fontSize: '0.75rem', marginBottom: 4 }}>
              Phase 14 — Design of Experiments
            </span>
            <h2 className="modal-title" style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--color-text)' }}>
              DOE Study Configurator &amp; Matrix Generator
            </h2>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        {/* Wizard Steps Progress Bar */}
        <div
          style={{
            background: 'var(--color-bg)',
            padding: '12px 24px',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.8125rem',
            overflowX: 'auto',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontWeight: step >= 1 ? 600 : 400,
              color: step >= 1 ? 'var(--color-primary)' : 'var(--color-text-secondary)',
            }}
          >
            <span
              style={{
                width: 22,
                height: 22,
                borderRadius: '50%',
                background: step >= 1 ? 'var(--color-primary)' : 'var(--color-border)',
                color: step >= 1 ? '#ffffff' : 'var(--color-text-secondary)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                fontWeight: 700,
              }}
            >
              1
            </span>
            1. Study &amp; Research Question
          </div>
          <span style={{ color: 'var(--color-border-dark)', margin: '0 4px' }}>→</span>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontWeight: step >= 2 ? 600 : 400,
              color: step >= 2 ? 'var(--color-primary)' : 'var(--color-text-secondary)',
            }}
          >
            <span
              style={{
                width: 22,
                height: 22,
                borderRadius: '50%',
                background: step >= 2 ? 'var(--color-primary)' : 'var(--color-border)',
                color: step >= 2 ? '#ffffff' : 'var(--color-text-secondary)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                fontWeight: 700,
              }}
            >
              2
            </span>
            2. Factors &amp; Ranges
          </div>
          <span style={{ color: 'var(--color-border-dark)', margin: '0 4px' }}>→</span>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontWeight: step >= 3 ? 600 : 400,
              color: step >= 3 ? 'var(--color-primary)' : 'var(--color-text-secondary)',
            }}
          >
            <span
              style={{
                width: 22,
                height: 22,
                borderRadius: '50%',
                background: step >= 3 ? 'var(--color-primary)' : 'var(--color-border)',
                color: step >= 3 ? '#ffffff' : 'var(--color-text-secondary)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                fontWeight: 700,
              }}
            >
              3
            </span>
            3. Method &amp; Parameters
          </div>
          <span style={{ color: 'var(--color-border-dark)', margin: '0 4px' }}>→</span>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontWeight: step >= 4 ? 600 : 400,
              color: step >= 4 ? 'var(--color-primary)' : 'var(--color-text-secondary)',
            }}
          >
            <span
              style={{
                width: 22,
                height: 22,
                borderRadius: '50%',
                background: step >= 4 ? 'var(--color-primary)' : 'var(--color-border)',
                color: step >= 4 ? '#ffffff' : 'var(--color-text-secondary)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                fontWeight: 700,
              }}
            >
              4
            </span>
            4. Preview &amp; Generate
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            style={{
              margin: '16px 24px 0 24px',
              padding: '12px 16px',
              background: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#991b1b',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.875rem',
            }}
          >
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Modal Body */}
        <div className="modal-body" style={{ padding: '24px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* STEP 1: Study Info & Research Question */}
          {step === 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div className="form-group">
                <label className="form-label required" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                  DOE Study Name
                </label>
                <input
                  type="text"
                  className="form-control"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter DOE Study Name"
                />
              </div>

              <div className="form-group">
                <label className="form-label required" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                  Research Question
                </label>
                <textarea
                  rows={3}
                  className="form-control"
                  value={researchQuestion}
                  onChange={(e) => setResearchQuestion(e.target.value)}
                  placeholder="State the scientific research question to investigate"
                />
              </div>

              <div className="form-group">
                <label className="form-label" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                  Study Description &amp; Objectives
                </label>
                <textarea
                  rows={3}
                  className="form-control"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the objectives and background of this DOE study"
                />
              </div>
            </div>
          )}

          {/* STEP 2: Controllable Factors & Ranges */}
          {step === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: 0 }}>Controllable Factors ({factors.length})</h3>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', margin: '2px 0 0 0' }}>
                    Define parameter codes, bounds, and units for your design matrix.
                  </p>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={handleAddFactor}>
                  + Add Factor
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {factors.map((f, idx) => (
                  <div
                    key={idx}
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
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 1fr 1fr auto', gap: 12, alignItems: 'center' }}>
                      <div>
                        <label className="form-label" style={{ fontSize: '0.75rem', fontWeight: 600 }}>
                          Code
                        </label>
                        <input
                          type="text"
                          className="form-control"
                          style={{ fontSize: '0.8125rem' }}
                          value={f.parameter_code}
                          onChange={(e) => handleUpdateFactor(idx, 'parameter_code', e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="form-label" style={{ fontSize: '0.75rem', fontWeight: 600 }}>
                          Factor Name
                        </label>
                        <input
                          type="text"
                          className="form-control"
                          style={{ fontSize: '0.8125rem' }}
                          value={f.name}
                          onChange={(e) => handleUpdateFactor(idx, 'name', e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="form-label" style={{ fontSize: '0.75rem', fontWeight: 600 }}>
                          Type
                        </label>
                        <select
                          className="form-control"
                          style={{ fontSize: '0.8125rem' }}
                          value={f.factor_type}
                          onChange={(e) => handleUpdateFactor(idx, 'factor_type', e.target.value)}
                        >
                          <option value="CONTINUOUS">Continuous</option>
                          <option value="CATEGORICAL">Categorical</option>
                          <option value="DISCRETE">Discrete</option>
                        </select>
                      </div>
                      <div>
                        <label className="form-label" style={{ fontSize: '0.75rem', fontWeight: 600 }}>
                          Unit
                        </label>
                        <input
                          type="text"
                          className="form-control"
                          style={{ fontSize: '0.8125rem' }}
                          value={f.unit || ''}
                          onChange={(e) => handleUpdateFactor(idx, 'unit', e.target.value)}
                        />
                      </div>
                      <div style={{ paddingTop: 18 }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          style={{ color: 'var(--color-danger)', borderColor: 'var(--color-danger-light)' }}
                          onClick={() => handleRemoveFactor(idx)}
                        >
                          <X size={16} />
                        </button>
                      </div>
                    </div>

                    {f.factor_type === 'CONTINUOUS' && (
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: '1fr 1fr 1fr',
                          gap: 12,
                          paddingTop: 8,
                          borderTop: '1px solid var(--color-border-light)',
                        }}
                      >
                        <div>
                          <label className="form-label" style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                            Lower Bound (-1)
                          </label>
                          <input
                            type="number"
                            step="any"
                            className="form-control"
                            style={{ fontSize: '0.8125rem' }}
                            value={f.lower_bound ?? ''}
                            onChange={(e) => handleUpdateFactor(idx, 'lower_bound', parseFloat(e.target.value))}
                          />
                        </div>
                        <div>
                          <label className="form-label" style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                            Upper Bound (+1)
                          </label>
                          <input
                            type="number"
                            step="any"
                            className="form-control"
                            style={{ fontSize: '0.8125rem' }}
                            value={f.upper_bound ?? ''}
                            onChange={(e) => handleUpdateFactor(idx, 'upper_bound', parseFloat(e.target.value))}
                          />
                        </div>
                        <div>
                          <label className="form-label" style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                            Levels Count
                          </label>
                          <input
                            type="number"
                            className="form-control"
                            style={{ fontSize: '0.8125rem' }}
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

          {/* STEP 3: Method & Parameters */}
          {step === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div className="form-group">
                <label className="form-label required" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                  Design Method
                </label>
                <select className="form-control" value={designMethod} onChange={(e) => setDesignMethod(e.target.value)}>
                  <option value="FULL_FACTORIAL">Full Factorial (Complete combinations: 2^k or 3^k)</option>
                  <option value="FRACTIONAL_FACTORIAL">Fractional Factorial (2^(k-1) reduced runs)</option>
                  <option value="CENTRAL_COMPOSITE">Central Composite Design (CCD Response Surface)</option>
                  <option value="BOX_BEHNKEN">Box-Behnken Design (Non-extreme bounds RSM)</option>
                  <option value="RANDOMIZED_CANDIDATE">Randomized Candidate Design</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                <div className="form-group">
                  <label className="form-label" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                    Replicate Runs
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    className="form-control"
                    value={replicates}
                    onChange={(e) => setReplicates(parseInt(e.target.value))}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                    Center Points Count
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={10}
                    className="form-control"
                    value={centerPoints}
                    onChange={(e) => setCenterPoints(parseInt(e.target.value))}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                    Random Seed
                  </label>
                  <input
                    type="number"
                    className="form-control"
                    value={randomSeed}
                    onChange={(e) => setRandomSeed(parseInt(e.target.value))}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
                <input
                  type="checkbox"
                  id="randomizeRunOrder"
                  checked={randomizeRunOrder}
                  onChange={(e) => setRandomizeRunOrder(e.target.checked)}
                  style={{ width: 16, height: 16, cursor: 'pointer' }}
                />
                <label htmlFor="randomizeRunOrder" style={{ fontSize: '0.875rem', cursor: 'pointer', fontWeight: 500 }}>
                  Randomize run execution order using seed
                </label>
              </div>
            </div>
          )}

          {/* STEP 4: Workload Preview & Quality Report */}
          {step === 4 && preview && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div
                style={{
                  background: 'var(--color-bg)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 20,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16,
                }}
              >
                <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, margin: 0, color: 'var(--color-primary)' }}>
                  Workload Calculation &amp; Design Resolution
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12, textWrap: 'nowrap' }}>
                  <div style={{ background: '#ffffff', padding: 12, borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border-light)', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>Design Method</div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 700, marginTop: 4 }}>{preview.design_method}</div>
                  </div>
                  <div style={{ background: '#ffffff', padding: 12, borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border-light)', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>Base Runs</div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-primary)', marginTop: 2 }}>{preview.base_runs}</div>
                  </div>
                  <div style={{ background: '#ffffff', padding: 12, borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border-light)', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>Replicates</div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, color: '#4f46e5', marginTop: 2 }}>× {preview.replicates}</div>
                  </div>
                  <div style={{ background: '#ffffff', padding: 12, borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border-light)', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>Total Runs</div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 800, color: '#d97706', marginTop: 2 }}>{preview.total_runs}</div>
                  </div>
                </div>

                {preview.design_resolution && (
                  <div style={{ fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <strong>Design Resolution:</strong>
                    <span className="badge badge-planned font-mono" style={{ fontSize: '0.8125rem' }}>
                      {preview.design_resolution}
                    </span>
                  </div>
                )}

                {preview.requires_workload_warning && (
                  <div
                    style={{
                      padding: '12px 16px',
                      background: '#fffbeb',
                      border: '1px solid #fef08a',
                      color: '#78350f',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.8125rem',
                    }}
                  >
                    <strong>Experimental Workload Warning:</strong> {preview.warning_message}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer" style={{ padding: '16px 24px', borderTop: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--color-bg)' }}>
          {step > 1 ? (
            <button className="btn btn-secondary" onClick={() => setStep(step - 1)}>
              ← Back
            </button>
          ) : (
            <div />
          )}

          {step < 3 && (
            <button className="btn btn-primary" onClick={() => setStep(step + 1)}>
              Next Step →
            </button>
          )}

          {step === 3 && (
            <button className="btn btn-primary" onClick={handleCalculatePreview} disabled={loading}>
              {loading ? 'Calculating...' : 'Preview Workload & Matrix →'}
            </button>
          )}

          {step === 4 && (
            <button className="btn btn-primary" onClick={handleGenerateDOE} disabled={loading} style={{ fontWeight: 700 }}>
              {loading ? 'Generating...' : 'Generate & Save DOE Matrix'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
