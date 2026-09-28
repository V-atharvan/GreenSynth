"""
GreenSynth Analytics — Project P7 ML Pipeline Runner
Tests MLDatasetService -> MLTrainingService -> MLPredictionService -> DOE

1. Builds MLDataset for target "Electrical Conductivity" (S/cm) from P7 experiments.
2. Trains candidate regression models (MEAN_BASELINE, LINEAR_REGRESSION, RIDGE, RANDOM_FOREST, GRADIENT_BOOSTING).
3. Evaluates 5-fold cross-validation metrics (R2, RMSE, MAE).
4. Runs test prediction with uncertainty intervals and applicability domain checks.
5. Saves execution summary report to synthetic_data/p7/ml_pipeline_results.json.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, "backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.models.project import Project
from app.models.ml import MLDataset, MLModel, MLPrediction
from app.ml.schemas import (
    MLDatasetCreateInput,
    MLDatasetFeatureSpec,
    MLPredictInput,
    MLTrainingRunCreateInput,
)
from app.ml.services.dataset_service import MLDatasetService
from app.ml.services.prediction_service import MLPredictionService
from app.ml.services.training_service import MLTrainingService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ml_pipeline")

OUTPUT_PATH = Path("synthetic_data/p7/ml_pipeline_results.json")


async def run_pipeline() -> dict[str, Any]:
    logger.info("Initializing ML Pipeline for Project P7...")
    async with AsyncSessionLocal() as session:
        # 1. Fetch Project P7
        proj_res = await session.execute(select(Project).where(Project.project_code == "P7"))
        project = proj_res.scalars().first()
        if not project:
            raise RuntimeError("Project P7 not found!")

        logger.info(f"Loaded Project P7: {project.id}")

        # 2. Define Features and Build ML Dataset
        features = [
            MLDatasetFeatureSpec(
                feature_name="substrate_temperature_c",
                source_parameter="substrate_temperature_c",
                unit="°C",
                data_type="NUMBER",
            ),
            MLDatasetFeatureSpec(
                feature_name="precursor_concentration",
                source_parameter="precursor_concentration",
                unit="mol/L",
                data_type="NUMBER",
            ),
            MLDatasetFeatureSpec(
                feature_name="precursor_solution_volume",
                source_parameter="precursor_solution_volume",
                unit="mL",
                data_type="NUMBER",
            ),
            MLDatasetFeatureSpec(
                feature_name="mulberry_extract_concentration",
                source_parameter="mulberry_extract_concentration",
                unit="g/L",
                data_type="NUMBER",
            ),
            MLDatasetFeatureSpec(
                feature_name="mulberry_extract_volume",
                source_parameter="mulberry_extract_volume",
                unit="mL",
                data_type="NUMBER",
            ),
            MLDatasetFeatureSpec(
                feature_name="ethanol_volume",
                source_parameter="ethanol_volume",
                unit="mL",
                data_type="NUMBER",
            ),
            MLDatasetFeatureSpec(
                feature_name="spray_rate_ml_min",
                source_parameter="spray_rate_ml_min",
                unit="mL/min",
                data_type="NUMBER",
            ),
            MLDatasetFeatureSpec(
                feature_name="spray_duration_min",
                source_parameter="spray_duration_min",
                unit="min",
                data_type="NUMBER",
            ),
            MLDatasetFeatureSpec(
                feature_name="nozzle_substrate_distance_cm",
                source_parameter="nozzle_substrate_distance_cm",
                unit="cm",
                data_type="NUMBER",
            ),
            MLDatasetFeatureSpec(
                feature_name="carrier_gas_pressure_kpa",
                source_parameter="carrier_gas_pressure_kpa",
                unit="kPa",
                data_type="NUMBER",
            ),
            MLDatasetFeatureSpec(
                feature_name="spray_cycles",
                source_parameter="spray_cycles",
                unit="cycles",
                data_type="NUMBER",
            ),
            MLDatasetFeatureSpec(
                feature_name="ambient_temperature_c",
                source_parameter="ambient_temperature_c",
                unit="°C",
                data_type="NUMBER",
            ),
            MLDatasetFeatureSpec(
                feature_name="ambient_relative_humidity",
                source_parameter="ambient_relative_humidity",
                unit="%",
                data_type="NUMBER",
            ),
        ]

        dataset_input = MLDatasetCreateInput(
            project_id=project.id,
            name="P7 CuO Spray Pyrolysis Conductivity Dataset",
            description="Synthetic research dataset for predicting electrical conductivity from 13 spray pyrolysis synthesis parameters.",
            target_property="Electrical Conductivity",
            target_type="CALCULATED",
            target_unit="S/cm",
            features=features,
        )

        dataset_service = MLDatasetService(session)
        logger.info("Building ML Dataset...")
        ml_dataset, quality_indicators = await dataset_service.create_dataset(
            payload=dataset_input, created_by="GreenSynth Synthetic Research Team"
        )
        await session.commit()

        logger.info(
            f"ML Dataset built successfully: {ml_dataset.id} | "
            f"Eligible records: {ml_dataset.eligible_count}, Excluded: {ml_dataset.excluded_count}"
        )

        # 3. Model Training
        training_service = MLTrainingService(session)
        training_input = MLTrainingRunCreateInput(
            dataset_id=ml_dataset.id,
            model_types=[
                "MEAN_BASELINE",
                "LINEAR_REGRESSION",
                "RIDGE",
                "RANDOM_FOREST",
                "GRADIENT_BOOSTING",
            ],
            scaling="STANDARD",
            cv_folds=5,
            random_seed=20260928,
        )

        logger.info("Running candidate model training across 5-fold cross-validation...")
        trained_models = await training_service.run_training(
            payload=training_input, created_by="GreenSynth Synthetic Research Team"
        )
        await session.commit()

        logger.info(f"Trained and registered {len(trained_models)} models.")

        # Rank models by test R2
        model_results = []
        best_model: MLModel | None = None
        best_r2 = -999.0

        for m in trained_models:
            met = m.metrics or {}
            test_r2 = met.get("cv_r2", -999.0)
            res_entry = {
                "model_id": str(m.id),
                "model_name": m.name,
                "model_type": m.model_type,
                "version": m.version,
                "status": m.status,
                "cv_r2": met.get("cv_r2"),
                "cv_rmse": met.get("cv_rmse"),
                "cv_mae": met.get("cv_mae"),
                "train_r2": met.get("train_r2"),
                "is_overfit": met.get("overfitting_warning", False),
            }
            model_results.append(res_entry)
            logger.info(
                f"Model [{m.model_type}]: CV R² = {test_r2:.4f}, "
                f"RMSE = {met.get('cv_rmse', 0):.4f}, MAE = {met.get('cv_mae', 0):.4f}"
            )

            if test_r2 > best_r2:
                best_r2 = test_r2
                best_model = m

        logger.info(f"Champion Model: {best_model.model_type} (R² = {best_r2:.4f})")

        # 4. Prediction Execution Test
        prediction_service = MLPredictionService(session)

        # Test point near optimal center-point
        test_condition = {
            "substrate_temperature_c": 370.0,
            "precursor_concentration": 0.22,
            "precursor_solution_volume": 80.0,
            "mulberry_extract_concentration": 16.0,
            "mulberry_extract_volume": 20.0,
            "ethanol_volume": 150.0,
            "spray_rate_ml_min": 4.2,
            "spray_duration_min": 25.0,
            "nozzle_substrate_distance_cm": 20.0,
            "carrier_gas_pressure_kpa": 210.0,
            "spray_cycles": 20,
            "ambient_temperature_c": 24.5,
            "ambient_relative_humidity": 45.0,
        }

        predict_input = MLPredictInput(
            input_parameters=test_condition,
            notes="Optimal central composite test synthesis condition",
        )

        logger.info(f"Generating prediction with champion model {best_model.id}...")
        pred_record = await prediction_service.predict(
            model_id=best_model.id,
            payload=predict_input,
            created_by="GreenSynth Synthetic Research Team",
        )
        await session.commit()

        logger.info(
            f"Prediction Result: {pred_record.predicted_value:.4f} S/cm | "
            f"95% CI: [{pred_record.uncertainty_lower:.4f}, {pred_record.uncertainty_upper:.4f}] S/cm | "
            f"Applicability: {pred_record.applicability_status}"
        )

        pipeline_summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "COMPLETED",
            "project_code": "P7",
            "dataset": {
                "id": str(ml_dataset.id),
                "name": ml_dataset.name,
                "target_property": ml_dataset.target_property,
                "target_unit": ml_dataset.target_unit,
                "eligible_count": ml_dataset.eligible_count,
                "excluded_count": ml_dataset.excluded_count,
                "is_synthetic": ml_dataset.is_synthetic,
            },
            "models_trained": model_results,
            "champion_model": {
                "id": str(best_model.id),
                "model_type": best_model.model_type,
                "cv_r2": best_r2,
            },
            "test_prediction": {
                "input_features": test_condition,
                "predicted_conductivity_s_cm": pred_record.predicted_value,
                "ci_lower": pred_record.uncertainty_lower,
                "ci_upper": pred_record.uncertainty_upper,
                "applicability_status": pred_record.applicability_status,
            },
        }

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(pipeline_summary, f, indent=2)

        logger.info(f"ML Pipeline results saved to {OUTPUT_PATH}")
        return pipeline_summary


if __name__ == "__main__":
    asyncio.run(run_pipeline())
