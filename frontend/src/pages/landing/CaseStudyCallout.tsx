/**
 * GreenSynth Analytics — Primary Case Study Callout
 * Immediately below hero; highlights the P7 research case study.
 */

import React from 'react'

const CaseStudyCallout: React.FC = () => (
  <section className="lp-callout" aria-label="Primary research case study">
    <div className="lp-container">
      <div className="lp-callout-inner">
        {/* Label column */}
        <div className="lp-callout-label-col">
          <span className="lp-callout-badge">Primary Research Case Study</span>
        </div>

        {/* Content */}
        <div>
          <p className="lp-callout-title">
            "Phytochemical synthesis of semiconducting copper oxide using mulberry extract in ethanol
            by spray pyrolysis"
          </p>

          <div className="lp-callout-grid">
            {[
              { label: 'Material',          value: 'CuO' },
              { label: 'Green Precursor',   value: 'Mulberry Extract' },
              { label: 'Solvent',           value: 'Ethanol' },
              { label: 'Synthesis Method',  value: 'Spray Pyrolysis' },
            ].map(({ label, value }) => (
              <div key={label} className="lp-callout-item">
                <div className="lp-callout-item-label">{label}</div>
                <div className="lp-callout-item-value">{value}</div>
              </div>
            ))}

            <div className="lp-callout-item" style={{ minWidth: '240px' }}>
              <div className="lp-callout-item-label">Characterization</div>
              <div className="lp-callout-char">XRD&nbsp;•&nbsp;UV-Vis&nbsp;•&nbsp;FTIR&nbsp;•&nbsp;SEM&nbsp;•&nbsp;Electrical</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
)

export default CaseStudyCallout
