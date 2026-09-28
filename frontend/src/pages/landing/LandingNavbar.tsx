/**
 * GreenSynth Analytics — Landing Navbar
 * Sticky navigation bar with hamburger menu for mobile.
 * Updated: added "Research Projects" nav link.
 */

import React, { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Dna, Menu, X } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'

const NAV_LINKS = [
  { label: 'Home',              id: 'hero' },
  { label: 'Research Projects', id: 'research-portfolio' },
  { label: 'Platform',         id: 'platform-modules' },
  { label: 'Workflow',         id: 'workflow' },
  { label: 'About',            id: 'why-greensynth' },
]

const LandingNavbar: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { isAuthenticated, isAdmin } = useAuth()
  const appDestination = isAdmin ? '/admin' : '/dashboard'

  const scrollTo = useCallback((id: string) => {
    setMobileOpen(false)
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [])

  return (
    <nav className="lp-navbar" role="navigation" aria-label="Main navigation">
      <div className="lp-container">
        <div className="lp-navbar-inner">
          {/* Brand */}
          <a href="#hero" className="lp-navbar-brand" aria-label="GreenSynth Analytics — Home"
            onClick={(e) => { e.preventDefault(); scrollTo('hero') }}>
            <div className="lp-navbar-logo-mark" aria-hidden="true">
              <Dna size={25} style={{ color: '#34d399' }} />
            </div>
            <div className="lp-navbar-brand-text">
              <span className="lp-navbar-brand-name">GreenSynth</span>
              <span className="lp-navbar-brand-sub">Analytics Platform</span>
            </div>
          </a>

          {/* Desktop links */}
          <ul className="lp-navbar-links" role="list">
            {NAV_LINKS.map(({ label, id }) => (
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
            <Link to={isAuthenticated ? appDestination : "/login"} className="lp-btn-nav-signin" id="navbar-signin-btn">
              {isAuthenticated ? (isAdmin ? 'Admin Portal' : 'Open Dashboard') : 'Sign In'}
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
          {NAV_LINKS.map(({ label, id }) => (
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
            to={isAuthenticated ? appDestination : "/login"}
            className="lp-mobile-nav-signin"
            onClick={() => setMobileOpen(false)}
            id="mobile-signin-btn"
          >
            {isAuthenticated ? (isAdmin ? 'Admin Portal' : 'Open Dashboard') : 'Sign In'}
          </Link>
        </nav>
      </div>
    </nav>
  )
}

export default LandingNavbar
