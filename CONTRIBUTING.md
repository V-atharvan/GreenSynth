# Contributing to GreenSynth

Thank you for your interest in contributing to **GreenSynth**, a data-driven research and analytics platform for the green synthesis of semiconductor materials. We welcome contributions from scientific software developers, computational materials scientists, chemists, and research engineers.

---

## Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to `v.atharvan@gmail.com`.

---

## How Can I Contribute?

You can contribute in several ways:
1. **Reporting Bugs:** File an issue describing the unexpected behavior, system specifications, and exact steps or dataset required to reproduce.
2. **Suggesting Enhancements:** Propose new characterization techniques (e.g., Raman spectroscopy, PL spectroscopy, XPS), improvements to analytical algorithms, or UI enhancements.
3. **Scientific Corrections & Algorithmic Provenance:** Report any discrepancies in scientific formulas, physical constants, or standard reference values.
4. **Code Contributions:** Fix existing issues, add test cases, or implement new modules.
5. **Documentation & Tutorials:** Improve user manuals, API reference docs, or provide sample experimental data files.

---

## Development Environment Setup

### Prerequisites
- **Python**: Version 3.11 or higher
- **Node.js**: Version 18 or higher (LTS recommended) and `npm`
- **PostgreSQL**: Version 15 or higher (or use Docker / SQLite for local unit testing)
- **Git**

### Backend Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/V-atharvan/GreenSynth.git
   cd GreenSynth/backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install backend dependencies (including scientific & development packages):
   ```bash
   pip install -e ".[dev,scientific]"
   ```
4. Copy the environment configuration:
   ```bash
   cp ../.env.example ../.env
   # Update database credentials in .env as needed
   ```
5. Run database migrations:
   ```bash
   alembic upgrade head
   ```
6. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The application UI will be available at `http://localhost:5173`.

---

## Running Automated Tests

Before submitting code changes, verify that all test suites pass:

### 1. Backend Unit & Integration Tests (pytest)
```bash
cd backend
pytest tests/ -v
```
To run tests with code coverage:
```bash
pytest --cov=greensynth --cov=app tests/
```

### 2. Frontend Unit & Component Tests (Vitest)
```bash
cd frontend
npm run test
```
To check TypeScript types and linting:
```bash
npm run typecheck
npm run lint
```

---

## Scientific Rigor & Algorithmic Provenance

GreenSynth is scientific research software. When adding or modifying physical characterization calculations (such as Scherrer crystallite sizing, Tauc plot optical bandgap extraction, FTIR peak matching, or electrical resistivity calculations):

1. **Document the Mathematical Provenance:** State the exact equation, physical units (e.g., eV, nm, Å, S/cm), and primary academic citations in docstrings.
2. **Include Ground-Truth Unit Tests:** Every analytical function must be accompanied by unit tests with known analytical values or benchmark experimental datasets.
3. **Handle Edge Cases Gracefully:** Ensure mathematical singularities (e.g., divide-by-zero, negative absorbance, zero baseline) raise descriptive validation errors rather than unhandled server exceptions.

---

## Pull Request Guidelines

1. **Create a Topic Branch:** Create a branch from `main` using a descriptive name:
   ```bash
   git checkout -b feat/tauc-direct-bandgap
   # or
   git checkout -b fix/xrd-baseline-noise
   ```
2. **Follow Commit Conventions:** Use clear, conventional commit messages:
   - `feat(...)`: New feature or analytical pipeline
   - `fix(...)`: Bug fix or mathematical correction
   - `docs(...)`: Documentation or tutorial updates
   - `test(...)`: Adding or improving test cases
3. **Keep PRs Focused:** Avoid bundling unrelated changes into a single pull request.
4. **Pass All CI Checks:** Ensure linting, type-checking, and all automated tests pass.
5. **Update Documentation:** If your change modifies API schemas or configuration variables, update the documentation and `.env.example` accordingly.

Thank you for helping advance open, reproducible research in materials science!
