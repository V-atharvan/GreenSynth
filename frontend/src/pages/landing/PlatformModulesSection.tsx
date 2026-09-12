/**
 * GreenSynth Analytics — Platform Modules Section
 * Grouped module cards for all research platform capabilities.
 */

import React from 'react'
import { Folder, Activity, BarChart3, Cpu, Layers, Waves, Zap, Microscope, GitBranch } from 'lucide-react'

interface ModuleItem {
  label: string
  desc: string
}

interface ModuleGroup {
  icon: React.ReactNode
  iconClass: string
  title: string
  items: ModuleItem[]
}

const GROUPS: ModuleGroup[] = [
  {
    icon: <Folder size={18} />,
    iconClass: '',
    title: 'Research Management',
    items: [
      { label: 'Projects',         desc: 'Organise research projects and access control.' },
      { label: 'Experiments',      desc: 'Design, log, and manage synthesis experiments.' },
      { label: 'Samples',          desc: 'Register and track prepared synthesis samples.' },
      { label: 'Research Groups',  desc: 'Manage team members and research group context.' },
    ],
  },
  {
    icon: <Waves size={18} />,
    iconClass: 'lp-module-icon-green',
    title: 'Characterization',
    items: [
      { label: 'XRD',                       desc: 'Crystal structure and phase analysis.' },
      { label: 'UV-Vis',                    desc: 'Optical absorption and band-gap analysis.' },
      { label: 'FTIR',                      desc: 'Functional-group and chemical-bond analysis.' },
      { label: 'SEM',                       desc: 'Surface morphology and particle size.' },
      { label: 'Electrical Characterization', desc: 'Conductivity and resistivity properties.' },
    ],
  },
  {
    icon: <BarChart3 size={18} />,
    iconClass: 'lp-module-icon-amber',
    title: 'Scientific Analysis',
    items: [
      { label: 'Scientific Calculations', desc: 'Derive material properties from raw characterization data.' },
      { label: 'Sample Comparison',       desc: 'Cross-sample property comparison and visualization.' },
      { label: 'Statistical Evidence',    desc: 'Correlation, regression, and descriptive statistics.' },
      { label: 'Data Visualization',      desc: 'Charts and plots for experimental data.' },
    ],
  },
  {
    icon: <Cpu size={18} />,
    iconClass: 'lp-module-icon-purple',
    title: 'AI & Optimization',
    items: [
      { label: 'Machine Learning',       desc: 'Train, evaluate, and predict using experimental datasets.' },
      { label: 'DOE',                    desc: 'Design of Experiments for parameter space exploration.' },
      { label: 'Experimental Optimization', desc: 'Identify promising synthesis conditions from models.' },
      { label: 'Recommendation Studio', desc: 'Generate and manage experimentally testable suggestions.' },
      { label: 'Validation & Drift',    desc: 'Validate predictions and monitor model reliability.' },
    ],
  },
]

const PlatformModulesSection: React.FC = () => (
  <section
    id="platform-modules"
    className="lp-section lp-section-alt"
    aria-labelledby="platform-heading"
  >
    <div className="lp-container">
      <div className="lp-section-header">
        <span className="lp-section-label lp-section-label-blue">Platform</span>
        <h2 id="platform-heading" className="lp-section-heading">
          Everything Needed for Data-Driven Research
        </h2>
      </div>

      <div className="lp-modules-grid">
        {GROUPS.map((group) => (
          <article key={group.title} className="lp-module-card">
            <div className="lp-module-card-header">
              <div className={`lp-module-icon ${group.iconClass}`} aria-hidden="true">
                {group.icon}
              </div>
              <h3 className="lp-module-card-title">{group.title}</h3>
            </div>

            <ul className="lp-module-items" aria-label={`${group.title} modules`}>
              {group.items.map((item) => (
                <li key={item.label} className="lp-module-item">
                  <span className="lp-module-dot" aria-hidden="true" />
                  <div>
                    <span style={{ fontWeight: 600, color: 'var(--color-text)' }}>{item.label}</span>
                    {' — '}
                    <span>{item.desc}</span>
                  </div>
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </div>
  </section>
)

export default PlatformModulesSection
