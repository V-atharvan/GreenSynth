/**
 * GreenSynth Analytics — Case Study Detail Section
 * Detailed structured case study for the primary P7 research case.
 */

import React from 'react'

const VARIABLES = [
  'Precursor concentration',
  'Extract concentration',
  'Substrate temperature',
  'Spray rate',
  'Spray duration',
  'Nozzle–substrate distance',
  'Carrier gas pressure',
  'Spray cycles',
]

const CHAR_TAGS   = ['XRD', 'UV-Vis', 'FTIR', 'SEM', 'Electrical']
const ANALYSIS_TAGS = ['Statistical Analysis', 'Machine Learning', 'DOE', 'Optimization', 'Validation']

const CaseStudyDetailSection: React.FC = () => (
  <section className="lp-section lp-section-dark" aria-labelledby="case-detail-heading">
    <div className="lp-container">
      <div className="lp-section-header">
        <span className="lp-section-label">Featured Research Case Study</span>
        <h2 id="case-detail-heading" className="lp-section-heading lp-section-heading-light">
          Primary Research Case Study
        </h2>
      </div>

      <div className="lp-case-layout">
        {/* Left */}
        <div>
          <p className="lp-case-info-title">
            "Phytochemical synthesis of semiconducting copper oxide using mulberry extract in ethanol
            by spray pyrolysis"
          </p>

          <div className="lp-case-meta-grid">
            {[
              { label: 'Material',          value: 'CuO' },
              { label: 'Green Component',   value: 'Mulberry Extract' },
              { label: 'Solvent',           value: 'Ethanol' },
              { label: 'Synthesis Method',  value: 'Spray Pyrolysis' },
            ].map(({ label, value }) => (
              <div key={label} className="lp-case-meta-item">
                <div className="lp-case-meta-label">{label}</div>
                <div className="lp-case-meta-value">{value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right */}
        <div className="lp-case-panels">
          {/* Research Variables */}
          <div className="lp-case-panel">
            <div className="lp-case-panel-title">Research Variables</div>
            <div className="lp-case-tag-wrap">
              {VARIABLES.map((v) => (
                <span key={v} className="lp-case-tag">{v}</span>
              ))}
            </div>
          </div>

          {/* Characterization */}
          <div className="lp-case-panel">
            <div className="lp-case-panel-title">Characterization Techniques</div>
            <div className="lp-case-tag-wrap">
              {CHAR_TAGS.map((t) => (
                <span key={t} className="lp-case-tag">{t}</span>
              ))}
            </div>
          </div>

          {/* Analysis */}
          <div className="lp-case-panel">
            <div className="lp-case-panel-title">Analysis Methods</div>
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
