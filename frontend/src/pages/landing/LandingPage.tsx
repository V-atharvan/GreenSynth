/**
 * GreenSynth Analytics — Public Landing Page
 *
 * Composes all landing-page sections in the specified order.
 * This page is accessible at "/" without authentication.
 * It does NOT use MainLayout, AuthProvider requirements, or any authenticated components.
 *
 * Section order (redesigned for multi-project scope):
 *  1. Navbar
 *  2. Hero
 *  3. Platform Overview ("What Is GreenSynth Analytics?")
 *  4. Research Portfolio (P1–P8 cards + filter + groups)
 *  5. Research Workflow
 *  6. Research Variables
 *  7. Characterization
 *  8. Statistical Analysis
 *  9. Machine Learning
 * 10. Data → Intelligence Loop
 * 11. Featured Case Study (P7)
 * 12. Research Traceability
 * 13. Platform Modules
 * 14. Research Impact ("Why GreenSynth")
 * 15. Final CTA
 * 16. Footer
 */

import React, { useEffect } from 'react'

import LandingNavbar            from './LandingNavbar'
import HeroSection              from './HeroSection'
import PlatformOverviewSection  from './PlatformOverviewSection'
import ResearchPortfolioSection from './ResearchPortfolioSection'
import WorkflowSection          from './WorkflowSection'
import ResearchVariablesSection from './ResearchVariablesSection'
import CharacterizationSection  from './CharacterizationSection'
import StatisticsSection        from './StatisticsSection'
import MachineLearningSection   from './MachineLearningSection'
import DataIntelligenceSection  from './DataIntelligenceSection'
import CaseStudyDetailSection   from './CaseStudyDetailSection'
import TraceabilitySection      from './TraceabilitySection'
import PlatformModulesSection   from './PlatformModulesSection'
import WhyGreenSynthSection     from './WhyGreenSynthSection'
import FinalCTASection          from './FinalCTASection'
import LandingFooter            from './LandingFooter'

import '../../styles/landing.css'

const LandingPage: React.FC = () => {
  useEffect(() => {
    const prevTitle = document.title
    document.title = 'GreenSynth Analytics | Data-Driven Green Synthesis Research'

    let metaDesc = document.querySelector<HTMLMetaElement>('meta[name="description"]')
    const prevDesc = metaDesc?.content ?? ''
    if (!metaDesc) {
      metaDesc = document.createElement('meta')
      metaDesc.name = 'description'
      document.head.appendChild(metaDesc)
    }
    metaDesc.content =
      'GreenSynth Analytics is a research and analytics platform for managing green synthesis experiments, semiconductor characterization, scientific calculations, machine learning, optimization, and experimental validation across multiple research projects (P1–P8).'

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
          position: 'absolute', top: '8px', left: '8px', zIndex: 9999,
          background: '#ffffff', color: '#1e3a5f', padding: '8px 16px',
          borderRadius: '4px', fontWeight: 600, fontSize: '0.875rem', textDecoration: 'none',
        }}
        onFocus={(e) => {
          e.currentTarget.style.position = 'fixed'
          e.currentTarget.style.clip = 'auto'
          e.currentTarget.style.width = 'auto'
          e.currentTarget.style.height = 'auto'
        }}
        onBlur={(e) => { e.currentTarget.style.position = 'absolute' }}
      >
        Skip to main content
      </a>

      {/* ── 1. Navigation ───────────────────────────────── */}
      <LandingNavbar />

      {/* ── Main Content ────────────────────────────────── */}
      <main id="main-content">
        {/* ── 2. Hero ──────────────────────────────────── */}
        <HeroSection />

        {/* ── 3. Platform Overview ─────────────────────── */}
        <PlatformOverviewSection />

        {/* ── 4. Research Portfolio P1–P8 ──────────────── */}
        <ResearchPortfolioSection />

        {/* ── 5. Research Workflow ──────────────────────── */}
        <WorkflowSection />

        {/* ── 6. Research Variables ─────────────────────── */}
        <ResearchVariablesSection />

        {/* ── 7. Characterization ──────────────────────── */}
        <CharacterizationSection />

        {/* ── 8. Statistical Analysis ──────────────────── */}
        <StatisticsSection />

        {/* ── 9. Machine Learning ─────────────────────── */}
        <MachineLearningSection />

        {/* ── 10. Data → Intelligence Loop ─────────────── */}
        <DataIntelligenceSection />

        {/* ── 11. Featured Case Study: P7 ──────────────── */}
        <CaseStudyDetailSection />

        {/* ── 12. Research Traceability ─────────────────── */}
        <TraceabilitySection />

        {/* ── 13. Platform Modules ──────────────────────── */}
        <PlatformModulesSection />

        {/* ── 14. Research Impact ──────────────────────── */}
        <WhyGreenSynthSection />

        {/* ── 15. Final CTA ─────────────────────────────── */}
        <FinalCTASection />
      </main>

      {/* ── 16. Footer ──────────────────────────────────── */}
      <LandingFooter />
    </div>
  )
}

export default LandingPage
