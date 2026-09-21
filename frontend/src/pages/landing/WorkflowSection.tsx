/**
 * GreenSynth Analytics — Complete Research Workflow Section
 * 14-step research cycle displayed as a connected process.
 * Desktop: two-row horizontal grid. Mobile: vertical timeline.
 */

import React from 'react'
import {
  Folder, FlaskConical, Layers, Sliders, Activity, Calculator,
  BarChart3, Cpu, Grid3X3, Target, Lightbulb, ShieldCheck, FileText,
  ChevronRight, ChevronDown,
} from 'lucide-react'

interface WorkflowStep {
  num: number
  icon: React.ReactNode
  title: string
  desc: string
  phase: 'planning' | 'lab' | 'analysis' | 'ai' | 'validation'
}

const PHASE_META = {
  planning:   { label: 'Planning',   color: '#3b9ede', bg: 'rgba(59,158,222,0.15)',  border: 'rgba(59,158,222,0.35)',  numBg: '#1e6fa0' },
  lab:        { label: 'Lab',        color: '#34d399', bg: 'rgba(52,211,153,0.12)',  border: 'rgba(52,211,153,0.32)',  numBg: '#0f7a52' },
  analysis:   { label: 'Analysis',   color: '#a78bfa', bg: 'rgba(167,139,250,0.13)', border: 'rgba(167,139,250,0.32)', numBg: '#6d3fc7' },
  ai:         { label: 'AI & Opt.',  color: '#fb923c', bg: 'rgba(251,146,60,0.13)',  border: 'rgba(251,146,60,0.32)',  numBg: '#c05621' },
  validation: { label: 'Validation', color: '#f472b6', bg: 'rgba(244,114,182,0.13)', border: 'rgba(244,114,182,0.32)', numBg: '#9b2563' },
} as const

const STEPS: WorkflowStep[] = [
  { num: 1,  icon: <Folder size={15} />,       title: 'Project',                  desc: 'Define and organise the research project.',                    phase: 'planning' },
  { num: 2,  icon: <FlaskConical size={15} />,  title: 'Experiment',               desc: 'Design and record synthesis experiments.',                      phase: 'planning' },
  { num: 3,  icon: <Layers size={15} />,        title: 'Sample',                   desc: 'Register prepared synthesis samples.',                          phase: 'lab' },
  { num: 4,  icon: <Sliders size={15} />,       title: 'Synthesis Parameters',     desc: 'Document process variables and conditions.',                    phase: 'lab' },
  { num: 5,  icon: <Activity size={15} />,      title: 'Characterization',         desc: 'Capture XRD, UV-Vis, FTIR, SEM & Electrical data.',            phase: 'lab' },
  { num: 6,  icon: <Calculator size={15} />,    title: 'Scientific Calculations',  desc: 'Derive material properties from raw instrument data.',          phase: 'analysis' },
  { num: 7,  icon: <BarChart3 size={15} />,     title: 'Statistical Analysis',     desc: 'Identify patterns, regressions and DOE relationships.',         phase: 'analysis' },
  { num: 8,  icon: <Cpu size={15} />,           title: 'Machine Learning',         desc: 'Train predictive models on experimental data.',                 phase: 'ai' },
  { num: 9,  icon: <Grid3X3 size={15} />,       title: 'DOE',                      desc: 'Design of Experiments for efficient parameter space search.',   phase: 'ai' },
  { num: 10, icon: <Target size={15} />,        title: 'Experimental Optimization',desc: 'Identify optimal candidate synthesis conditions.',              phase: 'ai' },
  { num: 11, icon: <Lightbulb size={15} />,     title: 'Recommendation',           desc: 'Generate experimentally testable synthesis suggestions.',       phase: 'ai' },
  { num: 12, icon: <ShieldCheck size={15} />,   title: 'Validation',               desc: 'Experimentally confirm model-predicted outcomes.',              phase: 'validation' },
  { num: 13, icon: <ShieldCheck size={15} />,   title: 'Drift Detection',          desc: 'Monitor model performance against new data over time.',         phase: 'validation' },
  { num: 14, icon: <FileText size={15} />,      title: 'Research Report',          desc: 'Compile traceable, evidence-based research findings.',          phase: 'validation' },
]

interface StepCardProps {
  step: WorkflowStep
}

