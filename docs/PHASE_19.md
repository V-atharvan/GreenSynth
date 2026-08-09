# Phase 19 — Configuration-Driven Multi-Project Research Platform

## Overview
Phase 19 extends the GreenSynth Analytics System from a single primary target (Project 7) to a **Configuration-Driven Multi-Project Research Platform** representing all eight planned laboratory synthesis projects (P1 through P8) without code duplication or hardcoded project business logic.

## The 8 Laboratory Projects Matrix

```
             ETHANOL       ACETONE

SOL-GEL        P1             P2

HYDROTHERMAL   P3             P4

SPRAY          P7             P8
PYROLYSIS

RICE HUSK
HYDROTHERMAL   P5             P6
(Silica/Si)
```

## Architectural Design Principles
1. **Shared Synthesis Engines**: `SolGelMethod` (P1/P2), `HydrothermalMethod` (P3–P6), `SprayPyrolysisMethod` (P7/P8).
2. **Domain Catalogs**: Material (`CuO`, `Silica`, `Silicon`), Biomass (`Rice husk`), Extract (`Mulberry extract`), Solvent (`Ethanol`, `Acetone`), Method (`SOL_GEL`, `HYDROTHERMAL`, `SPRAY_PYROLYSIS`).
3. **Biomass vs. Extract Distinction**: Rice husk is stored as `Biomass`, Mulberry as `PlantExtract` for Projects 5 & 6.
4. **Configuration Version Snapshots**: When experiments are created, the `ProjectConfigurationVersion` snapshot is saved. Historical experiments remain immutable.
5. **Cross-Project Property Comparability**: `PropertyComparabilityService` checks material system, synthesis method, and target property before allowing comparisons across projects.
