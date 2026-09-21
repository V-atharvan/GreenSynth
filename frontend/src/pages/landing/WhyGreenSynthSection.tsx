/**
 * GreenSynth Analytics — Why GreenSynth Section → "Research Impact"
 * Five research-impact cards using cautious, academically appropriate language.
 */

import React from 'react'
import { TrendingUp, Zap, Search, Link2, Database } from 'lucide-react'

interface ImpactCard {
  icon: React.ReactNode
  iconClass: string
  title: string
  desc: string
}

const CARDS: ImpactCard[] = [
  {
    icon: <TrendingUp size={20} />,
    iconClass: '',
    title: 'Reduce Inefficient Trial-and-Error',
    desc: 'Use existing experimental evidence to help researchers plan more informed experiments — supporting better decisions before additional resources are committed.',
  },
  {
    icon: <Zap size={20} />,
    iconClass: 'lp-focus-icon-amber',
    title: 'Improve Research Efficiency',
    desc: 'Help prioritize potentially useful synthesis conditions and reduce unnecessary repeated testing by connecting past results with future experiment planning.',
  },
  {
    icon: <Search size={20} />,
    iconClass: 'lp-focus-icon-purple',
    title: 'Understand Synthesis–Property Relationships',
    desc: 'Support investigation of how synthesis parameters may influence conductivity, band gap, crystallinity, morphology, and other material properties.',
  },
  {
    icon: <Link2 size={20} />,
    iconClass: 'lp-focus-icon-green',
    title: 'Improve Research Traceability',
    desc: 'Maintain connections between projects, experiments, samples, raw files, calculations, models, recommendations, and validation to enable reproducibility and verification.',
  },
  {
    icon: <Database size={20} />,
    iconClass: 'lp-focus-icon-teal',
    title: 'Build Reusable Scientific Datasets',
    desc: 'Convert scattered experimental records into structured datasets that can support future analysis, model development, and cross-project comparisons.',
  },
]

const WhyGreenSynthSection: React.FC = () => (
  <section
    id="why-greensynth"
    className="lp-section"
    aria-labelledby="why-heading"
  >
    <div className="lp-container">
      <div className="lp-section-header">
        <span className="lp-section-label">Research Impact</span>
        <h2 id="why-heading" className="lp-section-heading">
          Why GreenSynth Analytics Matters
        </h2>
        <p className="lp-section-subheading">
          GreenSynth Analytics aims to improve the efficiency, traceability, and data-driven
          decision-making of green synthesis research by integrating experimental data, material
          characterization, statistical analysis, machine learning, and optimization into a
          unified research workflow.
        </p>
      </div>

      <div className="lp-why-grid">
        {CARDS.map((card) => (
          <article key={card.title} className="lp-focus-card">
            <div className={`lp-focus-icon ${card.iconClass}`} aria-hidden="true">
              {card.icon}
            </div>
            <h3 className="lp-focus-card-title">{card.title}</h3>
            <p className="lp-focus-card-desc">{card.desc}</p>
          </article>
        ))}
      </div>

      {/* Impact statement */}
      <div className="lp-impact-statement" role="note">
        <p>
          GreenSynth Analytics <em>supports</em> scientific decision-making by organizing research data
          and providing analytical tools. It aims to help, enable, and improve research
          efficiency — not to replace researchers, guarantee specific outcomes, or fully automate
          laboratory science.
        </p>
      </div>
    </div>
  </section>
)

export default WhyGreenSynthSection
