# Machine Learning Prediction & Out-of-Domain Detection

## 1. Prediction Generation Workflow
`PredictionService` accepts candidate synthesis conditions (e.g. Substrate Temperature = 375 °C, Spray Rate = 3.5 mL/min), evaluates feature ranges, loads the registered pipeline, computes prediction, and estimates uncertainty bounds.

## 2. Feature Range & Extrapolation Checks
- `IN_RANGE`: Feature value falls within training min/max bounds.
- `NEAR_BOUNDARY`: Feature value falls within 5% of training boundary.
- `OUT_OF_RANGE`: Feature value extrapolates outside training range.

## 3. Distance from Training Data
Calculates standardized Euclidean distance in feature space:
$$\text{Distance} = \sqrt{\sum \left(\frac{x_i - \mu_i}{\sigma_i}\right)^2}$$
Displays warning if candidate condition extrapolates outside observed domain.
