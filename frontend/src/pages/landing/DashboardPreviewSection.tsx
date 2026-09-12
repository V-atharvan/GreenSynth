/**
 * GreenSynth Analytics — Dashboard Preview Section
 * Shows a realistic representation of the authenticated research platform UI.
 */

import React from 'react'
import { BarChart3, FlaskConical, Layers, Activity, Cpu, Target } from 'lucide-react'

const DashboardPreviewSection: React.FC = () => (
  <section className="lp-section lp-section-alt" aria-labelledby="preview-heading">
    <div className="lp-container">
      <div className="lp-section-header">
        <span className="lp-section-label lp-section-label-blue">Platform Preview</span>
        <h2 id="preview-heading" className="lp-section-heading">
          Designed Around the Researcher's Workflow
        </h2>
        <p className="lp-section-subheading">
          A structured research environment built for laboratory data management, scientific
          analysis, and evidence-based decision-making.
        </p>
      </div>

      {/* Simulated dashboard UI */}
      <div className="lp-preview-wrap" role="img" aria-label="GreenSynth Analytics dashboard preview">
        {/* Browser-style bar */}
        <div className="lp-preview-bar" aria-hidden="true">
          <div className="lp-preview-bar-dot" />
          <div className="lp-preview-bar-dot" />
          <div className="lp-preview-bar-dot" />
          <div className="lp-preview-bar-label">GreenSynth Analytics — Research Platform</div>
        </div>

        {/* Dashboard body */}
        <div className="lp-preview-content">
          {/* Stats row */}
          <div className="lp-preview-stats">
            {[
              { val: '3',  label: 'Projects' },
              { val: '24', label: 'Experiments' },
              { val: '96', label: 'Samples' },
              { val: '8',  label: 'ML Models' },
            ].map(({ val, label }) => (
              <div key={label} className="lp-preview-stat">
                <div className="lp-preview-stat-val">{val}</div>
                <div className="lp-preview-stat-label">{label}</div>
              </div>
            ))}
          </div>

          {/* Module panels */}
          <div className="lp-preview-row">
            <div className="lp-preview-module">
              <div className="lp-preview-module-title">
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Activity size={12} aria-hidden="true" />
                  Characterization
                </span>
              </div>
              <div className="lp-preview-module-items">
                {['XRD Analysis — Sample CuO-07', 'UV-Vis — Band Gap 2.1 eV', 'FTIR — Phase Confirmed', 'SEM — 45 nm particles'].map((item) => (
                  <div key={item} className="lp-preview-module-item">
                    <span className="lp-preview-module-item-dot" aria-hidden="true" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="lp-preview-module">
              <div className="lp-preview-module-title">
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Cpu size={12} aria-hidden="true" />
                  Machine Learning & Optimization
                </span>
              </div>
              <div className="lp-preview-module-items">
                {['Dataset: 32 samples — Active', 'Random Forest — R² 0.91', 'Optimization: 4 candidates', 'Validation: 2 confirmed'].map((item) => (
                  <div key={item} className="lp-preview-module-item">
                    <span className="lp-preview-module-item-dot" aria-hidden="true" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div style={{
            marginTop: '12px',
            padding: '8px 12px',
            background: '#ffffff',
            border: '1px solid var(--color-border-light)',
            borderRadius: '6px',
            fontSize: '0.75rem',
            color: 'var(--color-text-secondary)',
            fontStyle: 'italic',
          }}>
            Preview representation of the authenticated research platform — values shown are illustrative.
          </div>
        </div>
      </div>
    </div>
  </section>
)

export default DashboardPreviewSection
