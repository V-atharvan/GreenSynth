/**
 * GreenSynth Analytics — Research Portfolio Section
 * Displays all P1–P8 research projects with a filter bar and research group summaries.
 * This is the main correction: the platform supports multiple projects, not just P7.
 */

import React, { useState, useCallback } from 'react'
import { Atom, Droplets, Flame, Beaker, FlaskConical, Star } from 'lucide-react'
import {
  PROJECTS, PROJECT_GROUPS, FILTER_OPTIONS,
  filterProjects, type Project, type FilterKey,
} from './landingData'

/* ── Material / method icons ─────────────────────────────── */
function MaterialIcon({ material }: { material: Project['material'] }) {
  if (material === 'CuO') return <Atom size={16} aria-hidden="true" />
  return <Beaker size={16} aria-hidden="true" />
}

function MethodIcon({ method }: { method: Project['method'] }) {
  if (method === 'Spray Pyrolysis') return <Flame size={13} aria-hidden="true" />
  if (method === 'Hydrothermal') return <Droplets size={13} aria-hidden="true" />
  return <FlaskConical size={13} aria-hidden="true" />
}

/* ── Color maps ──────────────────────────────────────────── */
const MATERIAL_COLOR: Record<Project['material'], { color: string; bg: string; border: string }> = {
  'CuO':           { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)',   border: 'rgba(245,158,11,0.25)' },
  'Silica/Silicon':{ color: '#3b9ede', bg: 'rgba(59,158,222,0.1)',   border: 'rgba(59,158,222,0.25)' },
}

const METHOD_COLOR: Record<Project['method'], { color: string; bg: string }> = {
  'Sol-gel':        { color: '#8b5cf6', bg: 'rgba(139,92,246,0.12)' },
  'Hydrothermal':   { color: '#3b9ede', bg: 'rgba(59,158,222,0.12)' },
  'Spray Pyrolysis':{ color: '#f97316', bg: 'rgba(249,115,22,0.12)' },
}

const SOLVENT_COLOR: Record<Project['solvent'], { color: string; bg: string }> = {
  'Ethanol': { color: '#34d399', bg: 'rgba(52,211,153,0.12)' },
  'Acetone': { color: '#f472b6', bg: 'rgba(244,114,182,0.12)' },
}

/* ── Single project card ─────────────────────────────────── */
const ProjectCard: React.FC<{ project: Project }> = ({ project: p }) => {
  const mc = MATERIAL_COLOR[p.material]
  const me = METHOD_COLOR[p.method]
  const sc = SOLVENT_COLOR[p.solvent]

  return (
    <article
      className={`lp-proj-card${p.featured ? ' lp-proj-card-featured' : ''}`}
      aria-label={`Project ${p.id}: ${p.title}`}
    >
      {/* Header row */}
      <div className="lp-proj-card-header">
        <span className="lp-proj-id-badge">{p.id}</span>
        {p.featured && (
          <span className="lp-proj-featured-badge" aria-label="Featured case study">
            <Star size={10} aria-hidden="true" /> Featured
          </span>
        )}
        <div className="lp-proj-material-icon" style={{ color: mc.color, background: mc.bg, border: `1px solid ${mc.border}` }}>
          <MaterialIcon material={p.material} />
        </div>
      </div>

      {/* Title */}
      <h3 className="lp-proj-card-title">{p.title}</h3>

      {/* Key fields */}
      <dl className="lp-proj-fields">
        <div className="lp-proj-field">
          <dt>Material</dt>
          <dd style={{ color: mc.color, fontWeight: 700 }}>{p.material}</dd>
        </div>
        <div className="lp-proj-field">
          <dt>Green Component{p.greenComponents.length > 1 ? 's' : ''}</dt>
          <dd>{p.greenComponents.join(' · ')}</dd>
        </div>
        <div className="lp-proj-field">
          <dt>Solvent</dt>
          <dd>{p.solvent}</dd>
        </div>
        <div className="lp-proj-field">
          <dt>Synthesis Method</dt>
          <dd>{p.method}</dd>
        </div>
      </dl>

      {/* Tags */}
      <div className="lp-proj-tags">
        <span className="lp-proj-tag" style={{ color: me.color, background: me.bg }}>
          <MethodIcon method={p.method} /> {p.method}
        </span>
        <span className="lp-proj-tag" style={{ color: sc.color, background: sc.bg }}>
          {p.solvent}
        </span>
      </div>
    </article>
  )
}

