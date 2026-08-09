/**
 * GreenSynth Analytics — Main Layout
 *
 * Fixed sidebar navigation + scrollable main content area.
 */

import React, { useState } from 'react'
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
  Dna,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
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

  return (
    <div className={`layout ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>

      {/* ── Sidebar ─────────────────────────────────────── */}
      <aside className="sidebar" role="navigation" aria-label="Main navigation">

        {/* Logo / Brand */}
        <div className="sidebar-brand">
          <div className="brand-icon" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Dna className="w-6 h-6 text-emerald-400" />
          </div>
          {sidebarOpen && (
            <div className="brand-text">
              <div className="brand-name">GreenSynth</div>
              <div className="brand-sub">Analytics Platform</div>
            </div>
          )}
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle sidebar"
            title="Toggle sidebar"
          >
            {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>

        {/* Primary navigation */}
        <nav className="sidebar-nav">
          {sidebarOpen && (
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
                title={!sidebarOpen ? item.label : undefined}
              >
                <span className="nav-icon" aria-hidden="true" style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
                  <IconComp className="w-4.5 h-4.5" />
                </span>
                {sidebarOpen && <span className="nav-label">{item.label}</span>}
              </NavLink>
            )
          })}

          {/* Future/locked features */}
          {sidebarOpen && (
            <>
              <div className="nav-section-label nav-section-label-future">
                Coming Soon
              </div>
              {FUTURE_ITEMS.map((item) => {
                const IconComp = item.icon
                return (
                  <div key={item.label} className="nav-item nav-item-disabled" title={`Available in ${item.phase}`}>
                    <span className="nav-icon" style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
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

        {/* Footer */}
        {sidebarOpen && (
          <div className="sidebar-footer">
            <div className="sidebar-footer-text">v0.1.0 — Phase 1</div>
            <div className="sidebar-footer-sub">MVP Foundation</div>
          </div>
        )}
      </aside>

      {/* ── Main content ─────────────────────────────────── */}
      <div className="main-wrapper">
        {/* Top bar */}
        <header className="topbar">
          <div className="topbar-title">
            {getPageTitle(location.pathname)}
          </div>
          <div className="topbar-right">
            <span className="topbar-badge" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <FlaskConical className="w-3.5 h-3.5" /> Research Mode
            </span>
          </div>
        </header>

        {/* Page content */}
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