const StepCard: React.FC<StepCardProps> = ({ step }) => {
  const p = PHASE_META[step.phase]
  return (
    <div
      className="lp-wf-card"
      role="listitem"
      aria-label={`Step ${step.num}: ${step.title}`}
      style={{
        background: p.bg,
        borderColor: p.border,
      }}
    >
      <div className="lp-wf-card-top">
        <span
          className="lp-wf-num"
          style={{ background: p.numBg }}
          aria-hidden="true"
        >
          {step.num}
        </span>
        <span className="lp-wf-icon" style={{ color: p.color }} aria-hidden="true">
          {step.icon}
        </span>
      </div>
      <div className="lp-wf-title" style={{ color: '#ffffff' }}>{step.title}</div>
      <div className="lp-wf-desc">{step.desc}</div>
    </div>
  )
}

const WorkflowSection: React.FC = () => {
  const ROW1 = STEPS.slice(0, 7)
  const ROW2 = STEPS.slice(7, 14)

  return (
    <section id="workflow" className="lp-workflow-section" aria-labelledby="workflow-heading">
      <div className="lp-container">
        {/* Header */}
        <div className="lp-section-header" style={{ marginBottom: '44px' }}>
          <span className="lp-section-label">Complete Research Cycle</span>
          <h2 id="workflow-heading" className="lp-section-heading lp-section-heading-light">
            One Platform for the Complete Research Cycle
          </h2>
          <p className="lp-section-subheading lp-section-subheading-light">
            Connect experimental planning, laboratory data, characterization, analysis, prediction,
            optimization, and validation in one traceable research environment.
          </p>
        </div>

        {/* Phase Legend */}
        <div className="lp-wf-legend" aria-label="Workflow phase legend">
          {(Object.entries(PHASE_META) as [string, typeof PHASE_META[keyof typeof PHASE_META]][]).map(([key, p]) => (
            <div key={key} className="lp-wf-legend-item">
              <span className="lp-wf-legend-dot" style={{ background: p.color }} />
              <span className="lp-wf-legend-label">{p.label}</span>
            </div>
          ))}
        </div>

        {/* ── Desktop: Two-Row Grid ── */}
        <div className="lp-workflow-desktop" aria-label="Research workflow steps">
          {/* Row 1: steps 1–7 */}
          <div className="lp-wf-row">
            {ROW1.map((step, i) => (
              <React.Fragment key={step.num}>
                <div style={{ flex: 1, minWidth: 0, display: 'flex' }}>
                  <StepCard step={step} />
                </div>
                {i < ROW1.length - 1 && (
                  <div className="lp-wf-arrow" aria-hidden="true">
                    <ChevronRight size={14} />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Connector: row 1 → row 2 */}
          <div className="lp-wf-turn" aria-hidden="true">
            <ChevronDown size={16} style={{ color: 'rgba(200,216,232,0.4)' }} />
          </div>

          {/* Row 2: steps 8–14 (right-to-left) */}
          <div className="lp-wf-row" style={{ flexDirection: 'row-reverse' }}>
            {ROW2.map((step, i) => (
              <React.Fragment key={step.num}>
                <div style={{ flex: 1, minWidth: 0, display: 'flex' }}>
                  <StepCard step={step} />
                </div>
                {i < ROW2.length - 1 && (
                  <div className="lp-wf-arrow" aria-hidden="true">
                    <ChevronRight size={14} style={{ transform: 'rotate(180deg)' }} />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* ── Mobile: Vertical Timeline ── */}
        <div className="lp-workflow-mobile" aria-label="Research workflow steps">
          {STEPS.map((step, i) => {
            const p = PHASE_META[step.phase]
            return (
              <div key={step.num} className="lp-wf-mobile-item">
                {/* Timeline column */}
                <div className="lp-wf-mobile-col">
                  <div
                    className="lp-wf-mobile-num"
                    style={{ background: p.numBg, boxShadow: `0 0 0 3px ${p.border}` }}
                    aria-hidden="true"
                  >
                    {step.num}
                  </div>
                  {i < STEPS.length - 1 && (
                    <div className="lp-wf-mobile-line" aria-hidden="true" />
                  )}
                </div>
                {/* Content card */}
                <div className="lp-wf-mobile-content" style={{ paddingBottom: i < STEPS.length - 1 ? '16px' : 0 }}>
                  <div
                    className="lp-wf-mobile-card"
                    style={{ borderColor: p.border, background: p.bg }}
                    role="listitem"
                    aria-label={`Step ${step.num}: ${step.title}`}
                  >
                    <div className="lp-wf-mobile-card-top">
                      <span style={{ color: p.color }} aria-hidden="true">{step.icon}</span>
                      <span className="lp-wf-mobile-title">{step.title}</span>
                    </div>
                    <p className="lp-wf-mobile-desc">{step.desc}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

export default WorkflowSection
