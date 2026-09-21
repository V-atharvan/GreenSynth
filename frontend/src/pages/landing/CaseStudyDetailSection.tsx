/**
 * GreenSynth Analytics — Featured Case Study Section (P7)
 * Clearly framed as ONE featured example within the broader P1–P8 portfolio.
 */

import React from 'react'

const VARIABLES = [
  'Precursor concentration',
  'Extract concentration',
  'Substrate temperature (°C)',
  'Spray rate (mL/min)',
  'Spray duration (min)',
  'Nozzle–substrate distance (cm)',
  'Carrier-gas pressure (bar)',
  'Spray cycles',
]

const CHAR_TAGS     = ['XRD', 'UV-Vis', 'FTIR', 'SEM', 'Electrical']
const ANALYSIS_TAGS = ['Statistical Analysis', 'Machine Learning', 'DOE', 'Optimization', 'Validation']

const CaseStudyDetailSection: React.FC = () => (
  <section id="case-study" className="lp-section lp-section-dark" aria-labelledby="case-detail-heading">
    <div className="lp-container">
      <div className="lp-section-header">
        <span className="lp-section-label">Featured Research Case Study</span>
        <h2 id="case-detail-heading" className="lp-section-heading lp-section-heading-light">
          P7: The Primary Platform Demonstration Case
        </h2>
        <p className="lp-section-subheading lp-section-subheading-light">
          P7 serves as the primary demonstration case for the GreenSynth Analytics workflow.
          The same platform architecture also supports the other seven research projects — P1–P6
          and P8 — involving CuO, silica/silicon, different solvents, plant-based resources, and
          synthesis methods.
        </p>
      </div>

      <div className="lp-case-layout">
        {/* Left: Project details */}
        <div>
          {/* Portfolio context callout */}
          <div className="lp-case-context-note" role="note">
            <strong>Portfolio context:</strong> P7 is one of eight research projects supported by
            GreenSynth Analytics. It is not the only project the platform supports.
          </div>

          <p className="lp-case-info-title">
            "Phytochemical Synthesis of Semiconducting Copper Oxide Using Mulberry Extract in
            Ethanol by Spray Pyrolysis"
          </p>

          <div className="lp-case-meta-grid">
            {[
              { label: 'Project ID',        value: 'P7' },
              { label: 'Material',          value: 'CuO' },
              { label: 'Green Component',   value: 'Mulberry extract' },
              { label: 'Solvent',           value: 'Ethanol' },
              { label: 'Synthesis Method',  value: 'Spray pyrolysis' },
              { label: 'ML Target (Demo)',  value: 'Electrical conductivity' },
            ].map(({ label, value }) => (
              <div key={label} className="lp-case-meta-item">
                <div className="lp-case-meta-label">{label}</div>
                <div className="lp-case-meta-value">{value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Panels */}
        <div className="lp-case-panels">
          <div className="lp-case-panel">
            <div className="lp-case-panel-title">Synthesis Variables</div>
            <div className="lp-case-tag-wrap">
              {VARIABLES.map((v) => (
                <span key={v} className="lp-case-tag">{v}</span>
              ))}
            </div>
          </div>

          <div className="lp-case-panel">
            <div className="lp-case-panel-title">Characterization Techniques</div>
            <div className="lp-case-tag-wrap">
              {CHAR_TAGS.map((t) => (
                <span key={t} className="lp-case-tag">{t}</span>
              ))}
            </div>
          </div>

          <div className="lp-case-panel">
            <div className="lp-case-panel-title">Analysis Pipeline</div>
            <div className="lp-case-tag-wrap">
              {ANALYSIS_TAGS.map((t) => (
                <span key={t} className="lp-case-tag">{t}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
)

export default CaseStudyDetailSection
