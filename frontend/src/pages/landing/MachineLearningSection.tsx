/**
 * GreenSynth Analytics — Machine Learning Section
 * ML pipeline steps with conceptual visualization of inputs → model → output.
 */

import React from 'react'
import { Database, Cpu, TrendingUp, ShieldCheck, AlertCircle } from 'lucide-react'

const ML_STEPS = [
  {
    num: 1,
    icon: <Database size={16} />,
    dotClass: '',
    title: 'Dataset Builder',
    desc: 'Construct training datasets from experimental parameters, characterization results, and material property measurements.',
  },
  {
    num: 2,
    icon: <Cpu size={16} />,
    dotClass: 'lp-ml-step-dot-accent',
    title: 'Model Training',
    desc: 'Train regression or classification models with cross-validation, feature importance evaluation, and performance metrics.',
  },
  {
    num: 3,
    icon: <TrendingUp size={16} />,
    dotClass: 'lp-ml-step-dot-accent',
    title: 'Predict & Uncertainty',
    desc: 'Generate predictions for new synthesis conditions with quantified uncertainty ranges for informed decision-making.',
  },
  {
    num: 4,
    icon: <ShieldCheck size={16} />,
    dotClass: 'lp-ml-step-dot-success',
    title: 'Validation Studio',
    desc: 'Validate model predictions against experimental results and detect performance drift over time.',
  },
]

const MLVisualization: React.FC = () => (
  <div className="lp-ml-vis" role="img" aria-label="Machine learning pipeline visualization — illustrative">
    <div className="lp-ml-vis-title">Conceptual ML Pipeline</div>

    {/* Input parameter chips */}
    <div style={{ fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>
      Input Parameters
    </div>
    <div className="lp-ml-inputs">
      {['Substrate Temperature', 'Spray Rate', 'Extract Concentration', 'Precursor Concentration'].map((param) => (
        <div key={param} className="lp-ml-input-chip">
          <span className="lp-ml-input-dot" aria-hidden="true" />
          {param}
        </div>
      ))}
    </div>

    {/* Arrow down */}
    <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', marginBottom: '8px', fontSize: '1.25rem' }} aria-hidden="true">↓</div>

    {/* Model box */}
    <div className="lp-ml-model-box" aria-label="Predictive model">
      <div className="lp-ml-model-label">Predictive Model</div>
      <div className="lp-ml-model-sub">Trained on experimental dataset</div>
    </div>

    {/* Arrow down */}
    <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', marginBottom: '8px', fontSize: '1.25rem' }} aria-hidden="true">↓</div>

    {/* Output */}
    <div className="lp-ml-output" aria-label="Prediction output">
      <div className="lp-ml-output-label">Predicted Output</div>
      <div className="lp-ml-output-val">Electrical Conductivity</div>
      <div className="lp-ml-uncertainty">
        <AlertCircle size={12} aria-hidden="true" />
        <span>Uncertainty estimate included</span>
      </div>
    </div>

    <p className="lp-conceptual-note">Conceptual visualization — illustrative inputs and target</p>
  </div>
)

const MachineLearningSection: React.FC = () => (
  <section className="lp-section lp-section-alt" aria-labelledby="ml-heading">
    <div className="lp-container">
      <div className="lp-ml-layout">
        {/* Left: Pipeline steps */}
        <div>
          <span className="lp-section-label lp-section-label-blue">Machine Learning</span>
          <h2 id="ml-heading" className="lp-section-heading">
            Machine Learning for Experimental Research
          </h2>
          <p className="lp-section-subheading" style={{ marginBottom: '32px' }}>
            Build evidence-based datasets from experimental parameters, train predictive models,
            quantify uncertainty, and evaluate model performance against actual experimental results.
          </p>

          <div className="lp-ml-pipeline" role="list" aria-label="ML pipeline steps">
            {ML_STEPS.map((step, i) => (
              <div key={step.num} className="lp-ml-step" role="listitem">
                <div className="lp-ml-step-connector">
                  <div className={`lp-ml-step-dot ${step.dotClass}`} aria-hidden="true">
                    {step.icon}
                  </div>
                  {i < ML_STEPS.length - 1 && (
                    <div className="lp-ml-step-line" aria-hidden="true" />
                  )}
                </div>
                <div className="lp-ml-step-content">
                  <div className="lp-ml-step-title">{step.title}</div>
                  <div className="lp-ml-step-desc">{step.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Visualization */}
        <MLVisualization />
      </div>
    </div>
  </section>
)

export default MachineLearningSection
