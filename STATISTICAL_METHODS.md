# Statistical Methods & Regression Models

## 1. Descriptive Statistics
Always reports sample size $N$. Calculates mean, median, standard deviation, variance, minimum, maximum, range, Q1, Q3, IQR, and Coefficient of Variation (CV).

## 2. Correlation Analysis
- **Pearson Correlation**: Measures linear association for continuous variables.
- **Spearman Correlation**: Measures monotonic rank-based association.
- **Warnings**: Automatically flags $N < 10$ or missing observations.

## 3. Regression Models
- **Simple Linear**: $y = \beta_0 + \beta_1 x_1$.
- **Multiple Linear**: $y = \beta_0 + \sum \beta_i x_i$.
- **Interaction**: $y = \beta_0 + \sum \beta_i x_i + \sum \beta_{ij} x_i x_j$.
- **Quadratic**: $y = \beta_0 + \sum \beta_i x_i + \sum \beta_{ij} x_i x_j + \sum \beta_{ii} x_i^2$.
- **Model Selection Metrics**: $R^2$, Adjusted $R^2$, RMSE, MAE, AIC, BIC.
