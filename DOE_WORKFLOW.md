# DOE Workflow & Approval Lifecycle

## 1. Step-by-Step Workflow
1. **Define Study & Research Question**: Formulate research hypothesis and objectives.
2. **Configure Controllable Factors**: Define continuous bounds, discrete/categorical levels, roles, and units.
3. **Select DOE Method & Parameters**: Choose design method (Full Factorial, Fractional, CCD, Box-Behnken, Random), replicates, center points, and random seed.
4. **Preview Workload & Generate Matrix**: Calculate expected run count; display workload warning if runs > 32.
5. **Researcher Review & Approval**: Inspect proposed runs and lock version V1.
6. **Laboratory Conversion**: Convert approved proposed runs into `PLANNED` laboratory experiments (`Experiment`).
7. **Execution & Measured Response Linking**: Link actual synthesis parameters and characterization measurements back to DOE runs.
8. **Statistical Analysis**: Compute Main Effects, Interaction Effects, and Response Surface regression fit.
