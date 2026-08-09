# DOE Statistics & Regression Model Fitting

## 1. Main Factor Effects
Main Effect estimate for factor $A$:
$$E_A = \bar{Y}_{A, \text{high}} - \bar{Y}_{A, \text{low}}$$

## 2. Interaction Effects
Two-factor interaction effect estimate for factors $A$ and $B$:
$$E_{AB} = \frac{1}{2} \left[ (\bar{Y}_{A+B+} - \bar{Y}_{A+B-}) - (\bar{Y}_{A-B+} - \bar{Y}_{A-B-}) \right]$$

## 3. Polynomial Response Surface Model
Second-order polynomial response surface model:
$$y = \beta_0 + \sum_{i=1}^k \beta_i x_i + \sum_{i < j} \beta_{ij} x_i x_j + \sum_{i=1}^k \beta_{ii} x_i^2 + \epsilon$$

## 4. Goodness-of-Fit Metrics
- Coefficient of Determination ($R^2$):
  $$R^2 = 1 - \frac{SS_{\text{res}}}{SS_{\text{tot}}}$$
- Adjusted $R^2$:
  $$R^2_{\text{adj}} = 1 - \left(1 - R^2\right) \frac{n - 1}{n - p - 1}$$
- Root Mean Square Error ($\text{RMSE}$):
  $$\text{RMSE} = \sqrt{\frac{\sum e_i^2}{n}}$$
