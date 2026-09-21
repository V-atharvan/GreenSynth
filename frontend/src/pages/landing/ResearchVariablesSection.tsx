/**
 * GreenSynth Analytics — Research Variables Section
 * Explains synthesis variables grouped by method, with a disclaimer
 * that parameters are project-specific and method-specific.
 */

import React, { useState } from 'react'
import { Flame, Droplets, FlaskConical, ChevronDown, ChevronUp } from 'lucide-react'

interface VariableGroup {
  id: string
  method: string
  icon: React.ReactNode
  color: string
  bg: string
  border: string
  projects: string[]
  variables: string[]
  note: string
}

const VARIABLE_GROUPS: VariableGroup[] = [
  {
    id: 'spray',
    method: 'Spray Pyrolysis',
    icon: <Flame size={18} />,
    color: '#f97316',
    bg: 'rgba(249,115,22,0.08)',
    border: 'rgba(249,115,22,0.25)',
    projects: ['P7', 'P8'],
    variables: [
      'Precursor concentration',
      'Precursor solution volume',
      'Green extract concentration',
      'Green extract volume',
      'Solvent volume',
      'Substrate temperature (°C)',
      'Spray rate (mL/min)',
      'Spray duration (min)',
      'Nozzle–substrate distance (cm)',
      'Carrier-gas pressure (bar)',
      'Spray cycles',
      'Ambient temperature',
      'Ambient relative humidity',
      'Precursor-to-extract ratio',
    ],
    note: 'Spray-pyrolysis projects use process variables related to spray conditions, substrate heating, and nozzle configuration.',
  },
  {
    id: 'hydrothermal',
    method: 'Hydrothermal',
    icon: <Droplets size={18} />,
    color: '#3b9ede',
    bg: 'rgba(59,158,222,0.08)',
    border: 'rgba(59,158,222,0.25)',
    projects: ['P3', 'P4', 'P5', 'P6'],
    variables: [
      'Precursor concentration',
      'Green extract concentration',
      'Solvent volume',
      'Hydrothermal temperature (°C)',
      'Hydrothermal duration (h)',
      'Autoclave pressure (bar)',
      'pH',
      'Calcination temperature (°C)',
      'Calcination duration (h)',
      'Precursor-to-extract ratio',
      'Aging time (h)',
    ],
    note: 'Hydrothermal projects record autoclave conditions, reaction duration, and post-synthesis calcination parameters.',
  },
  {
    id: 'solgel',
    method: 'Sol-Gel',
    icon: <FlaskConical size={18} />,
    color: '#8b5cf6',
    bg: 'rgba(139,92,246,0.08)',
    border: 'rgba(139,92,246,0.25)',
    projects: ['P1', 'P2'],
    variables: [
      'Precursor concentration',
      'Green extract concentration',
      'Solvent volume',
      'Sol preparation temperature (°C)',
      'Aging time (h)',
      'Drying temperature (°C)',
      'Drying duration (h)',
      'Calcination temperature (°C)',
      'Calcination duration (h)',
      'pH',
      'Precursor-to-extract ratio',
    ],
    note: 'Sol-gel projects record sol preparation, aging, drying, and calcination conditions that govern gelation and crystal formation.',
  },
]

const VariableGroupCard: React.FC<{ group: VariableGroup }> = ({ group: g }) => {
  const [expanded, setExpanded] = useState(false)
  const visible = expanded ? g.variables : g.variables.slice(0, 6)

  return (
    <div
      className="lp-vars-card"
      style={{ borderColor: g.border, background: g.bg }}
    >
      {/* Card header */}
      <div className="lp-vars-card-header">
        <div className="lp-vars-method-icon" style={{ color: g.color }}>
          {g.icon}
        </div>
        <div>
          <div className="lp-vars-method-name" style={{ color: g.color }}>{g.method}</div>
          <div className="lp-vars-projects">
            {g.projects.map((pid) => (
              <span key={pid} className="lp-vars-pid">{pid}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Variables list */}
      <ul className="lp-vars-list" aria-label={`${g.method} synthesis variables`}>
        {visible.map((v) => (
          <li key={v} className="lp-vars-item">
            <span className="lp-vars-dot" style={{ background: g.color }} />
            {v}
          </li>
        ))}
      </ul>

      {g.variables.length > 6 && (
        <button
          className="lp-vars-toggle"
          style={{ color: g.color }}
          onClick={() => setExpanded((e) => !e)}
          aria-expanded={expanded}
        >
          {expanded ? (
            <><ChevronUp size={14} /> Show fewer</>
          ) : (
            <><ChevronDown size={14} /> {g.variables.length - 6} more variables</>
          )}
        </button>
      )}

      {/* Method note */}
      <p className="lp-vars-note">{g.note}</p>
    </div>
  )
}

const ResearchVariablesSection: React.FC = () => (
  <section
    id="research-variables"
    className="lp-section lp-section-alt"
    aria-labelledby="vars-heading"
  >
    <div className="lp-container">
      <div className="lp-section-header">
        <span className="lp-section-label lp-section-label-blue">Synthesis Variables</span>
        <h2 id="vars-heading" className="lp-section-heading">
          Track the Variables That Shape Material Properties
        </h2>
        <p className="lp-section-subheading">
          Each research project can record its own set of synthesis parameters. Variables are
          method-specific and should be recorded according to the selected research project and
          synthesis technique.
        </p>
      </div>

      {/* Disclaimer */}
      <div className="lp-vars-disclaimer" role="note">
        <strong>Note:</strong> Parameters are method-specific and should be recorded according
        to the selected research project and synthesis technique. Not every parameter applies
        to every project.
      </div>

      {/* Variable group cards */}
      <div className="lp-vars-grid">
        {VARIABLE_GROUPS.map((g) => (
          <VariableGroupCard key={g.id} group={g} />
        ))}
      </div>
    </div>
  </section>
)

export default ResearchVariablesSection
