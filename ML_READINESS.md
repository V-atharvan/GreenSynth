# ML Readiness Gate (MLReadinessValidator)

## 1. Quality Criteria
Before entering the ML pipeline, a dataset is evaluated against:
1. Dataset existence & version locking.
2. Experiment & sample traceability.
3. Target property & unit validity.
4. Feature specified & units valid.
5. Missing observation rate ($\le 35\%$).
6. Minimum sample size ($N \ge 5$).

## 2. Readiness Statuses
- `READY`: All criteria satisfied.
- `READY_WITH_WARNING`: Minor issues (e.g. small $N < 15$ or minor missing values).
- `NOT_READY`: Critical criteria failed (e.g. missing target, $N < 3$, unlocked dataset).
