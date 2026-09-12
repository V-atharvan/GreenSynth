/**
 * GreenSynth Analytics — Landing Footer
 */

import React from 'react'
import { Link } from 'react-router-dom'

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
            <img
              src="/branding/greensynth-logo-dark-horizontal.png"
              alt="GreenSynth Analytics"
              style={{ height: '28px', marginBottom: '14px' }}
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
            <div className="lp-footer-brand-name">GreenSynth Analytics</div>
            <div className="lp-footer-brand-desc">
              A Data-Driven Research and Analytics Platform for Green Synthesis of Semiconductor Materials.
            </div>
          </div>

          {/* Navigation */}
          <div>
            <div className="lp-footer-col-title">Navigation</div>
            <ul className="lp-footer-links" role="list">
              {[
                { label: 'Home',     id: 'hero' },
                { label: 'Research', id: 'research-focus' },
                { label: 'Platform', id: 'platform-modules' },
                { label: 'Workflow', id: 'workflow' },
                { label: 'About',   id: 'why-greensynth' },
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
              {['Green Synthesis', 'Semiconductor Materials', 'CuO', 'Spray Pyrolysis', 'Phytochemical Synthesis'].map((t) => (
                <li key={t}>
                  <span className="lp-footer-link" style={{ cursor: 'default' }}>{t}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="lp-footer-bottom">
          <div className="lp-footer-bottom-left">
            <span style={{ fontWeight: 700, color: 'rgba(200,216,232,0.6)' }}>GreenSynth Analytics</span>
            <span>·</span>
            <span>Research Platform</span>
          </div>
          <div className="lp-footer-bottom-right">
            Data-Driven Green Synthesis Research
          </div>
        </div>
      </div>
    </footer>
  )
}

export default LandingFooter
