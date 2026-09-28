# Model Retraining & Review Policy

## 1. No Automatic Model Retraining
The system NEVER automatically retrains or promotes models.

## 2. Review Triggers
When model health transitions to `WARNING`, `DEGRADED`, or `CRITICAL`, the system alerts:
> "Model review recommended due to observed performance deterioration relative to training baseline."

## 3. Researcher Options
The researcher explicitly chooses to:
1. Retain the model with active monitoring.
2. Build a new versioned MLDataset incorporating new validated experiments.
3. Train a new candidate model version ($V_{N+1}$).
4. Retire the model (`RETIRED` status).
