/**
 * GreenSynth Analytics — Platform Overview Section
 * "What Is GreenSynth Analytics?" — replaces CaseStudyCallout.
 * Five feature blocks explaining the platform's purpose.
 */

import React from 'react'
import { FolderOpen, Link2, BarChart3, Cpu, Compass } from 'lucide-react'

interface FeatureBlock {
  icon: React.ReactNode
  iconClass: string
  title: string
  desc: string
}

const FEATURES: FeatureBlock[] = [
  {
    icon: <FolderOpen size={20} />,
    iconClass: '',
    title: 'Organize Research',
    desc: 'Manage multiple research projects, experiments, samples, and synthesis methods in a structured, multi-tenant environment.',
  },
  {
    icon: <Link2 size={20} />,
    iconClass: 'lp-focus-icon-green',
    title: 'Connect Scientific Data',
    desc: 'Link synthesis conditions directly with characterization results and derived material properties, preserving data lineage at every step.',
  },
  {
    icon: <BarChart3 size={20} />,
    iconClass: 'lp-focus-icon-amber',
    title: 'Analyze Relationships',
    desc: 'Study how synthesis parameters influence conductivity, band gap, crystallinity, and morphology through statistical analysis and DOE.',
  },
  {
    icon: <Cpu size={20} />,
    iconClass: 'lp-focus-icon-purple',
    title: 'Support Prediction',
    desc: 'Use machine learning to estimate selected material properties from synthesis conditions. Predictions are decision-support outputs, not guaranteed results.',
  },
  {
    icon: <Compass size={20} />,
    iconClass: 'lp-focus-icon-teal',
    title: 'Guide New Experiments',
    desc: 'Use DOE and optimization tools to identify promising synthesis conditions for further experimental testing and validation.',
  },
]

const PlatformOverviewSection: React.FC = () => (
  <section
    id="platform-overview"
    className="lp-section"
    aria-labelledby="overview-heading"
  >
    <div className="lp-container">
      <div className="lp-section-header">
        <span className="lp-section-label lp-section-label-blue">What Is GreenSynth Analytics?</span>
        <h2 id="overview-heading" className="lp-section-heading">
          A Unified Platform for Green Synthesis Research
        </h2>
        <p className="lp-section-subheading">
          GreenSynth Analytics is a data-driven research and analytics platform designed to support
          the complete lifecycle of green synthesis research. It organizes research projects,
          experiments, samples, synthesis parameters, characterization results, calculated material
          properties, statistical relationships, machine-learning models, optimization candidates,
          and experimental validation in one connected environment.
        </p>
      </div>

      <div className="lp-overview-grid">
        {FEATURES.map((f) => (
          <article key={f.title} className="lp-overview-card">
            <div className={`lp-focus-icon ${f.iconClass}`} aria-hidden="true">
              {f.icon}
            </div>
            <h3 className="lp-focus-card-title">{f.title}</h3>
            <p className="lp-focus-card-desc">{f.desc}</p>
          </article>
        ))}
      </div>

      {/* ML Disclaimer */}
      <div className="lp-overview-disclaimer" role="note">
        <span className="lp-overview-disclaimer-label">Note</span>
        Machine-learning predictions are decision-support outputs and must be experimentally
        validated before being treated as scientific conclusions.
      </div>
    </div>
  </section>
)

export default PlatformOverviewSection
