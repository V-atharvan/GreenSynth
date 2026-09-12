/**
 * GreenSynth Analytics — Why GreenSynth Section
 * Four value proposition cards.
 */

import React from 'react'

const VALUE_PROPS = [
  {
    num: '01',
    title: 'Structured Research Data',
    desc: 'Organize experiments, samples, synthesis parameters, characterization results, and calculated material properties in one connected research environment.',
  },
  {
    num: '02',
    title: 'Scientific Traceability',
    desc: 'Maintain traceable relationships between raw data, calculated results, statistical analyses, predictive models, and experimental validation records.',
  },
  {
    num: '03',
    title: 'Data-Driven Decisions',
    desc: 'Use statistical analysis and machine learning to identify meaningful relationships between synthesis parameters and material properties.',
  },
  {
    num: '04',
    title: 'Research Optimization',
    desc: 'Generate experimentally testable candidate synthesis conditions through data-driven optimization, followed by laboratory validation.',
  },
]

const WhyGreenSynthSection: React.FC = () => (
  <section id="why-greensynth" className="lp-section" aria-labelledby="why-heading">
    <div className="lp-container">
      <div className="lp-section-header">
        <span className="lp-section-label lp-section-label-blue">Value</span>
        <h2 id="why-heading" className="lp-section-heading">
          Why GreenSynth?
        </h2>
        <p className="lp-section-subheading">
          GreenSynth Analytics is designed to support the complete research lifecycle — from
          experimental design to evidence-based findings — in a structured, traceable environment.
        </p>
      </div>

      <div className="lp-why-grid">
        {VALUE_PROPS.map((vp) => (
          <article key={vp.num} className="lp-why-card">
            <div className="lp-why-number" aria-hidden="true">{vp.num}</div>
            <h3 className="lp-why-title">{vp.title}</h3>
            <p className="lp-why-desc">{vp.desc}</p>
          </article>
        ))}
      </div>
    </div>
  </section>
)

export default WhyGreenSynthSection
