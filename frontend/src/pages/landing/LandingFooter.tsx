/**
 * GreenSynth Analytics — Landing Footer
 * Updated: expanded Research Focus tags, added "Research Projects" link,
 * added scientific disclaimer note.
 */

import React from 'react'
import { Link } from 'react-router-dom'
import { Dna } from 'lucide-react'

const LandingFooter: React.FC = () => {
  const scrollTo = (id: string) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <footer className="lp-footer" aria-label="Site footer">
      <div className="lp-container">
        <div className="lp-footer-main">
          {/* Brand */}
          <div>
            <div className="lp-footer-logo-mark" aria-hidden="true" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <img
                src="/branding/greensynth-mark.png"
                alt="GreenSynth Logo"
                style={{ width: '26px', height: '26px', objectFit: 'contain' }}
              />
            </div>
            <div className="lp-footer-brand-name">GreenSynth Analytics</div>
            <div className="lp-footer-brand-desc">
              A data-driven research and analytics platform for green synthesis of semiconductor materials.
            </div>
          </div>

          {/* Navigation */}
          <div>
            <div className="lp-footer-col-title">Navigation</div>
            <ul className="lp-footer-links" role="list">
              {[
                { label: 'Home',              id: 'hero' },
                { label: 'Research Projects', id: 'research-portfolio' },
                { label: 'Platform',         id: 'platform-modules' },
                { label: 'Workflow',         id: 'workflow' },
                { label: 'About',            id: 'why-greensynth' },
              ].map(({ label, id }) => (
                <li key={id}>
                  <button className="lp-footer-link" onClick={() => scrollTo(id)}>
                    {label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Application */}
          <div>
            <div className="lp-footer-col-title">Application</div>
            <ul className="lp-footer-links" role="list">
              <li>
                <Link to="/login" className="lp-footer-link" id="footer-signin-link">
                  Sign In
                </Link>
              </li>
            </ul>
          </div>

          {/* Research Focus */}
          <div>
            <div className="lp-footer-col-title">Research Focus</div>
            <ul className="lp-footer-links" role="list">
              {[
                'CuO',
                'Silica / Silicon',
                'Plant-based Green Synthesis',
                'Sol-gel',
                'Hydrothermal',
                'Spray Pyrolysis',
                'Characterization',
                'Machine Learning',
                'DOE & Optimization',
              ].map((t) => (
                <li key={t}>
                  <span className="lp-footer-link" style={{ cursor: 'default' }}>{t}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Disclaimer note */}
        <div className="lp-footer-disclaimer" role="note">
          GreenSynth Analytics supports scientific decision-making. Experimental recommendations
          require physical testing and validation before being treated as scientific conclusions.
        </div>

        <div className="lp-footer-bottom">
          <div className="lp-footer-bottom-left">
            <span style={{ fontWeight: 700, color: 'rgba(200,216,232,0.6)' }}>GreenSynth Analytics</span>
            <span>·</span>
            <span>Research Platform</span>
          </div>
          <div className="lp-footer-bottom-right">
            Data-Driven Green Synthesis Research — P1 to P8
          </div>
        </div>
      </div>
    </footer>
  )
}

export default LandingFooter