/* ── Research group summary ──────────────────────────────── */
const GroupSummary: React.FC = () => (
  <div className="lp-group-grid" aria-label="Research project groupings">
    {PROJECT_GROUPS.map((g) => (
      <div key={g.id} className="lp-group-card" style={{ borderColor: g.color }}>
        <div className="lp-group-dot" style={{ background: g.color }} />
        <div>
          <div className="lp-group-title" style={{ color: g.color }}>{g.label}</div>
          <div className="lp-group-projects">
            {g.projects.map((pid) => (
              <span key={pid} className="lp-group-pid">{pid}</span>
            ))}
          </div>
          <p className="lp-group-desc">{g.description}</p>
        </div>
      </div>
    ))}
  </div>
)

/* ── Main section ────────────────────────────────────────── */
const ResearchPortfolioSection: React.FC = () => {
  const [activeFilter, setActiveFilter] = useState<FilterKey>('all')

  const filtered = filterProjects(PROJECTS, activeFilter)

  const handleFilter = useCallback((key: FilterKey) => {
    setActiveFilter(key)
  }, [])

  return (
    <section
      id="research-portfolio"
      className="lp-section lp-section-alt"
      aria-labelledby="portfolio-heading"
    >
      <div className="lp-container">
        {/* Header */}
        <div className="lp-section-header">
          <span className="lp-section-label">Research Portfolio</span>
          <h2 id="portfolio-heading" className="lp-section-heading">
            Research Projects Across Green Synthesis
          </h2>
          <p className="lp-section-subheading">
            GreenSynth Analytics supports multiple green-synthesis research pathways involving
            different semiconductor materials, plant-based resources, solvents, and synthesis
            methods. Each project can be managed and analyzed through a common research workflow
            while preserving its own scientific parameters and characterization requirements.
          </p>
        </div>

        {/* Filter bar */}
        <div className="lp-filter-bar" role="group" aria-label="Filter research projects">
          {FILTER_OPTIONS.map(({ key, label }) => (
            <button
              key={key}
              className={`lp-filter-btn${activeFilter === key ? ' lp-filter-btn-active' : ''}`}
              onClick={() => handleFilter(key)}
              aria-pressed={activeFilter === key}
              id={`filter-${key.replace(/\//g, '-').replace(/\s/g, '-').toLowerCase()}`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Project count */}
        <div className="lp-portfolio-count" aria-live="polite">
          Showing {filtered.length} of {PROJECTS.length} research projects
        </div>

        {/* Cards grid */}
        <div
          className="lp-proj-grid"
          role="list"
          aria-label={`Research projects${activeFilter !== 'all' ? ` filtered by ${activeFilter}` : ''}`}
        >
          {filtered.map((p) => (
            <div key={p.id} role="listitem">
              <ProjectCard project={p} />
            </div>
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="lp-portfolio-empty">
            No projects match the selected filter. <button className="lp-portfolio-clear" onClick={() => setActiveFilter('all')}>Show all projects</button>
          </div>
        )}

        {/* Divider */}
        <div className="lp-section-divider" aria-hidden="true" />

        {/* Group summaries */}
        <div style={{ marginTop: '48px' }}>
          <div className="lp-section-header" style={{ marginBottom: '32px' }}>
            <span className="lp-section-label lp-section-label-blue">Scientific Groupings</span>
            <h3 className="lp-section-heading" style={{ fontSize: '1.5rem' }}>
              Research Focus Areas
            </h3>
          </div>
          <GroupSummary />
        </div>
      </div>
    </section>
  )
}

export default ResearchPortfolioSection
