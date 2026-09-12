/**
 * GreenSynth Analytics — Optimization Section
 * Pipeline from synthesis parameters to experimental validation.
 */

import React from 'react'
import { Sliders, Cpu, Target, Lightbulb, FlaskConical, Activity, ShieldCheck, ChevronDown } from 'lucide-react'

const OPT_NODES = [
  { icon: <Sliders size={16} />,     iconClass: '',                       title: 'Synthesis Parameters',    sub: 'Experimental input space' },
  { icon: <Cpu size={16} />,         iconClass: 'lp-opt-node-icon-primary', title: 'Predictive Model',         sub: 'Trained on experimental data' },
  { icon: <Target size={16} />,      iconClass: '',                       title: 'Optimization Engine',     sub: 'Candidate condition search' },
  { icon: <Lightbulb size={16} />,   iconClass: '',                       title: 'Recommended Conditions',  sub: 'Experimentally testable candidates' },
  { icon: <FlaskConical size={16} />, iconClass: '',                      title: 'New Experiment',          sub: 'Laboratory synthesis' },
  { icon: <Activity size={16} />,    iconClass: '',                       title: 'Characterization',        sub: 'Material property measurement' },
  { icon: <ShieldCheck size={16} />, iconClass: 'lp-opt-node-icon-success', title: 'Validation',             sub: 'Experimental confirmation' },
]

const OptimizationSection: React.FC = () => (
  <section className="lp-section" aria-labelledby="opt-heading">
    <div className="lp-container">
      <div className="lp-opt-layout">
        {/* Left: Description */}
        <div>
          <span className="lp-section-label">Optimization</span>
          <h2 id="opt-heading" className="lp-section-heading">
            Move from Prediction to Optimization
          </h2>
          <p className="lp-section-subheading" style={{ marginBottom: '28px' }}>
            Use experimental evidence and predictive models to identify promising synthesis conditions
            for future experiments, followed by experimental validation of predicted outcomes.
          </p>

          <div className="lp-opt-params">
            <div className="lp-opt-params-title">Example Synthesis Parameters</div>
            <div className="lp-param-tag-grid">
              {[
                { label: 'Temperature',           range: '300 – 500 °C' },
                { label: 'Spray Rate',            range: 'ml/min' },
                { label: 'Extract Concentration', range: 'v/v %' },
                { label: 'Precursor Conc.',       range: 'mol/L' },
              ].map(({ label, range }) => (
                <div key={label} className="lp-param-tag">
                  <div>
                    <div style={{ fontSize: '0.8125rem', fontWeight: 600 }}>{label}</div>
                    <div className="lp-param-range">{range}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="lp-opt-note">
              <strong>Note:</strong> GreenSynth identifies <em>promising candidate conditions</em> based
              on predictive models. All optimization outputs require experimental validation before
              research conclusions can be drawn.
            </div>
          </div>
        </div>

        {/* Right: Pipeline */}
        <div>
          <div className="lp-opt-pipeline" role="list" aria-label="Optimization pipeline steps">
            {OPT_NODES.map((node, i) => (
              <React.Fragment key={node.title}>
                <div className="lp-opt-node" role="listitem" aria-label={node.title}>
                  <div className={`lp-opt-node-icon ${node.iconClass}`} aria-hidden="true">
                    {node.icon}
                  </div>
                  <div>
                    <div className="lp-opt-node-title">{node.title}</div>
                    <div className="lp-opt-node-sub">{node.sub}</div>
                  </div>
                </div>
                {i < OPT_NODES.length - 1 && (
                  <div className="lp-opt-arrow" aria-hidden="true">
                    <ChevronDown size={14} />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </div>
  </section>
)

export default OptimizationSection
