/**
 * GreenSynth Analytics — Main Layout
 *
 * Responsive layout supporting Desktop (fixed sidebar), Tablet (collapsible),
 * and Mobile (top header + slide-out navigation drawer with overlay).
 */

import React, { useState, useEffect } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderKanban,
  FlaskConical,
  TestTube2,
  BarChart3,
  Cpu,
  ShieldCheck,
  Lightbulb,
  RotateCw,
  Ruler,
  BarChart2,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  Menu,
  X,
  Dna,
} from 'lucide-react'
import './MainLayout.css'

interface NavItem {
  to: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  end?: boolean
}

const NAV_ITEMS: NavItem[] = [
  { to: '/',                label: 'Dashboard',             icon: LayoutDashboard, end: true },
  { to: '/projects',        label: 'Projects',              icon: FolderKanban },
  { to: '/experiments',     label: 'Experiments',           icon: FlaskConical },
  { to: '/samples',         label: 'Samples',               icon: TestTube2 },
  { to: '/comparison',      label: 'Sample Comparison',     icon: BarChart3 },
  { to: '/ml',              label: 'Machine Learning',      icon: Cpu },
  { to: '/validation',      label: 'Validation & Drift',    icon: ShieldCheck },
  { to: '/recommendations', label: 'Recommendation Studio',icon: Lightbulb },
  { to: '/closed-loop',     label: 'Research Loop',        icon: RotateCw },
  { to: '/doe',             label: 'Design of Experiments', icon: Ruler },
  { to: '/statistics',      label: 'Statistical Evidence', icon: BarChart2 },
  { to: '/optimization',    label: 'Experimental Optimization', icon: Ruler },
]

const FUTURE_ITEMS = [
  { label: 'Analysis',       icon: BarChart3, phase: 'Phase 6–9' },
  { label: 'Statistics',     icon: TrendingUp, phase: 'Phase 11' },
  { label: 'ML & Predict',   icon: Cpu, phase: 'Phase 14–16' },
]

export default function MainLayout() {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false)

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileDrawerOpen(false)
  }, [location.pathname])

  // ESC key handler to close mobile drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && mobileDrawerOpen) {
        setMobileDrawerOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [mobileDrawerOpen])

  return (
    <div className={`layout ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>

      {/* ── Mobile Header Bar (visible on screens <= 1024px) ───────── */}
      <header className="mobile-header">
        <div className="mobile-header-left">
          <button
            className="mobile-hamburger-btn"
            onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
            aria-label={mobileDrawerOpen ? 'Close Navigation Menu' : 'Open Navigation Menu'}
            aria-expanded={mobileDrawerOpen}
          >
            {mobileDrawerOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
          <div className="mobile-brand-title">
            <Dna className="w-5 h-5 text-emerald-400" />
            <span className="mobile-brand-name">GreenSynth</span>
          </div>
        </div>
        <div className="mobile-header-right">
          <span className="mobile-mode-badge" title="Research Mode Active">
            <FlaskConical className="w-3.5 h-3.5" />
            <span className="mobile-mode-text">Research</span>
          </span>
        </div>
      </header>

      {/* ── Backdrop Overlay for Mobile Drawer ─────────────────────── */}
      {mobileDrawerOpen && (
        <div
          className="mobile-drawer-backdrop"
          onClick={() => setMobileDrawerOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* ── Desktop & Mobile Slide-Out Sidebar ─────────────────────── */}
      <aside
        className={`sidebar ${mobileDrawerOpen ? 'mobile-drawer-open' : ''}`}
        role="navigation"
        aria-label="Main navigation"
      >
        {/* Logo / Brand Header */}
        <div className="sidebar-brand">
          <div className="brand-icon">
            <Dna className="w-6 h-6 text-emerald-400" />
          </div>
          {(sidebarOpen || mobileDrawerOpen) && (
            <div className="brand-text">
              <div className="brand-name">GreenSynth</div>
              <div className="brand-sub">Analytics Platform</div>
            </div>
          )}
          {/* Desktop Toggle Button */}
          <button
            className="sidebar-toggle desktop-only-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle desktop sidebar"
            title="Toggle sidebar width"
          >
            {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
          {/* Mobile Drawer Close Button */}
          <button
            className="mobile-drawer-close-btn"
            onClick={() => setMobileDrawerOpen(false)}
            aria-label="Close navigation drawer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Primary Navigation List */}
        <nav className="sidebar-nav">
          {(sidebarOpen || mobileDrawerOpen) && (
            <div className="nav-section-label">Research</div>
          )}
          {NAV_ITEMS.map((item) => {
            const IconComp = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `nav-item ${isActive ? 'active' : ''}`
                }
                title={!sidebarOpen && !mobileDrawerOpen ? item.label : undefined}
                onClick={() => setMobileDrawerOpen(false)}
              >
                <span className="nav-icon" aria-hidden="true">
                  <IconComp className="w-4.5 h-4.5" />
                </span>
                {(sidebarOpen || mobileDrawerOpen) && (
                  <span className="nav-label">{item.label}</span>
                )}
              </NavLink>
            )
          })}

          {/* Future / Coming Soon items */}
          {(sidebarOpen || mobileDrawerOpen) && (
            <>
              <div className="nav-section-label nav-section-label-future">
                Coming Soon
              </div>
              {FUTURE_ITEMS.map((item) => {
                const IconComp = item.icon
                return (
                  <div key={item.label} className="nav-item nav-item-disabled" title={`Available in ${item.phase}`}>
                    <span className="nav-icon" aria-hidden="true">
                      <IconComp className="w-4.5 h-4.5" />
                    </span>
                    <span className="nav-label">{item.label}</span>
                    <span className="nav-badge">{item.phase}</span>
                  </div>
                )
              })}
            </>
          )}
        </nav>

        {/* Sidebar Footer */}
        {(sidebarOpen || mobileDrawerOpen) && (
          <div className="sidebar-footer">
            <div className="sidebar-footer-text">v0.1.0 — Phase 1</div>
            <div className="sidebar-footer-sub">MVP Foundation</div>
          </div>
        )}
      </aside>

      {/* ── Main Wrapper (Desktop Topbar + Scrollable Content) ───────── */}
      <div className="main-wrapper">
        {/* Desktop Topbar */}
        <header className="topbar">
          <div className="topbar-title">
            {getPageTitle(location.pathname)}
          </div>
          <div className="topbar-right">
            <span className="topbar-badge">
              <FlaskConical className="w-3.5 h-3.5" /> Research Mode
            </span>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="main-content" id="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function getPageTitle(pathname: string): string {
  if (pathname === '/') return 'Dashboard'
  if (pathname.startsWith('/projects')) return 'Projects'
  if (pathname.startsWith('/experiments')) return 'Experiments'
  if (pathname.startsWith('/samples')) return 'Samples'
  if (pathname.startsWith('/comparison')) return 'Sample Comparison'
  if (pathname.startsWith('/ml')) return 'Machine Learning'
  if (pathname.startsWith('/validation')) return 'Validation & Drift'
  if (pathname.startsWith('/recommendations')) return 'Recommendation Studio'
  if (pathname.startsWith('/closed-loop')) return 'Research Loop'
  if (pathname.startsWith('/doe')) return 'Design of Experiments'
  if (pathname.startsWith('/statistics')) return 'Statistical Evidence'
  if (pathname.startsWith('/optimization')) return 'Evidence-Based Optimization'
  return 'GreenSynth Analytics'
}
