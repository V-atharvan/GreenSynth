# ML Data Leakage Prevention

## 1. Principles of Isolation
To prevent optimistic bias and test contamination, the ML pipeline enforces:
1. **Split-First Rule**: Raw data is split into Train, Validation, and Test sets BEFORE fitting any feature scaler or transformation.
2. **Scaler Isolation**: `StandardScaler.fit_transform()` is called strictly on Train features. `transform()` is subsequently called on Validation/Test sets.
3. **Target Isolation**: Target property values are never included in feature vectors.
4. **Duplicate Prevention**: Automated checks (`verify_no_leakage()`) verify no sample IDs overlap between splits.

## 2. Automated Tests
Mandatory unit test `test_data_leakage.py` asserts that scaler means and variance are computed solely on Train data.
