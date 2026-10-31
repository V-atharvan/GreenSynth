# Accessibility Statement — GreenSynth Analytics Platform

GreenSynth is committed to ensuring digital accessibility for people of all abilities, including researchers, students, and engineers with visual, motor, auditory, or cognitive disabilities.

We continually improve the user experience for everyone and apply relevant accessibility standards to all web-based laboratory interfaces, interactive spectral visualization tools, and generated research documents.

---

## Conformance Status

The Web Content Accessibility Guidelines ([WCAG](https://www.w3.org/WAI/standards-guidelines/wcag/)) define requirements for designers and developers to improve accessibility for people with disabilities. It defines three levels of conformance: Level A, Level AA, and Level AAA.

**GreenSynth Analytics is partially conformant with WCAG 2.1 Level AA.**  
"Partially conformant" means that while the core user interface, forms, data tables, navigation, and PDF reports conform to Level AA standards, certain complex interactive SVG canvas tools (such as real-time multi-peak draggable calipers) are continuously being enhanced with keyboard and assistive technology alternatives.

---

## Accessibility Features in GreenSynth

### 1. Visual Presentation & Color Contrast
- **High-Contrast Scientific Palettes:** Interactive spectral plots (XRD, UV-Vis, FTIR, and electrical $I\text{--}V$ curves) utilize color palettes with minimum contrast ratios of **4.5:1** against the canvas background, ensuring legibility for users with low vision or color vision deficiencies (protanopia, deuteranopia, and tritanopia).
- **Distinguishable Trace Styling:** Multi-curve comparison charts employ distinct dash patterns (solid, dashed, dotted) and data point markers in addition to color encoding, avoiding reliance on color alone.
- **Fluid Text Scaling:** The interface supports browser zoom up to **200%** without loss of functionality, layout breakage, or overlapping text.

### 2. Keyboard Navigation & Focus Management
- **Full Keyboard Operability:** All navigation links, tabs, buttons, form controls, and modal dialogs are operable using standard keyboard navigation (`Tab`, `Shift+Tab`, `Enter`, `Space`, `Escape`, arrow keys).
- **Visible Focus Indicators:** Interactive elements display a high-visibility focus ring when navigating via keyboard.
- **Skip Links:** Skip-to-content links allow keyboard users to bypass redundant navigation sidebars and jump directly to the primary research dashboard.

### 3. Assistive Technology & Semantic HTML
- **Semantic Structure:** Pages are constructed using semantic HTML5 landmarks (`<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`) to ensure screen readers (NVDA, JAWS, VoiceOver, Orca) can navigate the hierarchy efficiently.
- **ARIA Attributes:** Dynamic components, status badges (e.g., `MEASURED`, `CALCULATED`, `PREDICTED`), modal dialogs, and asynchronous loading spinners are annotated with appropriate `aria-live`, `aria-label`, and `role` attributes.
- **Accessible Data Alternatives:** In addition to interactive graphical canvas representations, all characterization data and calculated properties are accessible through structured tabular views (`<table>` with row/column headers) and downloadable raw CSV files.

### 4. Reduced Motion
- GreenSynth respects user operating system preferences for reduced motion (`prefers-reduced-motion`). Transitions, graph animations, and sliding drawers are automatically disabled or simplified when this preference is enabled.

---

## Supported Environments

GreenSynth is tested and designed to be compatible with:
- **Operating Systems:** Windows 10/11, Ubuntu Linux 22.04+, macOS Sonoma+
- **Browsers:** Google Chrome (latest), Mozilla Firefox (latest), Microsoft Edge (latest), Apple Safari (latest)
- **Screen Readers:** NVDA (Windows), JAWS (Windows), VoiceOver (macOS / iOS)

---

## Known Limitations and Workarounds

Despite our best efforts to ensure accessibility across GreenSynth, some limitations may occur:

1. **Complex Interactive Canvas Calipers:**  
   *Limitation:* Dragging pixel calibration markers on high-resolution SEM micrographs currently requires mouse pointer precision.  
   *Workaround:* Researchers can manually enter numeric scale bar and pixel dimensions into the standard HTML input fields provided adjacent to the viewer.
2. **Dynamic WebGL / Canvas Tooltips:**  
   *Limitation:* Rapid mouse hover tooltips on continuous 5,000-point spectra may not always announce instantly to screen readers.  
   *Workaround:* Use the "View Tabular Coordinates" toggle to inspect discrete numerical data points in an accessible table format.

---

## Feedback & How to Report Accessibility Barriers

We welcome your feedback on the accessibility of GreenSynth. If you encounter accessibility barriers, experience difficulty using any module, or have recommendations for improvement:

- **Email:** `v.atharvan@gmail.com`
- **GitHub Issues:** File an issue using our [Bug Report Form](https://github.com/V-atharvan/GreenSynth/issues/new?template=bug_report.yml) with the label `accessibility`.
- **Subject:** `[ACCESSIBILITY] Issue Report - GreenSynth`

Please include the web page URL or module, your assistive technology setup (browser and screen reader version), and a description of the barrier. We aim to acknowledge reports within **48 hours** and provide a resolution roadmap within **10 business days**.

---

## Formal Approval & Review

This Accessibility Statement was created on **October 31, 2026**, and is reviewed alongside every minor and major software release.

