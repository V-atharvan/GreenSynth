# Evidence Architecture & Scoring Logic

## 1. Evidence Record Entity
An `EvidenceRecord` represents a formal evidence-backed scientific observation:
- `evidence_id`
- `dataset_version_id`
- `statement` (Cautious scientific language)
- `evidence_type` (`OBSERVATION`, `ASSOCIATION`, `STATISTICAL_EFFECT`, `MODEL_ESTIMATE`, `VALIDATED_RESULT`)
- `sample_size` ($N$)
- `statistical_method`
- `effect_estimate`
- `confidence_interval` (95% CI)
- `prediction_interval` (95% PI)
- `evidence_score` (0.0 to 100.0)
- `scoring_criteria`
- `status` (`DRAFT`, `APPROVED`, `REJECTED`, `ARCHIVED`)

## 2. Transparent Scoring Logic
- **Sample Size $N$** (up to 30 pts): 3 pts per observation up to $N=10$.
- **Replicate Tracking** (up to 20 pts): 20 pts if intentional replicates exist.
- **Data Completeness** (up to 20 pts): $20 \times (1 - \text{missing\_rate})$.
- **Model Diagnostics** (up to 30 pts): $R^2$ fit metric and absence of heteroscedasticity penalties.
