/**
 * GreenSynth Analytics — Statistical Analysis Section
 * Describes the statistical evidence capabilities with a conceptual visualization.
 */

import React from 'react'
import { BarChart3, GitMerge, TrendingUp, PieChart, ArrowRight } from 'lucide-react'

const FEATURES = [
  {
    icon: <BarChart3 size={16} />,
    title: 'Descriptive Statistics',
    desc: 'Mean, standard deviation, range, and distribution summaries across synthesis parameters and material properties.',
  },
  {
    icon: <GitMerge size={16} />,
    title: 'Correlation Analysis',
    desc: 'Identify statistically significant relationships between synthesis variables and experimental outcomes.',
  },
  {
    icon: <TrendingUp size={16} />,
    title: 'Regression Analysis',
    desc: 'Quantify the directional effect of synthesis parameters on measured material properties.',
  },
  {
    icon: <PieChart size={16} />,
    title: 'Sample Comparison',
    desc: 'Compare characterization profiles across multiple synthesis samples in a structured analytical view.',
  },
]

const ConceptualScatterPlot: React.FC = () => (
  <div className="lp-stats-visual">
    <div className="lp-stats-visual-title">
      Conceptual Parameter–Property Visualization
      <span className="lp-stats-badge">Illustrative Data</span>
    </div>

    <div className="lp-scatter-wrap">
      <svg
        className="lp-scatter-svg"
        viewBox="0 0 320 180"
        aria-label="Conceptual scatter plot showing relationship between substrate temperature and electrical conductivity"
      >
        {/* Grid lines */}
        {[40, 80, 120, 160].map((y) => (
          <line key={y} x1="35" y1={y} x2="305" y2={y}
            stroke="var(--color-border-light)" strokeWidth="1" strokeDasharray="3,3" />
        ))}
        {[75, 120, 165, 210, 255, 300].map((x) => (
          <line key={x} x1={x} y1="10" x2={x} y2="165"
            stroke="var(--color-border-light)" strokeWidth="1" strokeDasharray="3,3" />
        ))}

        {/* Axes */}
        <line x1="35" y1="165" x2="305" y2="165" stroke="var(--color-border)" strokeWidth="1.5" />
        <line x1="35" y1="10"  x2="35"  y2="165" stroke="var(--color-border)" strokeWidth="1.5" />

        {/* Regression line */}
        <line x1="45" y1="158" x2="295" y2="22"
          stroke="var(--color-accent)" strokeWidth="2" strokeDasharray="6,3" opacity="0.7" />

        {/* Data points */}
        {[
          [55,152],[80,140],[105,128],[130,118],[155,108],
          [175,95],[200,82],[220,72],[245,58],[270,46],[290,32],
        ].map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r="5" fill="var(--color-primary)" opacity="0.75" />
        ))}

        {/* Axis labels */}
        <text x="170" y="178" textAnchor="middle" fill="var(--color-text-secondary)" fontSize="10">
          Substrate Temperature (°C)
        </text>
        <text x="14" y="90" textAnchor="middle" fill="var(--color-text-secondary)" fontSize="10"
          transform="rotate(-90,14,90)">Conductivity</text>

        {/* R label */}
        <text x="268" y="36" fill="var(--color-accent)" fontSize="10" fontWeight="700">r = 0.92</text>
      </svg>
    </div>

    {/* Relationships */}
    <div className="lp-relationship-items">
      {[
        { param: 'Substrate Temperature', target: 'Electrical Conductivity' },
        { param: 'Substrate Temperature', target: 'Crystallite Size' },
        { param: 'Extract Concentration', target: 'Band Gap Energy' },
      ].map(({ param, target }) => (
        <div key={`${param}-${target}`} className="lp-relationship-item">
          <span className="lp-rel-param">{param}</span>
          <ArrowRight size={12} className="lp-rel-arrow" aria-hidden="true" />
          <span className="lp-rel-target">{target}</span>
        </div>
      ))}
    </div>

    <p className="lp-conceptual-note">
      Illustrative data — not actual experimental findings
    </p>
  </div>
)

const StatisticsSection: React.FC = () => (
  <section className="lp-section" aria-labelledby="stats-heading">
    <div className="lp-container">
      <div className="lp-stats-grid">
        {/* Left: features */}
        <div>
          <span className="lp-section-label lp-section-label-blue">Statistical Analysis</span>
          <h2 id="stats-heading" className="lp-section-heading">
            Understand Relationships in Experimental Data
          </h2>
          <p className="lp-section-subheading" style={{ marginBottom: '28px' }}>
            Statistical analysis helps identify meaningful relationships between synthesis parameters
            and material properties before predictive modeling and optimization — building
            evidence-based understanding of the research system.
          </p>

          <div className="lp-stats-feature-list">
            {FEATURES.map((f) => (
              <div key={f.title} className="lp-stats-feature">
                <div className="lp-stats-feature-icon" aria-hidden="true">
                  {f.icon}
                </div>
                <div>
                  <div className="lp-stats-feature-title">{f.title}</div>
                  <div className="lp-stats-feature-desc">{f.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: conceptual visualization */}
        <ConceptualScatterPlot />
      </div>
    </div>
  </section>
)

export default StatisticsSection
