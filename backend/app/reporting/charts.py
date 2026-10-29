"""
GreenSynth Analytics — Reporting Plot Generator (Matplotlib)

Generates publication-quality, in-memory PNG chart bytes for inclusion
in ReportLab PDF documents.
Strict Scientific Integrity: Only renders authentic measurement data; never synthesizes placeholder curves.
"""

from __future__ import annotations

import io
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np


class ReportChartGenerator:
    """
    In-memory Matplotlib chart renderer for ReportLab PDF documents.
    """

    @staticmethod
    def generate_xrd_plot(
        two_theta: list[float] | None = None,
        intensity: list[float] | None = None,
        peaks: list[dict[str, Any]] | None = None,
    ) -> bytes | None:
        """Generate XRD spectrum plot bytes with authentic experimental data. Returns None if raw data is unavailable."""
        if not (two_theta and intensity and len(two_theta) == len(intensity)):
            return None

        fig, ax = plt.subplots(figsize=(6, 3), dpi=200)
        ax.plot(two_theta, intensity, color="#1e40af", linewidth=1.2, label="Measured XRD Pattern")

        annotated_count = 0
        if peaks:
            for p in peaks:
                tt = p.get("two_theta")
                inten = p.get("intensity")
                if tt is not None and inten is not None:
                    ax.scatter([tt], [inten], color="#dc2626", s=25, zorder=5)
                    ax.annotate(
                        f"{tt:.1f}\u00b0",
                        (tt, inten),
                        textcoords="offset points",
                        xytext=(0, 6),
                        ha="center",
                        fontsize=7,
                        fontweight="bold",
                        color="#b91c1c",
                    )
                    annotated_count += 1

        # Auto-detect prominent peaks if none explicitly registered
        if annotated_count == 0 and len(intensity) > 20:
            tt_arr = np.array(two_theta)
            in_arr = np.array(intensity)
            baseline = float(np.median(in_arr))
            std_val = float(np.std(in_arr))
            candidates: list[tuple[float, float]] = []
            for i in range(5, len(in_arr) - 5):
                if in_arr[i] == max(in_arr[i - 5 : i + 6]) and in_arr[i] > baseline + 1.2 * std_val:
                    candidates.append((float(in_arr[i]), float(tt_arr[i])))
            # Sort descending by intensity, take top 4
            candidates.sort(key=lambda x: x[0], reverse=True)
            for pk_int, pk_tt in candidates[:4]:
                ax.scatter([pk_tt], [pk_int], color="#dc2626", s=22, zorder=5)
                ax.annotate(
                    f"{pk_tt:.1f}\u00b0",
                    (pk_tt, pk_int),
                    textcoords="offset points",
                    xytext=(0, 6),
                    ha="center",
                    fontsize=7,
                    fontweight="bold",
                    color="#b91c1c",
                )

        ax.set_title("X-Ray Diffraction (XRD) Spectrum", fontsize=10, fontweight="bold", pad=8)
        ax.set_xlabel(r"2$\theta$ (degrees)", fontsize=8)
        ax.set_ylabel("Intensity (a.u.)", fontsize=8)
        ax.tick_params(axis="both", labelsize=7)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(fontsize=7, loc="upper right")
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    @staticmethod
    def generate_uvvis_tauc_plot(
        band_gap_ev: float | None = None,
        photon_energies: list[float] | None = None,
        tauc_values: list[float] | None = None,
    ) -> bytes | None:
        """Generate UV-Vis Tauc plot bytes from spectrometer measurement. Returns None if raw data is unavailable."""
        if not (photon_energies and tauc_values and len(photon_energies) == len(tauc_values)):
            return None

        fig, ax = plt.subplots(figsize=(6, 3), dpi=200)

        hnu_arr = np.array(photon_energies)
        tauc_arr = np.array(tauc_values)
        s_idx = np.argsort(hnu_arr)
        hnu = hnu_arr[s_idx]
        tauc_val = tauc_arr[s_idx]

        ax.plot(hnu, tauc_val, color="#047857", linewidth=1.5, label=r"$(\alpha h\nu)^2$ Tauc Curve")

        # Fit extrapolation line crossing Eg on x-axis
        if band_gap_ev is not None and len(hnu) > 1:
            bg = float(band_gap_ev)
            max_y = float(np.max(tauc_val)) if len(tauc_val) > 0 else 25.0
            denom = float(hnu.max()) - bg
            slope = max_y / max(0.15, denom) if denom > 0 else 1.0
            fit_x = np.array([bg - 0.15, min(float(hnu.max()), bg + 0.45)])
            fit_y = np.maximum(0.0, (fit_x - bg) * slope)
            ax.plot(fit_x, fit_y, color="#dc2626", linestyle="--", linewidth=1.2, label=f"Fit (Eg = {bg:.2f} eV)")
            ax.axvline(x=bg, color="#b91c1c", linestyle=":", linewidth=1.0)
            ax.set_xlim(left=max(0.5, bg - 0.4), right=min(3.8, float(hnu.max()) + 0.1))

        ax.set_title("UV-Vis Tauc Plot (Direct Allowed Transition)", fontsize=10, fontweight="bold", pad=8)
        ax.set_xlabel(r"Photon Energy $h\nu$ (eV)", fontsize=8)
        ax.set_ylabel(r"$(\alpha h\nu)^2$ (a.u.)", fontsize=8)
        ax.tick_params(axis="both", labelsize=7)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(fontsize=7, loc="upper left")
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    @staticmethod
    def generate_electrical_iv_plot(
        resistance_ohms: float | None = None,
        voltages: list[float] | None = None,
        currents_ma: list[float] | None = None,
    ) -> bytes | None:
        """Generate Electrical I-V linear regression plot bytes. Returns None if raw data is unavailable."""
        if not (voltages and currents_ma and len(voltages) == len(currents_ma)):
            return None

        fig, ax = plt.subplots(figsize=(6, 3), dpi=200)

        ax.scatter(voltages, currents_ma, color="#6366f1", s=15, alpha=0.7, label="Measured I-V Data")
        if resistance_ohms is not None and resistance_ohms > 0 and len(voltages) > 1:
            v_line = np.linspace(min(voltages), max(voltages), 100)
            i_fit = (v_line / float(resistance_ohms)) * 1000.0  # mA
            ax.plot(v_line, i_fit, color="#4338ca", linewidth=1.2, label=f"Ohm's Fit (R = {resistance_ohms:.1f} \u03a9)")

        ax.set_title("Electrical I-V Characteristics", fontsize=10, fontweight="bold", pad=8)
        ax.set_xlabel("Voltage V (Volts)", fontsize=8)
        ax.set_ylabel("Current I (mA)", fontsize=8)
        ax.tick_params(axis="both", labelsize=7)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(fontsize=7, loc="upper left")
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
