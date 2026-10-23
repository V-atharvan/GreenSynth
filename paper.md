---
title: 'GreenSynth: A Data-Driven Research and Analytics Platform for Green Synthesis of Semiconductor Materials'
tags:
  - Python
  - FastAPI
  - React
  - Materials informatics
  - Green synthesis
  - Semiconductor materials
  - Copper oxide
  - Thin films
  - Crystallite sizing
  - Tauc plot
  - Data provenance
authors:
  - name: Atharva Nijguni Vaddepalli
    affiliation: 1
    corresponding: true
  - name: Jeevankumar Shivkumar Tolanure
    affiliation: 1
  - name: Rohan Mahadev Hede
    affiliation: 1
  - name: Shantesh Dilip Bhakare
    affiliation: 1
  - name: S. H. Pawar
    affiliation: "1, 2"
  - name: Harish T. Gurme
    affiliation: 1
affiliations:
  - name: Department of Computer Science & Engineering, N. B. Navale Sinhgad College of Engineering, Solapur, Maharashtra, India
    index: 1
  - name: Centre for Research and Technology Development (CRTD), Solapur, Maharashtra, India
    index: 2
date: 23 October 2026
bibliography: paper.bib
---

# Summary

The phytochemical-assisted synthesis of semiconductor materials leverages plant-derived reducing and capping agents to produce functional nanostructured thin films while mitigating hazardous chemical waste [@kharissova2013]. However, bench-scale materials laboratories face significant software bottlenecks: experimental protocols, synthesis parameters, and raw instrumental characterization outputs (e.g., X-ray diffraction, UV-Vis spectrophotometry, Fourier-transform infrared spectroscopy, scanning electron microscopy, and electrical probe stations) are routinely stored in disparate proprietary formats, ad-hoc spreadsheets, and disconnected one-off plotting scripts. This fragmentation introduces transcription errors, obscures analytical provenance, and impedes reproducible materials discovery.

`GreenSynth` is an open-source, full-stack research software and materials informatics platform engineered to bridge wet-laboratory synthesis protocols with automated, traceable scientific computing [@ramprasad2017]. Built with a FastAPI backend and a responsive React/TypeScript frontend, GreenSynth provides end-to-end data stewardship: cryptographic SHA-256 file ingestion, strict data category isolation (`MEASURED`, `CALCULATED`, `STATISTICAL`, `PREDICTED`, `VALIDATED`), deterministic scientific property calculation engines, and automated publication-quality research dossier generation. GreenSynth was developed and validated alongside an active experimental investigation into the phytochemical spray pyrolysis of copper oxide ($\text{CuO}$) semiconductor thin films using mulberry (*Morus alba*) leaf extract [@perednis2005].

# Statement of Need

Materials scientists and experimental chemists frequently rely on commercial graphing suites (e.g., OriginLab) or general spreadsheet software (e.g., Microsoft Excel) to process raw instrument outputs. While versatile for manual curve fitting, these desktop tools lack:

1. **Automated Data Provenance:** Calculated parameters (such as mean crystallite diameter or optical bandgap energy) are rarely linked programmatically to the raw instrument file hash, processing parameters, and formula versions.
2. **Category Isolation:** Unchecked spreadsheet calculations often blend directly measured instrumental data with derived physical models, statistical averages, or synthetic benchmarking values.
3. **Reproducibility and Modularity:** Established Python materials packages—such as `pymatgen` [@jain2013pymatgen] or `ASE` [@larsen2017ase]—focus primarily on computational density functional theory (DFT), crystallographic symmetry files, or atomic simulations, rather than wet-lab synthesis tracking, automated multi-instrument characterization pipelines, and real-time laboratory data ingestion.

GreenSynth fulfills this need by providing an open, standards-compliant platform that packages domain-specific characterization algorithms into reusable Python services while offering an intuitive, web-based graphical interface for laboratory researchers.

# Software Architecture and Key Features

GreenSynth is organized as a decoupled, multi-tier scientific software system:

