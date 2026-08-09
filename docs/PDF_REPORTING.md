# GreenSynth Analytics — Scientific PDF Report Generation Architecture

## Architecture Overview

The **Scientific PDF Report Generation Module** is a consumer-only reporting subsystem built using **Python ReportLab**. It renders formal, reproducible, and traceable scientific PDF reports directly from stored database analysis results without independently recalculating scientific quantities.

```
DATABASE (SQLAlchemy ORM) ──► ExperimentReportDataBuilder ──► ExperimentReportData DTO ──► PDFReportRenderer (ReportLab Platypus) ──► PDF Stream Output
```

---

## Technical Specifications

- **PDF Engine**: Python ReportLab (`reportlab.platypus`, `reportlab.lib`, `reportlab.pdfgen`)
- **Plot Engine**: Matplotlib in-memory PNG rendering (`ReportChartGenerator`)
- **API Endpoint**: `GET /api/v1/reports/experiments/{experiment_id}/pdf`
- **JSON Metadata Endpoint**: `GET /api/v1/reports/experiments/{experiment_id}/summary`
- **Output Filename Pattern**: `Experiment_Report_{experiment_code}.pdf`

---

## Mandatory Scientific Data Classifications

Every key numerical value displayed in the report is explicitly labeled with a visually distinct classification badge:

| Badge Tag | Description | Example Values |
|---|---|---|
| `[MEASURED DATA]` | Direct uncalibrated laboratory measurement values | Raw XRD 2θ/intensity arrays, Voltage/Current values, Raw absorbance |
| `[CALCULATED DATA]` | Derived physical properties computed by scientific algorithms | Scherrer crystallite size $D$ (nm), Tauc band gap $E_g$ (eV), Conductivity $\sigma$ (S/cm) |
| `[STATISTICAL DATA]` | Statistical summary metrics and regression fits | Pearson $r$, Spearman $\rho$, OLS $R^2$, ANOVA $F$-statistic |
| `[PREDICTED DATA]` | Machine learning model predictions with 95% confidence bounds | ML predicted conductivity with bounds `[lower, upper]` |
| `[RECOMMENDED DATA]` | Promising experimental candidate conditions | Candidate score, rank, target optimization parameters |
| `[VALIDATED DATA]` | Prospection validation error measurements | Signed error, absolute error, relative error (%), interval coverage |

---

## 14-Section PDF Structure

1. **Cover Page & Disclaimers**: Title, Experiment ID, Report ID, Researcher, System Version (`1.0.0-research`), and Scientific Mandatory Disclosure Box.
2. **Project Configuration & Synthesis Identity**: Project Code, Name, Material System (`CuO`), Plant Extract (`Mulberry`), Solvent (`Ethanol`), Synthesis Method (`Spray Pyrolysis`).
3. **Experiment Information**: Experiment ID, Title, Status (`PLANNED`, `COMPLETED`), Objective, Notes.
4. **Recorded Synthesis Parameters Table**: Parameter Code, Name, Recorded Value, Preserved Unit, Source, Validation Status.
5. **Samples Information**: Associated Sample Codes, Material, Substrate Type, Status.
6. **Characterization Summary Table**: Sample Code, Technique, Raw File Name, Analysis Status, Key Calculated Properties.
7. **XRD Characterization Section**: Raw File, Analysis Version, Processing Parameters, Peak Table ($2\theta$, Intensity, FWHM, Crystallite Size $D$), Peak Identification Disclaimer, and Matplotlib XRD Spectrum Chart.
8. **UV-Vis Spectroscopy Section**: Raw File, Transition Model, Tauc Extrapolation Fit, Optical Band Gap $E_g$ `[CALCULATED DATA]`, and Tauc Plot Chart.
9. **Electrical I-V Section**: Raw I-V File, Measurement Conditions, Sample Geometry (Thickness, Width, Length), Resistance, Resistivity, Electrical Conductivity $\sigma$ `[CALCULATED DATA]`, and $I\text{--}V$ Linear Regression Chart.
10. **FTIR / SEM Section**: Wavenumber Peak Table, Software-Assisted Peak Annotations, SEM Scale Calibration.
11. **Statistical Analysis Section**: Correlation $r$, OLS Regression $R^2$, ANOVA $F$-test, non-causal statistical disclosure.
12. **Machine Learning & Predictions Section**: Model Version, CV Metrics ($R^2$, RMSE), Input Parameters, Predicted Property, 95% Confidence Interval `[PREDICTED DATA]`, Domain Status (`IN_DOMAIN`).
13. **Optimization & Recommendations Section**: Objective, Direction (`MAXIMIZE`), Candidate Rank, Candidate Score `[RECOMMENDED DATA]`, Exploitation/Exploration classification.
14. **Data Provenance & Cryptographic Traceability Section**: Table listing every Raw File ID, Original Filename, SHA-256 Checksum, Analysis Run ID, Analysis Version, and Calculation Timestamp.

---

## Missing Data Handling

If optional characterization data (e.g. UV-Vis or ML prediction) is absent for an experiment, the section displays `"Data not available for this experiment"` without failing or fabricating placeholders.

---

## Testing & Verification

Run backend unit tests:
```powershell
$env:PYTHONPATH="backend"; python -m pytest backend/tests/unit/test_pdf_reporting.py -v
```

Execute database test PDF generation:
```powershell
python scripts/test_pdf.py
```
