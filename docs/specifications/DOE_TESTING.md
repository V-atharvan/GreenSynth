# DOE Testing Strategy

## 1. Automated Unit Tests (`backend/tests/unit/test_doe_generator.py`)
- Full factorial $2^k, 3^k$ run count verification.
- Fractional factorial half-fraction design resolution.
- Central Composite Design axial & center points.
- Seed-reproducible run order randomization.
- Constraint & unit validation block enforcement.
- Main Effects and response surface fit verification.

## 2. Integration Tests (`backend/tests/integration/test_doe_pipeline.py`)
- Project 7 CuO Mulberry Spray Pyrolysis end-to-end integration test: Study Creation $\rightarrow$ Factor & Response Definitions $\rightarrow$ Full Factorial Generation $\rightarrow$ Randomization & Replication $\rightarrow$ Approval $\rightarrow$ Conversion to PLANNED Experiment $\rightarrow$ Analysis.
