/**
 * GreenSynth Analytics — Characterization Section
 * Five characterization technique cards: XRD, UV-Vis, FTIR, SEM, Electrical.
 */

import React from 'react'
import { Activity, ScanLine, Waves, Microscope, Zap } from 'lucide-react'

interface CharCard {
  icon: React.ReactNode
  name: string
  fullName: string
  desc: string
}

const CHARS: CharCard[] = [
  {
    icon: <Activity size={22} />,
    name: 'XRD',
    fullName: 'X-Ray Diffraction',
    desc: 'Crystal structure, phase identification, peak analysis, and crystallite-size evaluation using Debye–Scherrer analysis.',
  },
  {
    icon: <ScanLine size={22} />,
    name: 'UV-Vis',
    fullName: 'UV-Visible Spectroscopy',
    desc: 'Optical absorption spectroscopy for band-gap determination using Tauc plot analysis of semiconductor materials.',
  },
  {
    icon: <Waves size={22} />,
    name: 'FTIR',
    fullName: 'Fourier-Transform Infrared',
    desc: 'Functional-group identification, chemical-bond analysis, and confirmation of material phase composition.',
  },
  {
    icon: <Microscope size={22} />,
    name: 'SEM',
    fullName: 'Scanning Electron Microscopy',
    desc: 'Surface morphology visualization, particle size and distribution analysis, and microstructure characterization.',
  },
  {
    icon: <Zap size={22} />,
    name: 'Electrical',
    fullName: 'Electrical Characterization',
    desc: 'Conductivity, resistivity, and related electrical transport property measurement and analysis.',
  },
]

const CharacterizationSection: React.FC = () => (
  <section className="lp-section lp-section-alt" aria-labelledby="char-heading">
    <div className="lp-container">
      <div className="lp-section-header">
        <span className="lp-section-label">Characterization</span>
        <h2 id="char-heading" className="lp-section-heading">
          Connect Material Characterization with Research Data
        </h2>
        <p className="lp-section-subheading">
          Characterization results become structured, traceable research data that can be compared
          across samples and used in downstream scientific analysis.
        </p>
      </div>

      <div className="lp-char-grid">
        {CHARS.map((c) => (
          <article key={c.name} className="lp-char-card">
            <div className="lp-char-icon-wrap" aria-hidden="true">
              {c.icon}
            </div>
            <h3 className="lp-char-name">{c.name}</h3>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginBottom: '8px', fontStyle: 'italic' }}>
              {c.fullName}
            </div>
            <p className="lp-char-desc">{c.desc}</p>
          </article>
        ))}
      </div>
    </div>
  </section>
)

export default CharacterizationSection
