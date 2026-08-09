"""
GreenSynth Analytics — ML Dataset Builder

Pure Python module to extract, assemble, and validate training data records from
experimental observations, synthesis parameters, and calculated properties.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecordExclusion:
    experiment_id: str
    sample_id: str
    reason: str  # MISSING_FEATURE, MISSING_TARGET, INVALID_UNIT, INVALID_VALUE, DUPLICATE_RECORD, etc.
    details: str


@dataclass
class DatasetRecordItem:
    experiment_id: str
    sample_id: str
    analysis_run_id: str | None
    feature_values: dict[str, float]
    target_value: float | None
    target_unit: str
    is_eligible: bool
    exclusion_reason: str | None = None
    provenance_details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DatasetBuildResult:
    dataset_name: str
    target_property: str
    target_unit: str
    feature_names: list[str]
    records: list[DatasetRecordItem]
    eligible_count: int
    excluded_count: int
    exclusion_summary: dict[str, int]
    is_synthetic: bool = False


class DatasetBuilder:
    """
    Assembles feature matrix and target vector from raw experiment parameter records and characterization properties.
    Enforces strict eligibility rules and records explicit exclusion reasons for ineligible samples.
    """

    def __init__(self, target_property: str, target_unit: str, feature_specs: list[dict[str, Any]]) -> None:
        self.target_property = target_property
        self.target_unit = target_unit
        self.feature_specs = feature_specs  # [{"feature_name": "temp", "source_parameter": "substrate_temperature", "unit": "°C"}]
        self.feature_names = [f["feature_name"] for f in feature_specs]

    def build_records(
        self,
        candidate_items: list[dict[str, Any]],
        dataset_name: str = "ML Dataset",
        is_synthetic: bool = False,
    ) -> DatasetBuildResult:
        """
        Process a list of raw experiment/sample observation dictionaries into structured DatasetRecordItems.

        Each item in candidate_items is expected to have:
          - experiment_id: str
          - sample_id: str
          - experiment_status: str ("COMPLETED", "PLANNED", etc.)
          - parameters: dict[str, Any] (e.g. {"substrate_temperature": 350.0})
          - properties: dict[str, Any] (e.g. {"conductivity": 5.2})
          - parameter_units: dict[str, str]
          - property_units: dict[str, str]
          - analysis_run_id: str | None
        """
        records: list[DatasetRecordItem] = []
        exclusion_summary: dict[str, int] = {}
        seen_signatures: set[str] = set()

        for item in candidate_items:
            exp_id = str(item.get("experiment_id", ""))
            smp_id = str(item.get("sample_id", ""))
            exp_status = item.get("experiment_status", "COMPLETED")
            params = item.get("parameters", {})
            props = item.get("properties", {})
            param_units = item.get("parameter_units", {})
            prop_units = item.get("property_units", {})
            analysis_run_id = item.get("analysis_run_id")

            # Rule 1: Check Experiment Status
            if exp_status in ("PLANNED", "PROPOSED", "CANCELLED", "ARCHIVED"):
                reason = "INCOMPLETE_EXPERIMENT"
                exclusion_summary[reason] = exclusion_summary.get(reason, 0) + 1
                records.append(
                    DatasetRecordItem(
                        experiment_id=exp_id,
                        sample_id=smp_id,
                        analysis_run_id=analysis_run_id,
                        feature_values={},
                        target_value=None,
                        target_unit=self.target_unit,
                        is_eligible=False,
                        exclusion_reason=reason,
                        provenance_details={"status": exp_status},
                    )
                )
                continue

            # Rule 2: Check Target Property
            target_val = props.get(self.target_property)
            if target_val is None or target_val == "":
                reason = "MISSING_TARGET"
                exclusion_summary[reason] = exclusion_summary.get(reason, 0) + 1
                records.append(
                    DatasetRecordItem(
                        experiment_id=exp_id,
                        sample_id=smp_id,
                        analysis_run_id=analysis_run_id,
                        feature_values={},
                        target_value=None,
                        target_unit=self.target_unit,
                        is_eligible=False,
                        exclusion_reason=reason,
                        provenance_details={"target_property": self.target_property},
                    )
                )
                continue

            try:
                target_float = float(target_val)
            except (ValueError, TypeError):
                reason = "INVALID_VALUE"
                exclusion_summary[reason] = exclusion_summary.get(reason, 0) + 1
                records.append(
                    DatasetRecordItem(
                        experiment_id=exp_id,
                        sample_id=smp_id,
                        analysis_run_id=analysis_run_id,
                        feature_values={},
                        target_value=None,
                        target_unit=self.target_unit,
                        is_eligible=False,
                        exclusion_reason=reason,
                        provenance_details={"raw_target_value": str(target_val)},
                    )
                )
                continue

            # Rule 3: Check Features
            feature_values: dict[str, float] = {}
            missing_feature = False
            missing_name = ""

            for spec in self.feature_specs:
                fname = spec["feature_name"]
                src_key = spec.get("source_parameter", fname)
                val = params.get(src_key)

                if val is None or val == "":
                    missing_feature = True
                    missing_name = fname
                    break

                try:
                    feature_values[fname] = float(val)
                except (ValueError, TypeError):
                    missing_feature = True
                    missing_name = fname
                    break

            if missing_feature:
                reason = "MISSING_FEATURE"
                exclusion_summary[reason] = exclusion_summary.get(reason, 0) + 1
                records.append(
                    DatasetRecordItem(
                        experiment_id=exp_id,
                        sample_id=smp_id,
                        analysis_run_id=analysis_run_id,
                        feature_values=feature_values,
                        target_value=target_float,
                        target_unit=self.target_unit,
                        is_eligible=False,
                        exclusion_reason=reason,
                        provenance_details={"missing_feature": missing_name},
                    )
                )
                continue

            # Rule 4: Duplicate Detection (Exact feature + target tuple)
            feat_tuple = tuple(sorted(feature_values.items()))
            sig = f"{feat_tuple}_{target_float}"
            if sig in seen_signatures:
                # Flag as potential duplicate
                reason = "DUPLICATE_RECORD"
                exclusion_summary[reason] = exclusion_summary.get(reason, 0) + 1
                records.append(
                    DatasetRecordItem(
                        experiment_id=exp_id,
                        sample_id=smp_id,
                        analysis_run_id=analysis_run_id,
                        feature_values=feature_values,
                        target_value=target_float,
                        target_unit=self.target_unit,
                        is_eligible=False,
                        exclusion_reason=reason,
                        provenance_details={"duplicate_signature": sig},
                    )
                )
                continue

            seen_signatures.add(sig)

            # Record is ELIGIBLE
            records.append(
                DatasetRecordItem(
                    experiment_id=exp_id,
                    sample_id=smp_id,
                    analysis_run_id=analysis_run_id,
                    feature_values=feature_values,
                    target_value=target_float,
                    target_unit=self.target_unit,
                    is_eligible=True,
                    exclusion_reason=None,
                    provenance_details={
                        "parameter_units": param_units,
                        "property_units": prop_units,
                    },
                )
            )

        eligible_count = sum(1 for r in records if r.is_eligible)
        excluded_count = len(records) - eligible_count

        return DatasetBuildResult(
            dataset_name=dataset_name,
            target_property=self.target_property,
            target_unit=self.target_unit,
            feature_names=self.feature_names,
            records=records,
            eligible_count=eligible_count,
            excluded_count=excluded_count,
            exclusion_summary=exclusion_summary,
            is_synthetic=is_synthetic,
        )
