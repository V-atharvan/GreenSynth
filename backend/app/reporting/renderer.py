"""
GreenSynth Analytics — ReportLab PDF Document Renderer

Generates formal, publication-grade scientific PDF reports from ExperimentReportData DTO.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.reporting.charts import ReportChartGenerator
from app.reporting.schemas import ExperimentReportData


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas for rendering 'Page X of Y' page numbers and running headers.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count: int) -> None:
        self.saveState()

        # Omit header on Cover Page (Page 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#1e293b"))
            self.drawString(36, 760, "GREENSYNTH ANALYTICS — FORMAL SCIENTIFIC EXPERIMENT REPORT")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, 752, 576, 752)

        # Running Footer on all pages
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(36, 30, "Confidential — Green Synthesis Research System (v1.0.0-research)")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 30, page_str)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(36, 42, 576, 42)

        self.restoreState()


class PDFReportRenderer:
    """
    Renders ReportLab PDF document from ExperimentReportData DTO.
    """

    @classmethod
    def render_experiment_report(cls, data: ExperimentReportData) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=48,
            bottomMargin=48,
        )

        styles = getSampleStyleSheet()

        # Custom Scientific Typography Styles
        title_style = ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
            spaceAfter=12,
        )

        h1_style = ParagraphStyle(
            "Heading1_Custom",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1e3a8a"),
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True,
        )

        body_style = ParagraphStyle(
            "Body_Custom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#ffffff"),
        )

        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1e293b"),
        )

        story: list[Any] = []

        # Helper: Render Classification Badge
        def make_badge(text: str, bg_color: str) -> Paragraph:
            return Paragraph(
                f'<font color="white"><b> [{text}] </b></font>',
                ParagraphStyle("Badge", parent=styles["Normal"], fontSize=7, fontName="Helvetica-Bold", backColor=colors.HexColor(bg_color)),
            )

        # ── 1. COVER / HEADER SECTION ────────────────────────────
        story.append(Paragraph("GREEN SYNTHESIS EXPERIMENT REPORT", ParagraphStyle("Sub", fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor("#2563eb"))))
        story.append(Paragraph(data.title, title_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563eb"), spaceAfter=14))

        # Meta summary box
        meta_data = [
            [Paragraph("<b>Experiment Code:</b>", table_cell_style), Paragraph(data.experiment_code, table_cell_style), Paragraph("<b>Report ID:</b>", table_cell_style), Paragraph(data.report_id, table_cell_style)],
            [Paragraph("<b>Project Code:</b>", table_cell_style), Paragraph(f"{data.project_code} ({data.project_name})", table_cell_style), Paragraph("<b>Generated At:</b>", table_cell_style), Paragraph(data.generated_at.strftime("%Y-%m-%d %H:%M UTC"), table_cell_style)],
            [Paragraph("<b>Researcher:</b>", table_cell_style), Paragraph(data.researcher, table_cell_style), Paragraph("<b>Software Version:</b>", table_cell_style), Paragraph(data.software_version, table_cell_style)],
        ]
        meta_table = Table(meta_data, colWidths=[110, 160, 110, 160])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # Scientific Disclaimer Box
        disc_text = (
            "<b>MANDATORY SCIENTIFIC DISCLAIMER:</b> Generated from data stored in the GreenSynth Analytics System. "
            "This report documents recorded laboratory conditions, derived physical properties, and model evaluation metrics. "
            "Model predictions and optimization suggestions are decision-support estimates requiring physical laboratory validation."
        )
        disc_table = Table([[Paragraph(disc_text, ParagraphStyle("Disc", fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#1e3a8a")))]], colWidths=[540])
        disc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#93c5fd")),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(disc_table)
        story.append(Spacer(1, 16))

        # ── 2. PROJECT INFORMATION ──────────────────────────────
        story.append(Paragraph("1. Project Configuration & Synthesis Identity", h1_style))
        proj_rows = [
            [Paragraph("Project Code", table_header_style), Paragraph("Material System", table_header_style), Paragraph("Plant Extract", table_header_style), Paragraph("Solvent", table_header_style), Paragraph("Method", table_header_style)],
            [Paragraph(data.project_code, table_cell_style), Paragraph(data.material + (f" ({data.biomass})" if data.biomass else ""), table_cell_style), Paragraph(data.extract, table_cell_style), Paragraph(data.solvent, table_cell_style), Paragraph(data.synthesis_method, table_cell_style)],
        ]
        proj_table = Table(proj_rows, colWidths=[80, 130, 110, 110, 110])
        proj_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(proj_table)
        story.append(Spacer(1, 14))

        # ── 3. SYNTHESIS PARAMETERS TABLE ──────────────────────
        story.append(Paragraph("2. Recorded Synthesis Parameters", h1_style))
        param_rows = [
            [Paragraph("Parameter Code", table_header_style), Paragraph("Parameter Name", table_header_style), Paragraph("Recorded Value", table_header_style), Paragraph("Unit", table_header_style), Paragraph("Classification", table_header_style)],
        ]
        for p in data.synthesis_parameters:
            param_rows.append([
                Paragraph(p.get("parameter_code", ""), table_cell_style),
                Paragraph(p.get("parameter_name", ""), table_cell_style),
                Paragraph(str(p.get("value", "")), ParagraphStyle("BoldVal", parent=table_cell_style, fontName="Helvetica-Bold")),
                Paragraph(str(p.get("unit", "—")), table_cell_style),
                make_badge("MEASURED DATA", "#0284c7"),
            ])
        if len(param_rows) == 1:
            param_rows.append([Paragraph("No synthesis parameters recorded.", table_cell_style), Paragraph("—", table_cell_style), Paragraph("—", table_cell_style), Paragraph("—", table_cell_style), Paragraph("—", table_cell_style)])

        param_table = Table(param_rows, colWidths=[120, 170, 90, 70, 90])
        param_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(param_table)
        story.append(Spacer(1, 14))

        # ── 4. SAMPLES & CHARACTERIZATION SUMMARY ────────────────
        story.append(Paragraph("3. Samples & Characterization Summary", h1_style))
        char_rows = [
            [Paragraph("Sample Code", table_header_style), Paragraph("Technique", table_header_style), Paragraph("Raw File Name", table_header_style), Paragraph("Analysis Status", table_header_style), Paragraph("Calculated Properties", table_header_style)],
        ]
        for c in data.characterization_summary:
            char_rows.append([
                Paragraph(c.get("sample_code", ""), table_cell_style),
                Paragraph(c.get("technique", ""), table_cell_style),
                Paragraph(c.get("raw_file", ""), table_cell_style),
                Paragraph(c.get("analysis_status", ""), table_cell_style),
                Paragraph(c.get("calculated_properties", "—"), ParagraphStyle("PropVal", parent=table_cell_style, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f766e"))),
            ])
        if len(char_rows) == 1:
            char_rows.append([Paragraph("No characterization data uploaded.", table_cell_style), Paragraph("—", table_cell_style), Paragraph("—", table_cell_style), Paragraph("—", table_cell_style), Paragraph("—", table_cell_style)])

        char_table = Table(char_rows, colWidths=[100, 70, 130, 90, 150])
        char_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(char_table)
        story.append(Spacer(1, 14))

        # ── 5. XRD CHARACTERIZATION SECTION ──────────────────────
        story.append(Paragraph("4. X-Ray Diffraction (XRD) Characterization", h1_style))
        if data.xrd.available:
            xrd_info = [
                f"<b>Raw File:</b> {data.xrd.raw_filename} | <b>Analysis Version:</b> {data.xrd.analysis_version}",
                f"<b>Crystallite Size (D):</b> <b>{data.xrd.crystallite_size_nm or 'N/A'} nm</b> [CALCULATED DATA]",
                f"<b>Formula:</b> {data.xrd.formula_used}",
                f"<i>Note: {data.xrd.disclaimer}</i>",
            ]
            for info in xrd_info:
                story.append(Paragraph(info, body_style))

            story.append(Spacer(1, 6))
            xrd_plot_bytes = ReportChartGenerator.generate_xrd_plot(peaks=data.xrd.peaks)
            xrd_img = Image(io.BytesIO(xrd_plot_bytes), width=450, height=220)
            story.append(xrd_img)
        else:
            story.append(Paragraph("<i>XRD characterization data not available for this experiment.</i>", body_style))

        story.append(Spacer(1, 14))

        # ── 6. UV-VIS SPECTROSCOPY SECTION ────────────────────────
        story.append(Paragraph("5. UV-Vis Spectroscopy & Band Gap Analysis", h1_style))
        if data.uvvis.available:
            uv_info = [
                f"<b>Raw File:</b> {data.uvvis.raw_filename} | <b>Transition Model:</b> {data.uvvis.transition_type}",
                f"<b>Optical Band Gap (Eg):</b> <b>{data.uvvis.optical_band_gap_ev or 'N/A'} eV</b> [CALCULATED DATA]",
                f"<b>Extrapolation Equation:</b> {data.uvvis.tauc_equation}",
            ]
            for info in uv_info:
                story.append(Paragraph(info, body_style))

            story.append(Spacer(1, 6))
            uv_plot_bytes = ReportChartGenerator.generate_uvvis_tauc_plot(data.uvvis.optical_band_gap_ev)
            uv_img = Image(io.BytesIO(uv_plot_bytes), width=450, height=220)
            story.append(uv_img)
        else:
            story.append(Paragraph("<i>UV-Vis spectroscopy data not available for this experiment.</i>", body_style))

        story.append(Spacer(1, 14))

        # ── 7. ELECTRICAL I-V SECTION ─────────────────────────────
        story.append(Paragraph("6. Electrical I-V Measurement & Conductivity Fit", h1_style))
        if data.electrical.available:
            elec_info = [
                f"<b>Raw File:</b> {data.electrical.raw_filename} | <b>Fit Method:</b> {data.electrical.measurement_type}",
                f"<b>Electrical Conductivity (σ):</b> <b>{data.electrical.conductivity_s_cm or 'N/A'} S/cm</b> [CALCULATED DATA]",
                f"<b>Resistivity (ρ):</b> {data.electrical.resistivity_ohm_cm or 'N/A'} Ω·cm | <b>Resistance (R):</b> {data.electrical.resistance_ohms or 'N/A'} Ω",
            ]
            for info in elec_info:
                story.append(Paragraph(info, body_style))

            story.append(Spacer(1, 6))
            elec_plot_bytes = ReportChartGenerator.generate_electrical_iv_plot(data.electrical.resistance_ohms)
            elec_img = Image(io.BytesIO(elec_plot_bytes), width=450, height=220)
            story.append(elec_img)
        else:
            story.append(Paragraph("<i>Electrical I-V measurement data not available for this experiment.</i>", body_style))

        story.append(Spacer(1, 14))

        # ── 8. ML PREDICTION & VALIDATION SECTION ─────────────────
        story.append(Paragraph("7. Machine Learning Prediction & Closed-Loop Validation", h1_style))
        if data.ml_prediction.available:
            ml_text = [
                f"<b>Trained Model:</b> {data.ml_prediction.model_name} (v{data.ml_prediction.model_version}) | <b>Cross-Validation R²:</b> {data.ml_prediction.r2_score or 'N/A'}",
                f"<b>Predicted Property:</b> {data.ml_prediction.target_property} = <b>{data.ml_prediction.predicted_value}</b> [PREDICTED DATA]",
                f"<b>95% Confidence Interval:</b> [{data.ml_prediction.lower_bound}, {data.ml_prediction.upper_bound}] | <b>Domain:</b> {data.ml_prediction.domain_status}",
                f"<i>Note: {data.ml_prediction.disclaimer}</i>",
            ]
            for t in ml_text:
                story.append(Paragraph(t, body_style))
        else:
            story.append(Paragraph("<i>No machine-learning prediction currently associated with this experiment.</i>", body_style))

        story.append(Spacer(1, 14))

        # ── 9. SCIENTIFIC DATA PROVENANCE BLOCK ───────────────────
        story.append(Paragraph("8. Data Provenance & Cryptographic Traceability", h1_style))
        prov_rows = [
            [Paragraph("Sample Code", table_header_style), Paragraph("Technique", table_header_style), Paragraph("Raw File Name", table_header_style), Paragraph("SHA-256 Checksum", table_header_style), Paragraph("Analysis Run ID", table_header_style)],
        ]
        for p in data.provenance_items:
            prov_rows.append([
                Paragraph(p.sample_code, table_cell_style),
                Paragraph(p.technique, table_cell_style),
                Paragraph(p.raw_filename, table_cell_style),
                Paragraph(p.sha256_checksum[:16] + "...", ParagraphStyle("HashVal", parent=table_cell_style, fontName="Helvetica-Bold", fontSize=7)),
                Paragraph(p.analysis_run_id[:8] if p.analysis_run_id else "—", table_cell_style),
            ])
        if len(prov_rows) == 1:
            prov_rows.append([Paragraph("No raw file provenance records.", table_cell_style), Paragraph("—", table_cell_style), Paragraph("—", table_cell_style), Paragraph("—", table_cell_style), Paragraph("—", table_cell_style)])

        prov_table = Table(prov_rows, colWidths=[90, 70, 140, 140, 100])
        prov_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(prov_table)

        # Build document using NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)
        return buffer.getvalue()
