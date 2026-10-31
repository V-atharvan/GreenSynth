## Description of Changes

Please provide a clear and concise summary of the changes proposed in this pull request.

- What problem does this PR solve?
- What changes were made in the backend, frontend, or scientific calculation layer?

---

## Type of Change

Please mark the relevant option with an `x`:

- [ ] **Bug fix** (non-breaking change fixing an existing software issue)
- [ ] **New feature** (non-breaking change adding a new capability or UI module)
- [ ] **Scientific algorithm update** (modifications to mathematical formulas, physics models, or constants)
- [ ] **Breaking change** (fix or feature causing existing APIs or database schemas to change)
- [ ] **Documentation update** (improvements to user manuals, scientific specifications, or README)
- [ ] **Performance & optimization** (refactoring for latency, memory, or throughput improvements)

---

## Scientific & Mathematical Validation

If this PR introduces or modifies any scientific calculations (XRD, UV-Vis, FTIR, Electrical, SEM, DOE, ML):

- [ ] **Mathematical Integrity:** Verified that equations match established literature and physical units are strictly preserved.
- [ ] **Benchmark Agreement:** Calculated outputs agree with analytical reference baselines (e.g., OriginLab 2024, HighScore Plus, SciPy) to within $< 0.5\%$ relative error.
- [ ] **Category Isolation:** Preserved the strict distinction between `MEASURED`, `CALCULATED`, `STATISTICAL`, `PREDICTED`, and `VALIDATED` data.
- [ ] **Boundary Guardrails:** Physical boundaries are enforced (e.g., non-negative thicknesses, valid photon energy ranges, positive resistance).
- [ ] **Not Applicable** (no scientific calculation changes)

---

## Testing & Quality Assurance

- [ ] **Backend Tests:** Ran `pytest` in `backend/` — all existing and new unit/integration tests pass.
- [ ] **Frontend Tests:** Ran `npm run test` in `frontend/` — Vitest component tests pass.
- [ ] **New Tests Added:** Added corresponding test cases verifying the new functionality or edge cases.
- [ ] **Code Quality:** Formatted and linted using `ruff`, `black`, and `eslint`. No unhandled type errors.

---

## Related Issues

Fixes #(issue number)  
Closes #(issue number)

---

## Checklist

- [ ] My code adheres to the style guidelines of this project.
- [ ] I have performed a self-review of my own code.
- [ ] I have commented my code, particularly in hard-to-understand or mathematically dense areas.
- [ ] I have updated the documentation (or added docstrings) accordingly.
- [ ] My changes generate no new warnings or unhandled exceptions.
- [ ] Database migrations (if any) were created using Alembic and tested both up and down.

