/**
 * GreenSynth Analytics — Public Landing Page
 *
 * Composes all landing-page sections in the specified order.
 * This page is accessible at "/" without authentication.
 * It does NOT use MainLayout, AuthProvider requirements, or any authenticated components.
 *
 * Section order per specification:
 *  1. Navbar
 *  2. Hero
 *  3. Primary Research Case Study (Callout)
 *  4. Research Focus
 *  5. Complete Research Workflow
 *  6. Platform Modules
 *  7. Data → Intelligence
 *  8. Characterization
 *  9. Statistical Analysis
 * 10. Machine Learning
 * 11. Optimization
 * 12. Research Traceability
 * 13. Dashboard Preview
 * 14. Security / Research Integrity (+ Case Study Detail)
 * 15. Why GreenSynth
 * 16. Final CTA
 * 17. Footer
 */

import React, { useEffect } from 'react'

import LandingNavbar           from './LandingNavbar'
import HeroSection             from './HeroSection'
import CaseStudyCallout        from './CaseStudyCallout'
import ResearchFocusSection    from './ResearchFocusSection'
import WorkflowSection         from './WorkflowSection'
import PlatformModulesSection  from './PlatformModulesSection'
import DataIntelligenceSection from './DataIntelligenceSection'
import CharacterizationSection from './CharacterizationSection'
import StatisticsSection       from './StatisticsSection'
import MachineLearningSection  from './MachineLearningSection'
import OptimizationSection     from './OptimizationSection'
import TraceabilitySection     from './TraceabilitySection'
import DashboardPreviewSection from './DashboardPreviewSection'
import SecuritySection         from './SecuritySection'
import CaseStudyDetailSection  from './CaseStudyDetailSection'
import WhyGreenSynthSection    from './WhyGreenSynthSection'
import FinalCTASection         from './FinalCTASection'
import LandingFooter           from './LandingFooter'

import '../../styles/landing.css'

const LandingPage: React.FC = () => {
  // Update document title and meta description for SEO
  useEffect(() => {
    const prevTitle = document.title
    document.title =
      'GreenSynth Analytics | Data-Driven Green Synthesis Research Platform'

    // Meta description
    let metaDesc = document.querySelector<HTMLMetaElement>('meta[name="description"]')
    const prevDesc = metaDesc?.content ?? ''
    if (!metaDesc) {
      metaDesc = document.createElement('meta')
      metaDesc.name = 'description'
      document.head.appendChild(metaDesc)
    }
    metaDesc.content =
      'GreenSynth Analytics is a data-driven research and analytics platform for green synthesis of semiconductor materials, connecting experiments, characterization, statistical analysis, machine learning, optimization, and validation.'

    return () => {
      document.title = prevTitle
      if (metaDesc) metaDesc.content = prevDesc
    }
  }, [])

  return (
    <div className="lp-root" id="lp-root">
      {/* Skip to main content for accessibility */}
      <a
        href="#hero"
        className="sr-only"
        style={{
          position: 'absolute',
          top: '8px',
          left: '8px',
          zIndex: 9999,
          background: '#ffffff',
          color: '#1e3a5f',
          padding: '8px 16px',
          borderRadius: '4px',
          fontWeight: 600,
          fontSize: '0.875rem',
          textDecoration: 'none',
        }}
        onFocus={(e) => {
          e.currentTarget.style.position = 'fixed'
          e.currentTarget.style.clip = 'auto'
          e.currentTarget.style.width = 'auto'
          e.currentTarget.style.height = 'auto'
        }}
        onBlur={(e) => {
          e.currentTarget.style.position = 'absolute'
        }}
      >
        Skip to main content
      </a>

      {/* ── 1. Navigation ───────────────────────────────── */}
      <LandingNavbar />

      {/* ── Main Content ────────────────────────────────── */}
      <main id="main-content">
        {/* ── 2. Hero ──────────────────────────────────── */}
        <HeroSection />

        {/* ── 3. Primary Case Study Callout ─────────────── */}
        <CaseStudyCallout />

        {/* ── 4. Research Focus ────────────────────────── */}
        <ResearchFocusSection />

        {/* ── 5. Research Workflow ──────────────────────── */}
        <WorkflowSection />

        {/* ── 6. Platform Modules ───────────────────────── */}
        <PlatformModulesSection />

        {/* ── 7. Data → Intelligence ───────────────────── */}
        <DataIntelligenceSection />

        {/* ── 8. Characterization ──────────────────────── */}
        <CharacterizationSection />

        {/* ── 9. Statistical Analysis ──────────────────── */}
        <StatisticsSection />

        {/* ── 10. Machine Learning ─────────────────────── */}
        <MachineLearningSection />

        {/* ── 11. Optimization ──────────────────────────── */}
        <OptimizationSection />

        {/* ── 12. Traceability ──────────────────────────── */}
        <TraceabilitySection />

        {/* ── 13. Dashboard Preview ─────────────────────── */}
        <DashboardPreviewSection />

        {/* ── 14a. Security / Research Integrity ────────── */}
        <SecuritySection />

        {/* ── 14b. Case Study Detail ─────────────────────── */}
        <CaseStudyDetailSection />

        {/* ── 15. Why GreenSynth ───────────────────────── */}
        <WhyGreenSynthSection />

        {/* ── 16. Final CTA ─────────────────────────────── */}
        <FinalCTASection />
      </main>

      {/* ── 17. Footer ──────────────────────────────────── */}
      <LandingFooter />
    </div>
  )
}

export default LandingPage
