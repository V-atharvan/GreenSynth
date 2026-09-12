/**
 * GreenSynth Analytics — Data → Intelligence Section
 * Visual pipeline showing how experimental data flows to research decisions.
 */

import React from 'react'
import { ChevronDown } from 'lucide-react'

interface PipelineNode {
  label: string
  sub?: string
  variant?: 'primary' | 'accent' | 'success' | 'default'
  isMulti?: string[]
}

const NODES: PipelineNode[] = [
  { label: 'Experimental Data', variant: 'primary' },
  { isMulti: ['Synthesis Parameters', 'Characterization Results', 'Material Properties'] } as PipelineNode,
  { label: 'Statistical Analysis', variant: 'accent' },
  { label: 'Machine Learning', variant: 'accent' },
  { label: 'Prediction + Uncertainty', variant: 'default', sub: 'Confidence-quantified output' },
  { label: 'DOE / Optimization', variant: 'default' },
  { label: 'Recommendation', variant: 'default', sub: 'Candidate conditions' },
  { label: 'New Experiment', variant: 'accent' },
  { label: 'Characterization', variant: 'default' },
  { label: 'Validation', variant: 'success' },
]

const classForVariant = (v?: string) => {
  if (v === 'primary') return 'lp-pipeline-node-primary'
  if (v === 'accent')  return 'lp-pipeline-node-accent'
  if (v === 'success') return 'lp-pipeline-node-success'
  return ''
}

const DataIntelligenceSection: React.FC = () => (
  <section className="lp-section" aria-labelledby="data-intel-heading">
    <div className="lp-container">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '64px', alignItems: 'center' }}>
        {/* Left: Text */}
        <div>
          <span className="lp-section-label">Data Intelligence</span>
          <h2 id="data-intel-heading" className="lp-section-heading">
            From Experimental Data to Research Decisions
          </h2>
          <p className="lp-section-subheading" style={{ marginBottom: '24px' }}>
            GreenSynth transforms structured experimental observations into statistical evidence,
            predictive models, optimization candidates, and experimentally testable recommendations.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {[
              { title: 'Structured Data Collection', desc: 'Parameters, characterization results, and material properties are stored in a consistent, queryable format.' },
              { title: 'Evidence-Based Analysis',    desc: 'Statistical methods identify relationships between synthesis variables and material outcomes before modeling.' },
              { title: 'Predictive Intelligence',    desc: 'Machine learning models are trained on experimental datasets to predict outcomes with quantified uncertainty.' },
              { title: 'Optimization Loop',          desc: 'Optimization identifies promising synthesis conditions that are then validated through new experiments.' },
            ].map(({ title, desc }) => (
              <div key={title} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                <div style={{
                  width: '8px', height: '8px', borderRadius: '50%',
                  background: 'var(--color-accent)', marginTop: '6px', flexShrink: 0,
                }} aria-hidden="true" />
                <div>
                  <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--color-text)', marginBottom: '2px' }}>{title}</div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', lineHeight: 1.55 }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Pipeline visualization */}
        <div>
          <div className="lp-pipeline" role="img" aria-label="Data to intelligence pipeline">
            {NODES.map((node, i) => (
              <React.Fragment key={i}>
                {node.isMulti ? (
                  <div className="lp-pipeline-multi">
                    {node.isMulti.map((item) => (
                      <div key={item} className="lp-pipeline-multi-item">{item}</div>
                    ))}
                  </div>
                ) : (
                  <div className={`lp-pipeline-node ${classForVariant(node.variant)}`}>
                    <div className="lp-pipeline-node-label">{node.label}</div>
                    {node.sub && <div className="lp-pipeline-node-sub">{node.sub}</div>}
                  </div>
                )}

                {i < NODES.length - 1 && (
                  <div className="lp-pipeline-arrow" aria-hidden="true">
                    <ChevronDown size={16} />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </div>

    <style>{`
      @media (max-width: 768px) {
        #data-intel-heading {
          font-size: 1.5rem;
        }
        .lp-section > .lp-container > div {
          grid-template-columns: 1fr !important;
        }
      }
    `}</style>
  </section>
)

export default DataIntelligenceSection
