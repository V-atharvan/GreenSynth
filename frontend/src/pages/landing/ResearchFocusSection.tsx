/**
 * GreenSynth Analytics — Research Focus Section
 * Four-card grid introducing the core research topics.
 */

import React from 'react'
import { Atom, Leaf, Wind, BarChart3 } from 'lucide-react'

interface FocusCard {
  icon: React.ReactNode
  iconClass: string
  title: string
  desc: string
}

const CARDS: FocusCard[] = [
  {
    icon: <Atom size={20} />,
    iconClass: '',
    title: 'CuO Semiconductor',
    desc: 'Copper oxide synthesis and material-property analysis across structural, optical, chemical, morphological, and electrical characterization.',
  },
  {
    icon: <Leaf size={20} />,
    iconClass: 'lp-focus-icon-green',
    title: 'Phytochemical Synthesis',
    desc: 'Plant-derived extracts as green synthesis components — replacing conventional chemical reducing and stabilizing agents.',
  },
  {
    icon: <Wind size={20} />,
    iconClass: 'lp-focus-icon-amber',
    title: 'Spray Pyrolysis',
    desc: 'Controlled thin-film deposition through precisely parameterized synthesis-process conditions including temperature, spray rate, and carrier gas.',
  },
  {
    icon: <BarChart3 size={20} />,
    iconClass: 'lp-focus-icon-purple',
    title: 'Data-Driven Research',
    desc: 'Statistical analysis, machine learning, design of experiments, and optimization applied to experimental data for evidence-based research decisions.',
  },
]

const ResearchFocusSection: React.FC = () => (
  <section
    id="research-focus"
    className="lp-section lp-section-alt"
    aria-labelledby="research-focus-heading"
  >
    <div className="lp-container">
      <div className="lp-section-header">
        <span className="lp-section-label lp-section-label-blue">Research Focus</span>
        <h2 id="research-focus-heading" className="lp-section-heading">
          Green Synthesis of Semiconductor Materials
        </h2>
        <p className="lp-section-subheading">
          GreenSynth provides a structured research environment for investigating sustainable
          synthesis routes, material properties, process parameters, and experimental outcomes.
        </p>
      </div>

      <div className="lp-focus-grid">
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
    </div>
  </section>
)

export default ResearchFocusSection
