/**
 * GreenSynth Analytics — Landing Navbar
 * Sticky navigation bar with hamburger menu for mobile.
 */

import React, { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Menu, X } from 'lucide-react'

const LandingNavbar: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false)

  const scrollTo = useCallback((id: string) => {
    setMobileOpen(false)
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [])

  return (
    <nav className="lp-navbar" role="navigation" aria-label="Main navigation">
      <div className="lp-container">
        <div className="lp-navbar-inner">
          {/* Brand */}
          <a href="#hero" className="lp-navbar-brand" aria-label="GreenSynth Analytics — Home"
            onClick={(e) => { e.preventDefault(); scrollTo('hero') }}>
            <img
              src="/branding/greensynth-logo-dark-horizontal.png"
              alt="GreenSynth logo"
              className="lp-navbar-logo"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
            <div className="lp-navbar-brand-text">
              <span className="lp-navbar-brand-name">GreenSynth</span>
              <span className="lp-navbar-brand-sub">Analytics Platform</span>
            </div>
          </a>

          {/* Desktop links */}
          <ul className="lp-navbar-links" role="list">
            {[
              { label: 'Home',     id: 'hero' },
              { label: 'Research', id: 'research-focus' },
              { label: 'Platform', id: 'platform-modules' },
              { label: 'Workflow', id: 'workflow' },
              { label: 'About',   id: 'why-greensynth' },
            ].map(({ label, id }) => (
              <li key={id}>
                <button
                  className="lp-navbar-link"
                  onClick={() => scrollTo(id)}
                  aria-label={`Navigate to ${label}`}
                >
                  {label}
                </button>
              </li>
            ))}
          </ul>

          {/* Desktop actions */}
          <div className="lp-navbar-actions">
            <Link to="/login" className="lp-btn-nav-signin" id="navbar-signin-btn">
              Sign In
            </Link>
          </div>

          {/* Hamburger */}
          <button
            className="lp-hamburger"
            aria-label={mobileOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={mobileOpen}
            aria-controls="lp-mobile-nav"
            onClick={() => setMobileOpen((o) => !o)}
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

        {/* Mobile drawer */}
        <nav
          id="lp-mobile-nav"
          className={`lp-mobile-nav${mobileOpen ? ' lp-open' : ''}`}
          aria-hidden={!mobileOpen}
        >
          {[
            { label: 'Home',     id: 'hero' },
            { label: 'Research', id: 'research-focus' },
            { label: 'Platform', id: 'platform-modules' },
            { label: 'Workflow', id: 'workflow' },
            { label: 'About',   id: 'why-greensynth' },
          ].map(({ label, id }) => (
            <button
              key={id}
              className="lp-mobile-nav-link"
              onClick={() => scrollTo(id)}
            >
              {label}
            </button>
          ))}
          <div className="lp-mobile-nav-divider" aria-hidden="true" />
          <Link
            to="/login"
            className="lp-mobile-nav-signin"
            onClick={() => setMobileOpen(false)}
            id="mobile-signin-btn"
          >
            Sign In
          </Link>
        </nav>
      </div>
    </nav>
  )
}

export default LandingNavbar
