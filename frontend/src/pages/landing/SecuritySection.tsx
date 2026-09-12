/**
 * GreenSynth Analytics — Security / Research Integrity Section
 * Dark section with 5 research integrity capability cards.
 */

import React from 'react'
import { Lock, Users, FileCheck, GitBranch, ShieldCheck } from 'lucide-react'

const CARDS = [
  {
    icon: <Lock size={18} />,
    title: 'Secure Authentication',
    desc: 'Unified authenticated access for authorized researchers through a single, controlled login entry point.',
  },
  {
    icon: <Users size={18} />,
    title: 'Project-Level Access',
    desc: 'Research data is scoped to the appropriate project and research group with role-based authorization.',
  },
  {
    icon: <FileCheck size={18} />,
    title: 'Raw File Integrity',
    desc: 'Uploaded raw characterization files can be tracked with SHA-256 integrity checksums for provenance verification.',
  },
  {
    icon: <GitBranch size={18} />,
    title: 'Traceable Research Data',
    desc: 'Connect experiments, samples, files, calculations, analyses, and results in a single auditable research record.',
  },
  {
    icon: <ShieldCheck size={18} />,
    title: 'Controlled Access',
    desc: 'Research data access is enforced through backend authorization — only authorized researchers can access project data.',
  },
]

const SecuritySection: React.FC = () => (
  <section className="lp-section lp-section-dark" aria-labelledby="security-heading">
    <div className="lp-container">
      <div className="lp-section-header">
        <span className="lp-section-label">Research Integrity</span>
        <h2 id="security-heading" className="lp-section-heading lp-section-heading-light">
          Built for Controlled Research Data
        </h2>
        <p className="lp-section-subheading lp-section-subheading-light">
          Research data control, access authorization, file integrity, and full traceability
          designed for academic and laboratory research environments.
        </p>
      </div>

      <div className="lp-security-grid">
        {CARDS.map((card) => (
          <article key={card.title} className="lp-security-card">
            <div className="lp-security-icon" aria-hidden="true">
              {card.icon}
            </div>
            <h3 className="lp-security-title">{card.title}</h3>
            <p className="lp-security-desc">{card.desc}</p>
          </article>
        ))}
      </div>
    </div>
  </section>
)

export default SecuritySection
