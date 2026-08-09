# Model Performance Monitoring & Health Snapshots

## 1. Aggregated Validation Metrics
`ModelMonitoringService` calculates:
- **MAE**: $\text{Mean Absolute Error} = \frac{1}{N}\sum |y_i - \hat{y}_i|$
- **RMSE**: $\text{Root Mean Squared Error} = \sqrt{\frac{1}{N}\sum (y_i - \hat{y}_i)^2}$
- **Signed Bias**: $\text{Mean Signed Error} = \frac{1}{N}\sum (y_i - \hat{y}_i)$ (Positive = Underprediction, Negative = Overprediction).
- **Uncertainty Interval Coverage**: Fraction of actuals falling within the 95% uncertainty interval.

## 2. Health Statuses
- `INSUFFICIENT_DATA`: Validation count $N < 3$.
- `STABLE`: MAE $\le 1.15 \times$ baseline training MAE.
- `WARNING`: MAE $> 1.15 \times$ baseline training MAE.
- `DEGRADED`: MAE $> 1.40 \times$ baseline training MAE.
- `CRITICAL`: MAE $> 2.00 \times$ baseline training MAE.
