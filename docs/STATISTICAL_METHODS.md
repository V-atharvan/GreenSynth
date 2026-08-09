# GreenSynth Analytics — Statistical Methods Documentation

**System Version:** 0.1.0  
**Module:** Sample Comparison & Statistical Analysis (Phase 8)  
**Date:** 2026-08-09

---

## 1. Scientific Overview & Core Principles

The Statistical Analysis & Sample Comparison Module provides descriptive, inferential, and comparative tools to evaluate synthesis parameters and characterization properties across multiple semiconductor samples.

### Core Scientific Rules
1. **Descriptive & Associative Scope:** Statistical findings describe observed relationships within the selected sample dataset. The system **never** asserts automatic physical causation (e.g. *"Temperature causes conductivity to increase"*).
2. **Neutral Non-Causal Disclaimers:** All correlation, regression, and group comparison outputs are accompanied by explicit statistical warnings (*"Correlation describes a statistical association in the available dataset; it does not establish causation"*).
3. **Data Provenance Separation:** Variables carry clear data status badges:
   - `MEASURED`: Directly recorded synthesis parameters or instrument values.
   - `CALCULATED`: Properties derived from scientific algorithms (e.g. XRD crystallite size, UV-Vis band gap, Electrical conductivity).
   - `DETECTED`: Features identified via peak detection algorithms.
   - `ANNOTATED`: Researcher-verified interpretations.
4. **No Data Tampering:** Missing values are explicitly highlighted and reported in Data Quality Reports. Raw laboratory data is never modified or silently discarded.

---

## 2. Descriptive Statistics

**Purpose:** Calculate central tendency, dispersion, and missing data metrics for numeric variables.

**Formulas:**
- **Sample Mean ($\bar{x}$):**
  $$\bar{x} = \frac{1}{n} \sum_{i=1}^{n} x_i$$
- **Sample Median ($\tilde{x}$):** Middle value of sorted observations.
- **Sample Standard Deviation ($s$):**
  $$s = \sqrt{\frac{1}{n-1} \sum_{i=1}^{n} (x_i - \bar{x})^2}$$
- **Sample Variance ($s^2$):**
  $$s^2 = \frac{1}{n-1} \sum_{i=1}^{n} (x_i - \bar{x})^2$$
- **Range ($R$):**
  $$R = x_{\max} - x_{\min}$$

**Sample Size Warning:** If valid observations $n < 5$, a warning is emitted: *"Statistical confidence is limited due to small sample size (n < 5)."*

---

## 3. Pearson Correlation Analysis

**Purpose:** Quantify linear association between independent variable $X$ and dependent variable $Y$.

**Formula:**
$$r = \frac{\sum_{i=1}^{n} (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n} (x_i - \bar{x})^2 \sum_{i=1}^{n} (y_i - \bar{y})^2}}$$

**Requirements:** Minimum $n \ge 3$ paired numeric observations with non-zero variance.

**Interpretation Scheme:**
- $r > 0.6$: Strong positive linear association.
- $0.2 < r \le 0.6$: Moderate positive linear association.
- $-0.2 \le r \le 0.2$: Weak or no linear association.
- $-0.6 \le r < -0.2$: Moderate negative linear association.
- $r < -0.6$: Strong negative linear association.

---

## 4. Ordinary Least Squares (OLS) Linear Regression

**Purpose:** Derive empirical linear trend model describing relationship $Y = a \cdot X + b$.

**Formulas:**
- **Slope ($a$):**
  $$a = \frac{\sum_{i=1}^{n} (x_i - \bar{x})(y_i - \bar{y})}{\sum_{i=1}^{n} (x_i - \bar{x})^2}$$
- **Intercept ($b$):**
  $$b = \bar{y} - a \cdot \bar{x}$$
- **Coefficient of Determination ($R^2$):**
  $$R^2 = 1 - \frac{\sum_{i=1}^{n} (y_i - \hat{y}_i)^2}{\sum_{i=1}^{n} (y_i - \bar{y})^2}$$
- **Mean Absolute Error (MAE):**
  $$\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|$$
- **Root Mean Squared Error (RMSE):**
  $$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2}$$

**Warning:** Extrapolation beyond the measured range of $X$ is explicitly warned as unvalidated.

---

## 5. Group Factor Comparison

**Purpose:** Evaluate target variable distribution across categorical groups (e.g. `solvent`, `synthesis_method`).

**Outputs:** Per-group sample size $n$, mean, median, standard deviation, min, max.

---

## 6. Outlier Detection (1.5 * IQR Rule)

**Purpose:** Identify potential numerical anomalies in experimental variables without deleting data.

**Formula:**
$$\text{IQR} = Q_3 - Q_1$$
$$\text{Lower Bound} = Q_1 - 1.5 \times \text{IQR}$$
$$\text{Upper Bound} = Q_3 + 1.5 \times \text{IQR}$$

Observations outside $[\text{Lower Bound}, \text{Upper Bound}]$ are flagged as `Potential Outlier` for researcher review.
