# GreenSynth Analytics — UI & Iconography Guidelines

## 1. Core Principles

GreenSynth Analytics is a production-grade scientific research platform. The interface maintains a professional, academic aesthetic suitable for materials science laboratories and research publications.

## 2. Zero Emoji Policy

* **No Emojis in UI**: Decorative Unicode emojis (such as 🧪, 🔬, 📊, ⚡, 🧠, 📁, 🚀, ⚠️, ✕) are **strictly forbidden** in all application UI components, headers, buttons, cards, modals, and notifications.
* **Icon System Standard**: All visual UI icons must be sourced directly from the project's standard icon library, **Lucide React** (`lucide-react`).

## 3. Scientific Notation & Mathematical Symbol Exceptions

The zero-emoji policy applies strictly to decorative emojis. The following mathematical, chemical, and physical symbols are standard scientific notation and **MUST** be preserved across all forms, tables, plots, and PDF exports:

| Category | Symbols | Usage Examples |
| :--- | :--- | :--- |
| **Units & Measurements** | `°C`, `µm`, `nm`, `eV`, `S/cm`, `Ω`, `%` | Temperature (`°C`), Wavelength (`nm`), Band gap (`eV`) |
| **Greek Letters & Coefficients** | `α`, `β`, `γ`, `Δ`, `θ`, `λ`, `µ`, `ρ`, `σ`, `Ω`, `ω` | Bragg angle (`2θ`), Crystallite size (`D`), Wavelength (`λ`) |
| **Exponents & Subscripts** | `²`, `³`, `⁻¹`, `⁻²` | Wavenumber (`cm⁻¹`), Volume (`cm³`), Area (`cm²`) |
| **Relational & Directional** | `±`, `≤`, `≥`, `→`, `≈`, `≠` | Uncertainty (`±0.05`), Trend direction (`→`), Limits (`≤`) |

## 4. Standardized Lucide Icon Mapping

Developers adding new features or components should reuse the following standardized icon mappings:

| Action / Entity | Lucide Icon | Component Code |
| :--- | :--- | :--- |
| Projects & Datasets | `FolderKanban`, `Database` | `<FolderKanban size={18} />`, `<Database size={18} />` |
| Experiments | `FlaskConical` | `<FlaskConical size={18} />` |
| Physical Samples | `TestTube2` | `<TestTube2 size={18} />` |
| Characterization & Charts | `BarChart3`, `TrendingUp`, `Ruler` | `<BarChart3 size={18} />`, `<TrendingUp size={18} />` |
| Machine Learning & Models | `Cpu`, `ShieldCheck` | `<Cpu size={18} />`, `<ShieldCheck size={18} />` |
| Alert / Warning | `AlertTriangle` | `<AlertTriangle size={16} />` |
| Success / Complete | `Check` | `<Check size={16} />` |
| Close Action / Dismiss | `X` | `<X size={18} />` |
| File Upload / Download | `Upload`, `Download` | `<Upload size={18} />`, `<Download size={18} />` |

## 5. Enforcement & Code Reviews

Before submitting PRs or deploying feature branches:
1. Run linting and typechecking: `npx tsc --noEmit`
2. Verify frontend build: `npm run build`
3. Ensure no unicode emojis are added to JSX templates, page headers, or component prop strings.
