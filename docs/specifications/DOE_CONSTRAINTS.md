# DOE Constraint Engine & Unit Validation

## 1. Constraint Rules
1. **Factor Bounds**: $L_i \le x_i \le U_i$.
2. **Applied Constraints**: Operators `>=, <=, =, BETWEEN, IN`.
3. **Unit Consistency**: Parameter definitions and constraints must specify compatible physical units (e.g. °C, mL/min, M, S/cm).

## 2. Validation Failure Handling
If all generated candidate runs violate configured constraints, DOE matrix generation raises an explicit `ValueError` blocking design creation.
