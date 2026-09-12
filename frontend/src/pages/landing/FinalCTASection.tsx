/**
 * GreenSynth Analytics — Final CTA Section
 */

import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, LogIn } from 'lucide-react'

const FinalCTASection: React.FC = () => {
  const scrollToWorkflow = () => {
    const el = document.getElementById('workflow')
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <section className="lp-cta" aria-labelledby="cta-heading">
      <div className="lp-container">
        <div className="lp-cta-eyebrow" aria-hidden="true">
          GREEN SYNTHESIS • DATA • INTELLIGENCE
        </div>

        <h2 id="cta-heading" className="lp-cta-title">
          Build Better Research from Better Data
        </h2>

        <p className="lp-cta-desc">
          GreenSynth Analytics connects green synthesis experiments, characterization, statistical
          evidence, machine learning, optimization, and experimental validation in one traceable
          research environment.
        </p>

        <div className="lp-cta-actions">
          <Link
            to="/login"
            className="lp-btn-cta-primary"
            id="cta-enter-btn"
            aria-label="Enter GreenSynth Analytics research platform"
          >
            <LogIn size={18} aria-hidden="true" />
            Enter GreenSynth Analytics
          </Link>

          <button
            className="lp-btn-cta-secondary"
            id="cta-workflow-btn"
            onClick={scrollToWorkflow}
            aria-label="Explore the research workflow"
          >
            Explore Research Workflow
            <ArrowRight size={16} aria-hidden="true" />
          </button>
        </div>
      </div>
    </section>
  )
}

export default FinalCTASection
