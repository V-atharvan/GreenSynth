# Prediction Validation & Experimental Linkage

## 1. PredictionValidation Entity
Links an `MLPrediction` to an actual laboratory measurement:
- `error = actual - predicted`
- `absolute_error = abs(actual - predicted)`
- `relative_error = abs(actual - predicted) / abs(actual)`

## 2. Model Validation Dashboard
Provides:
- Predicted vs Actual 1:1 scatter plot with identity reference line.
- Cumulative validation metrics (MAE, RMSE, $R^2$).
- Prediction error distribution.
- Model performance drift warnings over time.
