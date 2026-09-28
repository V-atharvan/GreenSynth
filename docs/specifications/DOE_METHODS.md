# DOE Methods & Mathematical Formulas

## 1. Supported Design Methods
1. **Full Factorial Design ($2^k, 3^k$)**:
   - Evaluates all combinations of factor levels.
   - Base runs: $N = \prod_{i=1}^k L_i$.
2. **Fractional Factorial Design ($2^{k-1}$)**:
   - Half-fraction designs reducing experimental runs for screening.
   - Includes design resolution indicators (`Res IV`, `Res III`) and confounding warnings.
3. **Central Composite Design (CCD)**:
   - Response surface design incorporating 2-level factorial points ($2^k$), axial/star points ($2k$), and center points ($n_c$).
   - Total base runs: $N = 2^k + 2k + n_c$.
4. **Box-Behnken Design**:
   - 3-level response surface design avoiding extreme axial corner points.
   - Total base runs for $k \ge 3$: $N = 2k(k-1) + n_c$.
5. **Randomized Candidate Design**:
   - Reproducible random selection within defined continuous/discrete bounds using a stored `random_seed`.
