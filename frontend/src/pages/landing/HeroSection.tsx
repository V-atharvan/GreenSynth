/**
 * GreenSynth Analytics — Hero Section
 * Main landing hero with left text content and right scientific data visualization.
 */

import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, FlaskConical, BarChart3, Cpu, ChevronDown } from 'lucide-react'

const HeroVisualization: React.FC = () => (
  <div className="lp-hero-vis-card" aria-hidden="true">
    <div className="lp-hero-vis-title">Research Analytics Overview</div>

    {/* Mini stat chips */}
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '16px' }}>
      {[
        { icon: <FlaskConical size={14} />, label: 'Experiments', val: '24', color: '#3b9ede' },
        { icon: <BarChart3 size={14} />,   label: 'Samples',     val: '96', color: '#1e8a4a' },
        { icon: <Cpu size={14} />,         label: 'ML Models',   val: '8',  color: '#b8740a' },
        { icon: <FlaskConical size={14} />,label: 'Validated',   val: '12', color: '#6d28d9' },
      ].map((s) => (
        <div key={s.label} style={{
          background: 'rgba(255,255,255,0.07)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '8px',
          padding: '10px 12px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          <span style={{ color: s.color }}>{s.icon}</span>
          <div>
            <div style={{ fontSize: '1.125rem', fontWeight: 800, color: '#ffffff', lineHeight: 1 }}>{s.val}</div>
            <div style={{ fontSize: '0.625rem', color: 'rgba(200,216,232,0.6)', textTransform: 'uppercase', letterSpacing: '0.07em', marginTop: 2 }}>{s.label}</div>
          </div>
        </div>
      ))}
    </div>

    {/* Workflow mini-pipeline */}
    <div style={{ marginBottom: '16px' }}>
      <div style={{ fontSize: '0.625rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'rgba(200,216,232,0.45)', marginBottom: '8px' }}>
        Research Pipeline
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
        {['Project', 'Experiment', 'Sample', 'Characterization', 'Analysis', 'ML', 'Validation'].map((step, i, arr) => (
          <React.Fragment key={step}>
            <span style={{
              fontSize: '0.625rem',
              fontWeight: 600,
              color: 'rgba(200,216,232,0.8)',
              background: 'rgba(255,255,255,0.07)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '4px',
              padding: '3px 7px',
              whiteSpace: 'nowrap',
            }}>{step}</span>
            {i < arr.length - 1 && (
              <span style={{ color: 'rgba(200,216,232,0.3)', fontSize: '0.625rem' }}>›</span>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>

    {/* Conceptual scatter plot */}
    <div style={{ background: 'rgba(0,0,0,0.15)', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
      <div style={{ fontSize: '0.625rem', color: 'rgba(200,216,232,0.4)', marginBottom: '8px', fontStyle: 'italic' }}>
        Conceptual visualization — illustrative data
      </div>
      <svg width="100%" height="80" viewBox="0 0 300 80" aria-label="Conceptual data scatter plot">
        {/* Axes */}
        <line x1="20" y1="70" x2="290" y2="70" stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
        <line x1="20" y1="10" x2="20"  y2="70" stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
        {/* Trend line */}
        <line x1="30" y1="65" x2="280" y2="18" stroke="#3b9ede" strokeWidth="1.5" strokeDasharray="4,3" opacity="0.6" />
        {/* Data points */}
        {[
          [40,60],[70,54],[95,48],[120,42],[145,40],[170,33],[195,28],[220,24],[250,20],[275,18]
        ].map(([x,y], i) => (
          <circle key={i} cx={x} cy={y} r="3.5" fill="#3b9ede" opacity="0.8" />
        ))}
        {/* Axis labels */}
        <text x="155" y="78" textAnchor="middle" fill="rgba(200,216,232,0.4)" fontSize="8">Substrate Temperature (°C)</text>
        <text x="10" y="40" textAnchor="middle" fill="rgba(200,216,232,0.4)" fontSize="8" transform="rotate(-90,10,40)">Conductivity</text>
      </svg>
    </div>

    {/* CuO material label */}
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      background: 'rgba(30,138,74,0.12)',
      border: '1px solid rgba(52,211,153,0.2)',
      borderRadius: '6px',
      padding: '8px 12px',
    }}>
      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#34d399', flexShrink: 0 }} />
      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'rgba(200,216,232,0.85)' }}>
        CuO — Phytochemical Green Synthesis via Spray Pyrolysis
      </div>
    </div>
  </div>
)

const HeroSection: React.FC = () => {
  const scrollToWorkflow = () => {
    const el = document.getElementById('workflow')
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
              GREEN SYNTHESIS&nbsp;•&nbsp;DATA&nbsp;•&nbsp;INTELLIGENCE
            </div>

            <h1 id="hero-heading" className="lp-hero-title">
              Transforming Green Synthesis Research with{' '}
              <span className="lp-hero-title-accent">Data and Intelligence</span>
            </h1>

            <p className="lp-hero-desc">
              GreenSynth Analytics is a research and analytics platform for designing, managing,
              analyzing, and optimizing green synthesis experiments for semiconductor materials.
            </p>

            <p className="lp-hero-desc-secondary">
              From green synthesis experiments to characterization, statistical analysis, machine
              learning, optimization, and experimental validation.
            </p>

            <div className="lp-hero-actions">
              <button
                className="lp-btn-primary"
                id="hero-explore-btn"
                onClick={scrollToWorkflow}
                aria-label="Explore the research platform workflow"
              >
                Explore Platform
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

          {/* Right: Scientific visualization */}
          <div className="lp-hero-visual lp-fade-in" role="img" aria-label="Research analytics overview visualization">
            <HeroVisualization />
          </div>
        </div>

        {/* Scroll indicator */}
        <div style={{ textAlign: 'center', marginTop: '40px' }}>
          <button
            onClick={scrollToWorkflow}
            aria-label="Scroll down to explore"
            style={{
              background: 'none',
              border: 'none',
              color: 'rgba(200,216,232,0.4)',
              cursor: 'pointer',
              padding: '8px',
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
