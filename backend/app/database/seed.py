"""
GreenSynth Analytics — Database Seed Data (Phase 19 Multi-Project Platform)

Seeds Catalogs (Materials, Biomass, PlantExtracts, Solvents, SynthesisMethods) and
all eight laboratory project configurations (P1 through P8).

IMPORTANT:
  - Contains ONLY configuration templates (parameter definitions, units, types, ranges).
  - Contains ZERO fabricated experimental values or measurements.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus
from app.models.parameter import ParameterDefinition, ParameterDataType, ParameterStatus
from app.models.project_config import (
    MaterialCatalog,
    BiomassCatalog,
    ExtractCatalog,
    SolventCatalog,
    SynthesisMethodCatalog,
    ProjectDefinition,
)
from app.models.optimization import OptimizationObjective
from app.models.doe import Objective

logger = logging.getLogger(__name__)

ALL_PROJECT_SPECS = [
    {
        "code": "P1",
        "name": "CuO Phytochemical Synthesis via Sol-Gel (Ethanol)",
        "desc": "Project 1: Sol-gel green synthesis of CuO semiconductors using mulberry extract in ethanol.",
        "material": "CuO",
        "extract": "Mulberry",
        "solvent": "Ethanol",
        "method": "Sol-gel",
        "biomass": None,
    },
    {
        "code": "P2",
        "name": "CuO Phytochemical Synthesis via Sol-Gel (Acetone)",
        "desc": "Project 2: Sol-gel green synthesis of CuO semiconductors using mulberry extract in acetone.",
        "material": "CuO",
        "extract": "Mulberry",
        "solvent": "Acetone",
        "method": "Sol-gel",
        "biomass": None,
    },
    {
        "code": "P3",
        "name": "CuO Phytochemical Synthesis via Hydrothermal (Ethanol)",
        "desc": "Project 3: Hydrothermal green synthesis of CuO nanostructures using mulberry extract in ethanol.",
        "material": "CuO",
        "extract": "Mulberry",
        "solvent": "Ethanol",
        "method": "Hydrothermal",
        "biomass": None,
    },
    {
        "code": "P4",
        "name": "CuO Phytochemical Synthesis via Hydrothermal (Acetone)",
        "desc": "Project 4: Hydrothermal green synthesis of CuO nanostructures using mulberry extract in acetone.",
        "material": "CuO",
        "extract": "Mulberry",
        "solvent": "Acetone",
        "method": "Hydrothermal",
        "biomass": None,
    },
    {
        "code": "P5",
        "name": "Biomass-Derived Silica/Silicon Hydrothermal Synthesis (Ethanol)",
        "desc": "Project 5: Rice-husk-derived Silica/Silicon hydrothermal synthesis assisted by mulberry extract in ethanol.",
        "material": "Silica / Silicon",
        "extract": "Mulberry",
        "solvent": "Ethanol",
        "method": "Hydrothermal",
        "biomass": "Rice husk",
    },
    {
        "code": "P6",
        "name": "Biomass-Derived Silica/Silicon Hydrothermal Synthesis (Acetone)",
        "desc": "Project 6: Rice-husk-derived Silica/Silicon hydrothermal synthesis assisted by mulberry extract in acetone.",
        "material": "Silica / Silicon",
        "extract": "Mulberry",
        "solvent": "Acetone",
        "method": "Hydrothermal",
        "biomass": "Rice husk",
    },
    {
        "code": "P7",
        "name": "Phytochemical synthesis of semiconducting copper oxide using mulberry extract in ethanol by spray pyrolysis",
        "desc": "Project 7: Green synthesis of CuO semiconductor thin films using mulberry leaf extract, ethanol solvent, and spray pyrolysis. Primary MVP project.",
        "material": "CuO",
        "extract": "Mulberry",
        "solvent": "Ethanol",
        "method": "Spray Pyrolysis",
        "biomass": None,
    },
    {
        "code": "P8",
        "name": "CuO Phytochemical Synthesis via Spray Pyrolysis (Acetone)",
        "desc": "Project 8: Green synthesis of CuO semiconductor thin films using mulberry extract in acetone solvent by spray pyrolysis.",
        "material": "CuO",
        "extract": "Mulberry",
        "solvent": "Acetone",
        "method": "Spray Pyrolysis",
        "biomass": None,
    },
]

PROJECT_SPRAY_PYROLYSIS_PARAMETERS = [
    {
        "parameter_code": "copper_precursor_salt",
        "parameter_name": "Copper Precursor Salt",
        "description": "Precursor chemical compound used for Cu ions (e.g. Copper acetate monohydrate)",
        "data_type": ParameterDataType.TEXT.value,
        "unit": None,
        "required": True,
        "minimum_value": None,
        "maximum_value": None,
        "allowed_values": None,
    },
    {
        "parameter_code": "precursor_concentration",
        "parameter_name": "Precursor Concentration",
        "description": "Molar concentration of precursor solution",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mol/L",
        "required": True,
        "minimum_value": 0.001,
        "maximum_value": 2.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "precursor_solution_volume",
        "parameter_name": "Precursor Solution Volume",
        "description": "Volume of precursor solution mixed",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mL",
        "required": True,
        "minimum_value": 1.0,
        "maximum_value": 500.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "mulberry_extract_concentration",
        "parameter_name": "Mulberry Extract Concentration",
        "description": "Concentration of plant extract reducing/capping agent",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "g/L",
        "required": True,
        "minimum_value": 0.1,
        "maximum_value": 100.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "mulberry_extract_volume",
        "parameter_name": "Mulberry Extract Volume",
        "description": "Volume of mulberry extract added",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mL",
        "required": True,
        "minimum_value": 0.1,
        "maximum_value": 100.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "ethanol_volume",
        "parameter_name": "Ethanol Volume",
        "description": "Volume of ethanol or solvent added to spray solution",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mL",
        "required": True,
        "minimum_value": 1.0,
        "maximum_value": 500.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "substrate_type",
        "parameter_name": "Substrate Type",
        "description": "Material type of substrate receiving spray deposition",
        "data_type": ParameterDataType.ENUM.value,
        "unit": None,
        "required": True,
        "minimum_value": None,
        "maximum_value": None,
        "allowed_values": ["Glass", "FTO Glass", "ITO Glass", "Quartz", "Silicon"],
    },
    {
        "parameter_code": "substrate_temperature_c",
        "parameter_name": "Substrate Temperature",
        "description": "Substrate temperature during spray deposition",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "°C",
        "required": True,
        "minimum_value": 100.0,
        "maximum_value": 600.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "spray_rate_ml_min",
        "parameter_name": "Spray Rate",
        "description": "Volumetric liquid spray delivery rate",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mL/min",
        "required": True,
        "minimum_value": 0.1,
        "maximum_value": 20.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "spray_duration_min",
        "parameter_name": "Spray Duration",
        "description": "Total active deposition spray duration",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "min",
        "required": True,
        "minimum_value": 0.5,
        "maximum_value": 120.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "nozzle_substrate_distance_cm",
        "parameter_name": "Nozzle-to-Substrate Distance",
        "description": "Vertical distance between spray nozzle tip and substrate surface",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "cm",
        "required": True,
        "minimum_value": 5.0,
        "maximum_value": 50.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "carrier_gas_pressure_kpa",
        "parameter_name": "Carrier Gas Pressure",
        "description": "Pneumatic atomizer carrier gas line pressure",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "kPa",
        "required": True,
        "minimum_value": 10.0,
        "maximum_value": 500.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "spray_cycles",
        "parameter_name": "Number of Spray Cycles",
        "description": "Number of discrete spray-pause deposition cycles",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "cycles",
        "required": True,
        "minimum_value": 1.0,
        "maximum_value": 100.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "ambient_temperature_c",
        "parameter_name": "Ambient Temperature",
        "description": "Laboratory ambient temperature during spray deposition",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "°C",
        "required": True,
        "minimum_value": 15.0,
        "maximum_value": 40.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "ambient_relative_humidity",
        "parameter_name": "Ambient Relative Humidity",
        "description": "Laboratory ambient relative humidity percentage",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "%",
        "required": True,
        "minimum_value": 10.0,
        "maximum_value": 95.0,
        "allowed_values": None,
    },
]

PROJECT_SOL_GEL_PARAMETERS = [
    {
        "parameter_code": "copper_precursor_salt",
        "parameter_name": "Copper Precursor Salt",
        "description": "Precursor salt for sol-gel preparation",
        "data_type": ParameterDataType.TEXT.value,
        "unit": None,
        "required": True,
        "minimum_value": None,
        "maximum_value": None,
        "allowed_values": None,
    },
    {
        "parameter_code": "precursor_concentration",
        "parameter_name": "Precursor Concentration",
        "description": "Molar concentration of precursor sol",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mol/L",
        "required": True,
        "minimum_value": 0.001,
        "maximum_value": 2.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "precursor_solution_volume",
        "parameter_name": "Precursor Solution Volume",
        "description": "Volume of precursor solution",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mL",
        "required": True,
        "minimum_value": 1.0,
        "maximum_value": 500.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "mulberry_extract_concentration",
        "parameter_name": "Mulberry Extract Concentration",
        "description": "Concentration of plant extract",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "g/L",
        "required": True,
        "minimum_value": 0.1,
        "maximum_value": 100.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "mulberry_extract_volume",
        "parameter_name": "Mulberry Extract Volume",
        "description": "Volume of extract added to sol",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mL",
        "required": True,
        "minimum_value": 0.1,
        "maximum_value": 100.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "solvent_volume",
        "parameter_name": "Solvent Volume",
        "description": "Solvent volume used in sol-gel mix",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mL",
        "required": True,
        "minimum_value": 1.0,
        "maximum_value": 500.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "sol_gel_aging_temperature_c",
        "parameter_name": "Sol-Gel Aging Temperature",
        "description": "Temperature during sol aging/gelation",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "°C",
        "required": False,
        "minimum_value": 20.0,
        "maximum_value": 100.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "sol_gel_aging_time_h",
        "parameter_name": "Sol-Gel Aging Time",
        "description": "Sol aging duration prior to drying",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "h",
        "required": False,
        "minimum_value": 1.0,
        "maximum_value": 72.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "calcination_temperature_c",
        "parameter_name": "Calcination Temperature",
        "description": "Thermal anneal/calcination temperature",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "°C",
        "required": False,
        "minimum_value": 200.0,
        "maximum_value": 800.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "calcination_duration_h",
        "parameter_name": "Calcination Duration",
        "description": "Duration at peak calcination temperature",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "h",
        "required": False,
        "minimum_value": 0.5,
        "maximum_value": 12.0,
        "allowed_values": None,
    },
]

PROJECT_HYDROTHERMAL_PARAMETERS = [
    {
        "parameter_code": "copper_precursor_salt",
        "parameter_name": "Copper Precursor Salt",
        "description": "Precursor salt used in hydrothermal synthesis",
        "data_type": ParameterDataType.TEXT.value,
        "unit": None,
        "required": True,
        "minimum_value": None,
        "maximum_value": None,
        "allowed_values": None,
    },
    {
        "parameter_code": "precursor_concentration",
        "parameter_name": "Precursor Concentration",
        "description": "Molar concentration of precursor solution",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mol/L",
        "required": True,
        "minimum_value": 0.001,
        "maximum_value": 2.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "precursor_solution_volume",
        "parameter_name": "Precursor Solution Volume",
        "description": "Volume of precursor solution",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mL",
        "required": True,
        "minimum_value": 1.0,
        "maximum_value": 500.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "mulberry_extract_concentration",
        "parameter_name": "Mulberry Extract Concentration",
        "description": "Concentration of plant extract",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "g/L",
        "required": True,
        "minimum_value": 0.1,
        "maximum_value": 100.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "mulberry_extract_volume",
        "parameter_name": "Mulberry Extract Volume",
        "description": "Volume of mulberry extract",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mL",
        "required": True,
        "minimum_value": 0.1,
        "maximum_value": 100.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "solvent_volume",
        "parameter_name": "Solvent Volume",
        "description": "Solvent volume in reaction mixture",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mL",
        "required": True,
        "minimum_value": 1.0,
        "maximum_value": 500.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "autoclave_fill_factor_pct",
        "parameter_name": "Autoclave Fill Factor",
        "description": "Percentage of Teflon vessel volume occupied by solution",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "%",
        "required": False,
        "minimum_value": 30.0,
        "maximum_value": 85.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "hydrothermal_temperature_c",
        "parameter_name": "Hydrothermal Temperature",
        "description": "Autoclave reaction temperature",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "°C",
        "required": False,
        "minimum_value": 100.0,
        "maximum_value": 250.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "hydrothermal_reaction_time_h",
        "parameter_name": "Hydrothermal Reaction Time",
        "description": "Reaction duration inside autoclave",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "h",
        "required": False,
        "minimum_value": 1.0,
        "maximum_value": 48.0,
        "allowed_values": None,
    },
]

PROJECT_BIOMASS_SILICA_PARAMETERS = [
    {
        "parameter_code": "biomass_source_mass_g",
        "parameter_name": "Biomass Source Mass (Rice Husk)",
        "description": "Mass of raw agricultural rice husk biomass",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "g",
        "required": True,
        "minimum_value": 1.0,
        "maximum_value": 500.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "mulberry_extract_concentration",
        "parameter_name": "Mulberry Extract Concentration",
        "description": "Concentration of plant extract",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "g/L",
        "required": True,
        "minimum_value": 0.1,
        "maximum_value": 100.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "mulberry_extract_volume",
        "parameter_name": "Mulberry Extract Volume",
        "description": "Volume of plant extract",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mL",
        "required": True,
        "minimum_value": 0.1,
        "maximum_value": 100.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "solvent_volume",
        "parameter_name": "Solvent Volume",
        "description": "Volume of solvent added",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mL",
        "required": True,
        "minimum_value": 1.0,
        "maximum_value": 500.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "pretreatment_acid_concentration",
        "parameter_name": "Pretreatment Acid Concentration",
        "description": "Acid leaching solution concentration",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "mol/L",
        "required": False,
        "minimum_value": 0.1,
        "maximum_value": 5.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "hydrothermal_temperature_c",
        "parameter_name": "Hydrothermal Temperature",
        "description": "Hydrothermal reaction temperature",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "°C",
        "required": False,
        "minimum_value": 100.0,
        "maximum_value": 250.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "hydrothermal_reaction_time_h",
        "parameter_name": "Hydrothermal Reaction Time",
        "description": "Hydrothermal digestion duration",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "h",
        "required": False,
        "minimum_value": 1.0,
        "maximum_value": 48.0,
        "allowed_values": None,
    },
    {
        "parameter_code": "calcination_temperature_c",
        "parameter_name": "Calcination Temperature",
        "description": "Thermal treatment temperature to produce silica/silicon",
        "data_type": ParameterDataType.NUMBER.value,
        "unit": "°C",
        "required": False,
        "minimum_value": 400.0,
        "maximum_value": 1000.0,
        "allowed_values": None,
    },
]


async def seed_catalogs(db: AsyncSession) -> None:
    """Seed Domain Catalogs: Materials, Biomass, Extracts, Solvents, Methods."""

    # 1. Materials
    mats = [
        {"code": "CUO", "name": "Copper Oxide (CuO)", "formula": "CuO", "type": "SINGLE_MATERIAL"},
        {"code": "SILICA_SILICON", "name": "Silica / Silicon", "formula": "SiO2 / Si", "type": "BIOMASS_DERIVED"},
    ]
    for m in mats:
        res = await db.execute(select(MaterialCatalog).where(MaterialCatalog.material_code == m["code"]))
        if res.scalar_one_or_none() is None:
            db.add(MaterialCatalog(material_code=m["code"], name=m["name"], chemical_formula=m["formula"], material_type=m["type"]))

    # 2. Biomass
    bio = [{"code": "RICE_HUSK", "name": "Rice Husk", "source": "Agricultural Waste"}]
    for b in bio:
        res = await db.execute(select(BiomassCatalog).where(BiomassCatalog.biomass_code == b["code"]))
        if res.scalar_one_or_none() is None:
            db.add(BiomassCatalog(biomass_code=b["code"], name=b["name"], source=b["source"]))

    # 3. Extracts
    exts = [{"code": "MULBERRY", "name": "Mulberry Extract", "source": "Morus alba leaves"}]
    for e in exts:
        res = await db.execute(select(ExtractCatalog).where(ExtractCatalog.extract_code == e["code"]))
        if res.scalar_one_or_none() is None:
            db.add(ExtractCatalog(extract_code=e["code"], name=e["name"], source_plant=e["source"]))

    # 4. Solvents
    solvs = [
        {"code": "ETHANOL", "name": "Ethanol", "formula": "C2H5OH"},
        {"code": "ACETONE", "name": "Acetone", "formula": "C3H6O"},
    ]
    for s in solvs:
        res = await db.execute(select(SolventCatalog).where(SolventCatalog.solvent_code == s["code"]))
        if res.scalar_one_or_none() is None:
            db.add(SolventCatalog(solvent_code=s["code"], name=s["name"], chemical_formula=s["formula"]))

    # 5. Synthesis Methods
    meths = [
        {"code": "SOL_GEL", "name": "Sol-Gel Synthesis"},
        {"code": "HYDROTHERMAL", "name": "Hydrothermal Synthesis"},
        {"code": "SPRAY_PYROLYSIS", "name": "Spray Pyrolysis Synthesis"},
    ]
    for m in meths:
        res = await db.execute(select(SynthesisMethodCatalog).where(SynthesisMethodCatalog.method_code == m["code"]))
        if res.scalar_one_or_none() is None:
            db.add(SynthesisMethodCatalog(method_code=m["code"], name=m["name"]))

    await db.flush()


async def seed_demo_project(db: AsyncSession) -> None:
    """
    Seed all eight projects (P1 through P8) and their method-specific parameter schemas.
    """
    await seed_catalogs(db)

    for spec in ALL_PROJECT_SPECS:
        res = await db.execute(select(Project).where(Project.project_code == spec["code"]))
        proj = res.scalar_one_or_none()

        if proj is None:
            proj = Project(
                project_code=spec["code"],
                name=spec["name"],
                description=spec["desc"],
                material=spec["material"],
                extract=spec["extract"],
                solvent=spec["solvent"],
                synthesis_method=spec["method"],
                status=ProjectStatus.ACTIVE,
            )
            db.add(proj)
            await db.flush()
            await db.refresh(proj)
            logger.info("Created Project %s.", spec["code"])

        # Seed ProjectDefinition link
        pdef_res = await db.execute(select(ProjectDefinition).where(ProjectDefinition.project_id == proj.id))
        if pdef_res.scalar_one_or_none() is None:
            pdef = ProjectDefinition(
                project_id=proj.id,
                project_code=spec["code"],
                material_system_type="BIOMASS_DERIVED" if spec["biomass"] else "SINGLE_MATERIAL",
                characterization_capabilities={"XRD": True, "UV_Vis": True, "Electrical": True, "FTIR": True, "SEM": True},
                analysis_capabilities={"PeakDetection": True, "TaucPlot": True, "ConductivityFit": True},
                optimization_capabilities={"GridSearch": True, "RandomSearch": True, "ModelGuided": True},
            )
            db.add(pdef)

        # Select parameter schema based on project code / methodology
        p_code = spec["code"]
        if p_code in ("P7", "P8"):
            target_params = PROJECT_SPRAY_PYROLYSIS_PARAMETERS
        elif p_code in ("P1", "P2"):
            target_params = PROJECT_SOL_GEL_PARAMETERS
        elif p_code in ("P3", "P4"):
            target_params = PROJECT_HYDROTHERMAL_PARAMETERS
        elif p_code in ("P5", "P6"):
            target_params = PROJECT_BIOMASS_SILICA_PARAMETERS
        else:
            target_params = PROJECT_SPRAY_PYROLYSIS_PARAMETERS

        # Fetch existing parameter codes for this project
        param_res = await db.execute(
            select(ParameterDefinition.parameter_code).where(ParameterDefinition.project_id == proj.id)
        )
        existing_codes = set(param_res.scalars().all())

        for p_spec in target_params:
            if p_spec["parameter_code"] not in existing_codes:
                db.add(
                    ParameterDefinition(
                        project_id=proj.id,
                        parameter_code=p_spec["parameter_code"],
                        parameter_name=p_spec["parameter_name"],
                        description=p_spec["description"],
                        data_type=p_spec["data_type"],
                        unit=p_spec["unit"],
                        required=p_spec["required"],
                        minimum_value=p_spec["minimum_value"],
                        maximum_value=p_spec["maximum_value"],
                        allowed_values=p_spec["allowed_values"],
                        status=ParameterStatus.ACTIVE.value,
                    )
                )

        # Seed default DOE Objective
        d_obj_res = await db.execute(select(Objective).where(Objective.project_id == proj.id))
        if len(d_obj_res.scalars().all()) == 0:
            db.add(
                Objective(
                    project_id=proj.id,
                    name="Maximize Electrical Conductivity",
                    version="v1",
                    description="Optimize precursor and spray parameters to maximize electrical conductivity (S/cm)",
                    target_property="Electrical Conductivity",
                    direction="MAXIMIZE",
                    weight=1.0,
                    unit="S/cm",
                    status="ACTIVE",
                )
            )

        # Seed default OptimizationObjective
        opt_obj_res = await db.execute(
            select(OptimizationObjective).where(OptimizationObjective.project_id == proj.id)
        )
        if len(opt_obj_res.scalars().all()) == 0:
            db.add(
                OptimizationObjective(
                    project_id=proj.id,
                    name="Maximize Electrical Conductivity",
                    description="Optimize precursor and spray parameters to maximize electrical conductivity (S/cm)",
                    target_property="Electrical Conductivity",
                    direction="MAXIMIZE",
                    weight=1.0,
                    unit="S/cm",
                    status="ACTIVE",
                )
            )

    await db.commit()
    logger.info("Seeded project definitions (P1-P8) and optimization objectives.")