```
┌─────────────────────────────────────────────────────────────┐
│                 React + TypeScript Frontend                 │
│      (Interactive Spectra, Tauc Plots, Dashboards, UI)      │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST API / JSON
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend Engine                   │
│  ┌───────────────────────┐       ┌───────────────────────┐  │
│  │  Data Stewardship &   │       │ Scientific Analytics  │  │
│  │ Cryptographic SHA-256 │       │  Domain Services      │  │
│  └───────────┬───────────┘       └───────────┬───────────┘  │
│              │                               │              │
│  ┌───────────▼───────────┐       ┌───────────▼───────────┐  │
│  │ Storage & PostgreSQL  │       │ XRD, UV-Vis, FTIR,    │  │
│  │   Alembic Migrations  │       │ Electrical Engines    │  │
│  └───────────────────────┘       └───────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Deterministic Scientific Calculation Engines

The platform implements dedicated calculation engines within its backend domain services:

- **X-Ray Diffraction (XRD) Crystallite Sizing:** Implements automated peak detection and baseline subtraction to compute crystallite size ($D$) via the Debye-Scherrer formula [@scherrer1918]:
  $$D = \frac{K \cdot \lambda}{\beta \cdot \cos\theta}$$
  where $K = 0.94$ (shape factor), $\lambda = 0.15406\text{ nm}$ ($\text{Cu K}\alpha$ radiation), $\theta$ is the Bragg diffraction angle, and $\beta$ is the full width at half maximum (FWHM) in radians.
- **UV-Vis Optical Bandgap Determination:** Processes wavelength ($\lambda$) and absorbance ($A$), converts photon energy ($h\nu = 1239.84193/\lambda\text{ eV}$), calculates absorption coefficient ($\alpha = 2.303 \cdot A / t$), and executes linear regression on the linear region of the direct Tauc relation [@tauc1966]:
  $$(\alpha h\nu)^2 = B(h\nu - E_g)$$
  yielding the direct optical bandgap ($E_g$) at the horizontal axis intercept.
- **FTIR Spectroscopy & Functional Group Attribution:** Automatically identifies vibrational absorption bands (e.g., $\text{Cu--O}$ stretching at $530\text{--}610\text{ cm}^{-1}$, $\text{O--H}$ stretching at $3200\text{--}3500\text{ cm}^{-1}$, and carbonyl $\text{C=O}$ vibrations from phytochemical constituents) with polynomial baseline correction.
- **Electrical Transport Analysis:** Evaluates two-probe current-voltage ($I\text{--}V$) characteristics to compute electrical resistivity ($\rho$), sheet resistance ($R_s$), and activation energies across varying temperature regimes.

### Cryptographic Provenance and Immutability

Raw experimental files (ASCII `.txt`, `.csv`, `.xy`) are assigned a cryptographic SHA-256 checksum upon upload. Once ingested, raw experimental records are marked immutable. Any analytical transformation creates a versioned `AnalysisRun` entity that explicitly stores the formula name, input file hash, algorithm version, and fitting parameters.

# Research Application: Phytochemical Synthesis of CuO Thin Films

GreenSynth served as the central research data platform for the experimental synthesis of nanocrystalline cupric oxide ($\text{CuO}$) thin films. In this investigation, mulberry (*Morus alba*) leaves were extracted in ethanol to provide phytochemical reducing and stabilizing agents. Thin films were deposited onto preheated glass substrates via chemical spray pyrolysis using an optimized precursor mixture of copper sulfate pentahydrate ($\text{CuSO}_4{\cdot}5\text{H}_2\text{O}$) and sodium hydroxide ($\text{NaOH}$). 

GreenSynth ingested the multi-technique laboratory datasets across deposition temperatures ($300^\circ\text{C}\text{--}400^\circ\text{C}$), automatically extracting monoclinic $\text{CuO}$ crystallite dimensions ($D \approx 18\text{--}24\text{ nm}$), confirming direct optical bandgaps ($E_g \approx 1.85\text{--}2.10\text{ eV}$), and compiling reproducible, publication-ready PDF research dossiers.

# Quality Assurance and Testing

The repository contains an automated test suite comprising 98 test files:
- **Backend Tests (`pytest`):** 47 unit and 28 integration test suites verifying mathematical accuracy against analytical benchmarks, API authorization, and database persistence with both SQLite (in-memory) and PostgreSQL 16.
- **Frontend Tests (`Vitest`):** 23 component test suites verifying user interface states, input validation, and interactive spectra rendering.
- **Continuous Integration:** Fully automated via GitHub Actions, running linting (Ruff), type-checking (TypeScript), Alembic schema migrations, and coverage reporting on every commit.

# AI Usage Disclosure

In compliance with the JOSS Generative AI Policy, generative AI tools (Anthropic Claude and Google Gemini via the Antigravity development environment) were employed for boilerplate code scaffolding, automated test generation, schema refactoring, and initial documentation drafting. The human authors manually designed all platform architecture, authored and validated all mathematical equations and scientific algorithms, reviewed and revised all source code and documentation, and take full responsibility for the contents of the software and manuscript.

# Acknowledgements

The authors express their sincere gratitude to Dr. S. H. Pawar, Director of the Centre for Research and Technology Development (CRTD), for valuable guidance, encouragement, and laboratory facilities. We thank Prof. Harish T. Gurme, Prof. V. V. Palmur, and the Department of Computer Science & Engineering at N. B. Navale Sinhgad College of Engineering, Solapur, affiliated to Punyashlok Ahilyadevi Holkar Solapur University, for academic and technical support.

# References
