/**
 * GreenSynth Analytics — Hero Section
 * Multi-project hero communicating the full P1–P8 platform scope.
 */

import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, ChevronDown } from 'lucide-react'
import { PROJECTS } from './landingData'

const METHOD_COLOR: Record<string, string> = {
  'Sol-gel':         '#8b5cf6',
  'Hydrothermal':    '#3b9ede',
  'Spray Pyrolysis': '#f97316',
}

const MATERIAL_COLOR: Record<string, string> = {
  'CuO':            '#f59e0b',
  'Silica/Silicon': '#3b9ede',
}

const HeroVisualization: React.FC = () => (
  <div className="lp-hero-vis-card" aria-hidden="true">
    <div className="lp-hero-vis-title">Research Portfolio — P1 to P8</div>

    {/* Mini project grid */}
    <div className="lp-hero-proj-grid">
      {PROJECTS.map((p) => (
        <div
          key={p.id}
          className={`lp-hero-proj-chip${p.featured ? ' lp-hero-proj-chip-featured' : ''}`}
          style={{ borderColor: `${MATERIAL_COLOR[p.material]}40` }}
        >
          <span
            className="lp-hero-proj-id"
            style={{ color: MATERIAL_COLOR[p.material] }}
          >
            {p.id}
          </span>
          <span
            className="lp-hero-proj-method-dot"
            style={{ background: METHOD_COLOR[p.method] }}
            title={p.method}
          />
        </div>
      ))}
    </div>

    {/* Legend */}
    <div className="lp-hero-legend">
      {[
        { label: 'CuO', color: '#f59e0b' },
        { label: 'Silica/Si', color: '#3b9ede' },
      ].map((l) => (
        <div key={l.label} className="lp-hero-legend-item">
          <span className="lp-hero-legend-dot" style={{ background: l.color }} />
          <span>{l.label}</span>
        </div>
      ))}
      {Object.entries(METHOD_COLOR).map(([m, c]) => (
        <div key={m} className="lp-hero-legend-item">
          <span className="lp-hero-legend-dot" style={{ background: c }} />
          <span>{m}</span>
        </div>
      ))}
    </div>

    {/* Pipeline */}
    <div style={{ marginTop: '14px' }}>
      <div style={{ fontSize: '0.625rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'rgba(200,216,232,0.45)', marginBottom: '8px' }}>
        Common Research Workflow
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
        {['Project', 'Experiment', 'Sample', 'Characterization', 'Analysis', 'ML', 'Validation'].map((step, i, arr) => (
          <React.Fragment key={step}>
            <span style={{
              fontSize: '0.5625rem', fontWeight: 600, color: 'rgba(200,216,232,0.85)',
              background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '4px', padding: '3px 6px', whiteSpace: 'nowrap',
            }}>{step}</span>
            {i < arr.length - 1 && <span style={{ color: 'rgba(200,216,232,0.3)', fontSize: '0.625rem' }}>›</span>}
          </React.Fragment>
        ))}
      </div>
    </div>

    {/* Conceptual scatter */}
    <div style={{ background: 'rgba(0,0,0,0.15)', borderRadius: '8px', padding: '10px', marginTop: '12px' }}>
      <div style={{ fontSize: '0.5625rem', color: 'rgba(200,216,232,0.4)', marginBottom: '6px', fontStyle: 'italic' }}>
        Conceptual visualization — illustrative data
      </div>
      <svg width="100%" height="64" viewBox="0 0 300 64" aria-label="Conceptual synthesis-property relationship">
        <line x1="20" y1="54" x2="290" y2="54" stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
        <line x1="20" y1="8"  x2="20"  y2="54" stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
        <line x1="30" y1="50" x2="280" y2="14" stroke="#3b9ede" strokeWidth="1.5" strokeDasharray="4,3" opacity="0.6" />
        {[[40,48],[70,42],[95,38],[120,33],[145,30],[170,25],[195,22],[220,19],[250,16],[275,14]].map(([x,y], i) => (
          <circle key={i} cx={x} cy={y} r="3" fill={i < 6 ? '#f59e0b' : '#3b9ede'} opacity="0.85" />
        ))}
        <text x="155" y="62" textAnchor="middle" fill="rgba(200,216,232,0.4)" fontSize="7">Synthesis Parameters</text>
        <text x="10" y="31" textAnchor="middle" fill="rgba(200,216,232,0.4)" fontSize="7" transform="rotate(-90,10,31)">Property</text>
      </svg>
    </div>
  </div>
)

const HeroSection: React.FC = () => {
  const scrollTo = (id: string) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <section id="hero" className="lp-hero" aria-labelledby="hero-heading">
      <div className="lp-container">
        <div className="lp-hero-inner">
          {/* Left: Text */}
          <div className="lp-slide-up">
            <div className="lp-hero-eyebrow" aria-hidden="false">
              <span className="lp-hero-eyebrow-dot" />
              GREEN SYNTHESIS&nbsp;•&nbsp;P1–P8 RESEARCH PORTFOLIO&nbsp;•&nbsp;DATA INTELLIGENCE
            </div>

            <h1 id="hero-heading" className="lp-hero-title">
              Data-Driven Intelligence for{' '}
              <span className="lp-hero-title-accent">Green Synthesis Research</span>
            </h1>

            <p className="lp-hero-desc">
              GreenSynth Analytics brings green synthesis experiments, semiconductor
              characterization, scientific calculations, statistical analysis, machine learning,
              and optimization together in one structured research platform.
            </p>

            <p className="lp-hero-desc-secondary">
              Supporting <strong style={{ color: 'rgba(200,216,232,0.9)' }}>eight research projects</strong> across
              CuO and Silica/Silicon synthesis — using sol-gel, hydrothermal, and spray-pyrolysis
              methods with ethanol and acetone solvents.
            </p>

            <div className="lp-hero-actions">
              <button
                className="lp-btn-primary"
                id="hero-explore-btn"
                onClick={() => scrollTo('research-portfolio')}
                aria-label="Explore the research portfolio — all P1 to P8 projects"
              >
                Explore Research Platform
                <ArrowRight size={16} aria-hidden="true" />
              </button>
              <Link
                to="/login"
                className="lp-btn-secondary"
                id="hero-signin-btn"
                aria-label="Sign in to GreenSynth Analytics"
              >
                Sign In
              </Link>
            </div>
          </div>

          {/* Right: Visualization */}
          <div className="lp-hero-visual lp-fade-in" role="img" aria-label="Research portfolio overview visualization">
            <HeroVisualization />
          </div>
        </div>

        {/* Scroll indicator */}
        <div style={{ textAlign: 'center', marginTop: '36px' }}>
          <button
            onClick={() => scrollTo('platform-overview')}
            aria-label="Scroll down to explore"
            style={{
              background: 'none', border: 'none', color: 'rgba(200,216,232,0.4)',
              cursor: 'pointer', padding: '8px',
              animation: 'lp-slideUp 1s ease infinite alternate',
            }}
          >
            <ChevronDown size={20} />
          </button>
        </div>
      </div>
    </section>
  )
}

export default HeroSection
