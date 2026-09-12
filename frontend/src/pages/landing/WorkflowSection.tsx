/**
 * GreenSynth Analytics — Complete Research Workflow Section
 * 14-step research cycle displayed as a connected process.
 * Desktop: two-row horizontal grid. Mobile: vertical timeline.
 */

import React from 'react'
import {
  Folder, FlaskConical, Layers, Sliders, Activity, Calculator,
  BarChart3, Cpu, Grid3X3, Target, Lightbulb, ShieldCheck, FileText, ChevronRight, ChevronDown,
} from 'lucide-react'

interface WorkflowStep {
  num: number
  icon: React.ReactNode
  title: string
  desc: string
}

const STEPS: WorkflowStep[] = [
  { num: 1,  icon: <Folder size={16} />,       title: 'Project',                desc: 'Define and organise the research project.' },
  { num: 2,  icon: <FlaskConical size={16} />,  title: 'Experiment',             desc: 'Design and record synthesis experiments.' },
  { num: 3,  icon: <Layers size={16} />,        title: 'Sample',                 desc: 'Register prepared synthesis samples.' },
  { num: 4,  icon: <Sliders size={16} />,       title: 'Synthesis Parameters',   desc: 'Document process variables and conditions.' },
  { num: 5,  icon: <Activity size={16} />,      title: 'Characterization',       desc: 'Capture XRD, UV-Vis, FTIR, SEM, Electrical.' },
  { num: 6,  icon: <Calculator size={16} />,    title: 'Scientific Calculations',desc: 'Derive material properties from raw data.' },
  { num: 7,  icon: <BarChart3 size={16} />,     title: 'Statistical Analysis',   desc: 'Identify patterns and relationships.' },
  { num: 8,  icon: <Cpu size={16} />,           title: 'Machine Learning',       desc: 'Train predictive models on experimental data.' },
  { num: 9,  icon: <Grid3X3 size={16} />,       title: 'DOE',                    desc: 'Design of Experiments for parameter space.' },
  { num: 10, icon: <Target size={16} />,        title: 'Experimental Optimization', desc: 'Identify candidate synthesis conditions.' },
  { num: 11, icon: <Lightbulb size={16} />,     title: 'Recommendation',         desc: 'Generate experimentally testable suggestions.' },
  { num: 12, icon: <ShieldCheck size={16} />,   title: 'Validation',             desc: 'Experimentally confirm predicted outcomes.' },
  { num: 13, icon: <ShieldCheck size={16} />,   title: 'Drift Detection',        desc: 'Monitor model performance over time.' },
  { num: 14, icon: <FileText size={16} />,      title: 'Research Report',        desc: 'Compile traceable, evidence-based findings.' },
]

const WorkflowSection: React.FC = () => {
  const ROW1 = STEPS.slice(0, 7)
  const ROW2 = STEPS.slice(7, 14)

  return (
    <section id="workflow" className="lp-section" aria-labelledby="workflow-heading">
      <div className="lp-container">
        <div className="lp-section-header">
          <span className="lp-section-label">Complete Research Cycle</span>
          <h2 id="workflow-heading" className="lp-section-heading">
            One Platform for the Complete Research Cycle
          </h2>
          <p className="lp-section-subheading">
            Connect experimental planning, laboratory data, characterization, analysis, prediction,
            optimization, and validation in one traceable research environment.
          </p>
        </div>

        {/* ── Desktop: Two-Row Horizontal Grid ── */}
        <div className="lp-workflow-desktop" aria-label="Research workflow steps">
          {/* Row 1: steps 1–7 */}
          <div className="lp-workflow-row" style={{ display: 'flex', alignItems: 'stretch', marginBottom: '8px' }}>
            {ROW1.map((step, i) => (
              <React.Fragment key={step.num}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="lp-workflow-step-inner" role="listitem" aria-label={`Step ${step.num}: ${step.title}`}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span className="lp-workflow-step-num" aria-hidden="true">{step.num}</span>
                      <span className="lp-workflow-step-icon" aria-hidden="true">{step.icon}</span>
                    </div>
                    <div className="lp-workflow-step-title">{step.title}</div>
                    <div className="lp-workflow-step-desc">{step.desc}</div>
                  </div>
                </div>
                {i < ROW1.length - 1 && (
                  <div className="lp-workflow-arrow" aria-hidden="true">
                    <ChevronRight size={14} />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Connector: row 1 → row 2 (right-to-left) */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '0 4px', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-text-muted)' }}>
              <ChevronDown size={14} />
            </div>
          </div>

          {/* Row 2: steps 8–14 (right-to-left display) */}
          <div className="lp-workflow-row" style={{ display: 'flex', alignItems: 'stretch', flexDirection: 'row-reverse' }}>
            {ROW2.map((step, i) => (
              <React.Fragment key={step.num}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="lp-workflow-step-inner" role="listitem" aria-label={`Step ${step.num}: ${step.title}`}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span className="lp-workflow-step-num" aria-hidden="true">{step.num}</span>
                      <span className="lp-workflow-step-icon" aria-hidden="true">{step.icon}</span>
                    </div>
                    <div className="lp-workflow-step-title">{step.title}</div>
                    <div className="lp-workflow-step-desc">{step.desc}</div>
                  </div>
                </div>
                {i < ROW2.length - 1 && (
                  <div className="lp-workflow-arrow" aria-hidden="true">
                    <ChevronRight size={14} style={{ transform: 'rotate(180deg)' }} />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* ── Mobile: Vertical Timeline ── */}
        <div
          className="lp-workflow-mobile"
          style={{ display: 'none' }}
          aria-label="Research workflow steps"
        >
          {STEPS.map((step, i) => (
            <div
              key={step.num}
              style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', position: 'relative' }}
            >
              {/* Connector column */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '50%',
                    background: 'var(--color-primary)',
                    color: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    flexShrink: 0,
                    zIndex: 1,
                  }}
                  aria-hidden="true"
                >
                  {step.num}
                </div>
                {i < STEPS.length - 1 && (
                  <div style={{ width: '2px', flex: 1, minHeight: '24px', background: 'var(--color-border)', margin: '4px 0' }} aria-hidden="true" />
                )}
              </div>

              {/* Content */}
              <div style={{ paddingBottom: i < STEPS.length - 1 ? '16px' : 0, flex: 1 }}>
                <div style={{
                  background: '#ffffff',
                  border: '1px solid var(--color-border)',
                  borderRadius: '10px',
                  padding: '14px 16px',
                  boxShadow: 'var(--shadow-sm)',
                }} role="listitem" aria-label={`Step ${step.num}: ${step.title}`}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--color-accent)' }} aria-hidden="true">{step.icon}</span>
                    <span style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--color-text)' }}>
                      {step.title}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', lineHeight: 1.5, margin: 0 }}>
                    {step.desc}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .lp-workflow-desktop { display: none !important; }
          .lp-workflow-mobile  { display: flex !important; flex-direction: column; }
        }
      `}</style>
    </section>
  )
}

export default WorkflowSection
