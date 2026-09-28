# Phase 14: Design of Experiments (DOE) Architecture

## 1. Overview
The Design of Experiments (DOE) module in GreenSynth Analytics provides a formal, scientific framework for structured experimental exploration in semiconductor thin-film synthesis.

## 2. Core Architectural Layers
```
┌─────────────────────────────────────────────────────────────┐
│                 Frontend DOE Studio UI                      │
│ (DOEDashboard, DOEWizardModal, MatrixView, AnalysisView)    │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST API
┌──────────────────────────────▼──────────────────────────────┐
│                    DOE API Router                           │
│ (/api/v1/doe: preview, create, approve, convert, analyze)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                   DOE Service Layer                         │
│ (DOEService, DOEGeneratorFactory, DOEValidator, Linker)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│               Data Access & ORM Models                      │
│ (DOEStudy/DOE, DOEDesignRun/ProposedExperiment, DOEAnalysis)│
└─────────────────────────────────────────────────────────────┘
```

## 3. Key Entities & Status Lifecycles
- **DOEStudy (DOE)**: `DRAFT` $\rightarrow$ `CONFIGURED` $\rightarrow$ `GENERATED` $\rightarrow$ `APPROVED` $\rightarrow$ `COMPLETED` / `ARCHIVED`.
- **DOEDesignRun (ProposedExperiment)**: `PROPOSED` $\rightarrow$ `APPROVED` $\rightarrow$ `PLANNED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `COMPLETED` / `FAILED`.
- **DOEAnalysis**: Stores Main Effects ($E_A$), Interaction Effects ($E_{AB}$), Response Surface polynomial regression fit, and fit metrics ($R^2$, Adj $R^2$, RMSE, MAE, $n$).
