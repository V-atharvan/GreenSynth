/**
 * GreenSynth Analytics — Research Traceability Section
 * Shows the full traceability chain and highlight cards.
 */

import React from 'react'
import { Link2, Shield, Database, FileCheck, GitBranch } from 'lucide-react'

const CHAIN_STEPS = [
  { title: 'Project',                  desc: 'Root research container' },
  { title: 'Experiment',               desc: 'Synthesis design and execution record' },
  { title: 'Sample',                   desc: 'Physical synthesis sample registration' },
  { title: 'Raw Characterization File', desc: 'Uploaded instrument data file' },
  { title: 'Processed Data',           desc: 'Extracted numerical data from raw file' },
  { title: 'Scientific Calculation',   desc: 'Derived property (e.g., crystallite size, band gap)' },
  { title: 'Statistical Analysis',     desc: 'Evidence-based analysis results' },
  { title: 'ML Dataset',               desc: 'Curated training dataset with provenance' },
  { title: 'Model',                    desc: 'Trained predictive model artifact' },
  { title: 'Prediction',               desc: 'Model output with uncertainty range' },
  { title: 'Recommendation',           desc: 'Data-driven synthesis suggestion' },
  { title: 'Validation',               desc: 'Experimental confirmation record' },
]

const HIGHLIGHTS = [
  {
    icon: <Shield size={16} />,
    title: 'Raw File Integrity',
    desc: 'Uploaded characterization files can be tracked using SHA-256 integrity checksums for provenance verification.',
  },
  {
    icon: <Database size={16} />,
    title: 'Dataset Provenance',
    desc: 'Every ML dataset maintains traceable links to the experimental samples, parameters, and calculations it was built from.',
  },
  {
    icon: <FileCheck size={16} />,
    title: 'Model Provenance',
    desc: 'Trained models are linked to their dataset version, ensuring reproducibility and auditability of model predictions.',
  },
  {
    icon: <GitBranch size={16} />,
    title: 'Validation Records',
    desc: 'Experimental validation results are stored and linked to the recommendations and model predictions they confirm or refute.',
  },
]

const TraceabilitySection: React.FC = () => (
  <section className="lp-section" aria-labelledby="trace-heading">
    <div className="lp-container">
      <div className="lp-section-header">
        <span className="lp-section-label lp-section-label-blue">Research Traceability</span>
        <h2 id="trace-heading" className="lp-section-heading">
          Every Result Has a Research Trail
        </h2>
        <p className="lp-section-subheading">
          Maintain traceable relationships between experimental conditions, samples, raw files,
          calculated properties, analyses, predictions, and validation results throughout the
          complete research lifecycle.
        </p>
      </div>

      <div className="lp-trace-layout">
        {/* Left: Chain */}
        <div>
          <div className="lp-trace-chain" role="list" aria-label="Research traceability chain">
            {CHAIN_STEPS.map((step, i) => (
              <div key={step.title} className="lp-trace-step" role="listitem">
                <div className="lp-trace-connector">
                  <div className="lp-trace-dot" aria-hidden="true" />
                  {i < CHAIN_STEPS.length - 1 && (
                    <div className="lp-trace-line" aria-hidden="true" />
                  )}
                </div>
                <div className="lp-trace-content">
                  <div className="lp-trace-title">{step.title}</div>
                  <div className="lp-trace-desc">{step.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Highlight cards */}
        <div>
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Link2 size={18} color="var(--color-accent)" aria-hidden="true" />
              <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-text)' }}>
                Traceable Research Data
              </span>
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', lineHeight: 1.55, margin: 0 }}>
              GreenSynth connects every element of the research process — from raw laboratory files
              to final validation results — in one traceable, auditable research record.
            </p>
          </div>

          <div className="lp-trace-highlights">
            {HIGHLIGHTS.map((h) => (
              <div key={h.title} className="lp-trace-highlight-card">
                <div className="lp-trace-h-icon" aria-hidden="true">
                  {h.icon}
                </div>
                <div>
                  <div className="lp-trace-h-title">{h.title}</div>
                  <div className="lp-trace-h-desc">{h.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  </section>
)

export default TraceabilitySection
