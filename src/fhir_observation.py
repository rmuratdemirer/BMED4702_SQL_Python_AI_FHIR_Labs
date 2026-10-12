from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .db import read_only_connection
from .lab_creatinine import PARAMETERS
from .provenance import sha256


FHIR_VERSION = "4.0.1"
TIME_EXTENSION = "urn:bmed4702:source-timezone-assumption"
SOURCE_TIME_EXTENSION = "urn:bmed4702:source-local-datetime"
MIMIC_BASE = "https://physionet.org/content/mimic-iv-demo/2.2"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _fhir_datetime(source: str, offset: str) -> str:
    if offset != "Z" and not re.fullmatch(r"[+-](?:0\d|1\d|2[0-3]):[0-5]\d", offset):
        raise ValueError("timezone_offset must be Z or an offset such as +03:00")
    return source.replace(" ", "T") + offset


def _entry(resource: dict[str, Any]) -> dict[str, Any]:
    return {
        "fullUrl": f"urn:bmed4702:{resource['resourceType'].lower()}:{resource['id']}",
        "resource": resource,
    }


def observation_from_row(row: dict[str, Any], timezone_offset: str) -> dict[str, Any]:
    observation_id = f"mimic-lab-{row['labevent_id']}"
    coding = [
        {
            "system": "http://loinc.org",
            "code": "38483-4",
            "display": "Creatinine [Mass/volume] in Blood",
        },
        {
            "system": f"{MIMIC_BASE}/CodeSystem/d-labitems",
            "code": str(row["itemid"]),
            "display": row["label"],
        },
    ]
    resource: dict[str, Any] = {
        "resourceType": "Observation",
        "id": observation_id,
        "meta": {
            "source": f"{MIMIC_BASE}/",
            "tag": [{
                "system": "urn:bmed4702:dataset",
                "code": "mimic-iv-demo-2.2",
                "display": "MIMIC-IV Clinical Database Demo v2.2",
            }],
        },
        "extension": [
            {"url": TIME_EXTENSION, "valueString": timezone_offset},
            {"url": SOURCE_TIME_EXTENSION, "valueString": row["charttime"]},
        ],
        "identifier": [{
            "system": f"{MIMIC_BASE}/identifier/labevent-id",
            "value": str(row["labevent_id"]),
        }],
        "status": "unknown",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory",
                "display": "Laboratory",
            }],
        }],
        "code": {"coding": coding, "text": row["label"]},
        "subject": {"reference": f"Patient/mimic-subject-{row['subject_id']}"},
        "encounter": {"reference": f"Encounter/mimic-admission-{row['hadm_id']}"},
        "effectiveDateTime": _fhir_datetime(row["charttime"], timezone_offset),
        "valueQuantity": {
            "value": float(row["valuenum"]),
            "unit": row["valueuom"],
            "system": "http://unitsofmeasure.org",
            "code": "mg/dL",
        },
        "specimen": {
            "identifier": {
                "system": f"{MIMIC_BASE}/identifier/specimen-id",
                "value": str(row["specimen_id"]),
            }
        },
    }
    if row.get("storetime"):
        resource["issued"] = _fhir_datetime(row["storetime"], timezone_offset)
        resource["extension"].append({
            "url": SOURCE_TIME_EXTENSION + "/storetime",
            "valueString": row["storetime"],
        })
    if row.get("ref_range_lower") is not None or row.get("ref_range_upper") is not None:
        reference_range: dict[str, Any] = {}
        for key, fhir_key in (("ref_range_lower", "low"), ("ref_range_upper", "high")):
            if row.get(key) is not None:
                reference_range[fhir_key] = {
                    "value": float(row[key]), "unit": row["valueuom"],
                    "system": "http://unitsofmeasure.org", "code": "mg/dL",
                }
        resource["referenceRange"] = [reference_range]
    if row.get("flag") == "abnormal":
        resource["interpretation"] = [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": "A",
                "display": "Abnormal",
            }],
            "text": "Source flag: abnormal",
        }]
    if row.get("priority"):
        resource["note"] = [{"text": f"MIMIC-IV source priority: {row['priority']}"}]
    return resource


def validate_bundle(bundle: dict[str, Any], expected_observations: int) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if bundle.get("resourceType") != "Bundle" or bundle.get("type") != "collection":
        errors.append("Root must be a FHIR collection Bundle")
    resources = [entry.get("resource", {}) for entry in bundle.get("entry", [])]
    observations = [r for r in resources if r.get("resourceType") == "Observation"]
    if len(observations) != expected_observations:
        errors.append(f"Expected {expected_observations} Observations, found {len(observations)}")
    ids: set[str] = set()
    for index, obs in enumerate(observations):
        prefix = f"Observation[{index}]"
        if obs.get("status") not in {"registered", "preliminary", "final", "amended", "corrected", "cancelled", "entered-in-error", "unknown"}:
            errors.append(prefix + " has an invalid status")
        if obs.get("id") in ids:
            errors.append(prefix + " has a duplicate id")
        ids.add(obs.get("id", ""))
        coding = obs.get("code", {}).get("coding", [])
        if not any(c.get("system") == "http://loinc.org" and c.get("code") == "38483-4" for c in coding):
            errors.append(prefix + " lacks the expected blood creatinine LOINC coding")
        quantity = obs.get("valueQuantity", {})
        if quantity.get("system") != "http://unitsofmeasure.org" or quantity.get("code") != "mg/dL":
            errors.append(prefix + " lacks UCUM mg/dL coding")
        if not obs.get("subject", {}).get("reference") or not obs.get("encounter", {}).get("reference"):
            errors.append(prefix + " lacks subject or encounter context")
        for key in ("effectiveDateTime", "issued"):
            value = obs.get(key)
            if value and not re.search(r"(?:Z|[+-]\d{2}:\d{2})$", value):
                errors.append(prefix + f" {key} lacks an explicit timezone offset")
    if any(obs.get("status") == "unknown" for obs in observations):
        warnings.append("Observation.status is unknown because the source table does not provide a FHIR result status")
    warnings.append("The source timestamps have no timezone; the selected offset is an explicit teaching assumption")
    return {
        "fhir_version": FHIR_VERSION,
        "valid_for_lab_contract": not errors,
        "observation_count": len(observations),
        "errors": errors,
        "warnings": warnings,
    }


def build_bundle(database: Path, project_root: Path, timezone_offset: str = "+00:00") -> dict[str, Any]:
    query_path = project_root / "sql" / "02_creatinine_timeline.sql"
    query = query_path.read_text(encoding="utf-8")
    with read_only_connection(database) as con:
        rows = [dict(row) for row in con.execute(query, PARAMETERS).fetchall()]
        encounter = dict(con.execute(
            "SELECT subject_id, hadm_id, admittime, dischtime, admission_type "
            "FROM admissions WHERE hadm_id = ?", (PARAMETERS["hadm_id"],)
        ).fetchone())
    patient_id = f"mimic-subject-{PARAMETERS['subject_id']}"
    encounter_id = f"mimic-admission-{PARAMETERS['hadm_id']}"
    device_id = "bmed4702-mimic-fhir-converter"
    patient = {
        "resourceType": "Patient", "id": patient_id,
        "identifier": [{
            "system": f"{MIMIC_BASE}/identifier/subject-id",
            "value": str(PARAMETERS["subject_id"]),
        }],
    }
    encounter_resource = {
        "resourceType": "Encounter", "id": encounter_id, "status": "finished",
        "class": {
            "system": f"{MIMIC_BASE}/CodeSystem/admission-type",
            "code": encounter["admission_type"],
            "display": encounter["admission_type"],
        },
        "identifier": [{
            "system": f"{MIMIC_BASE}/identifier/hadm-id",
            "value": str(PARAMETERS["hadm_id"]),
        }],
        "subject": {"reference": f"Patient/{patient_id}"},
        "period": {
            "start": _fhir_datetime(encounter["admittime"], timezone_offset),
            "end": _fhir_datetime(encounter["dischtime"], timezone_offset),
        },
    }
    device = {
        "resourceType": "Device", "id": device_id, "status": "active",
        "deviceName": [{"name": "BMED4702 MIMIC to FHIR converter", "type": "user-friendly-name"}],
        "version": [{"value": "1.0"}],
    }
    observations = [observation_from_row(row, timezone_offset) for row in rows]
    provenance = {
        "resourceType": "Provenance", "id": "mimic-creatinine-transform",
        "target": [{"reference": f"Observation/{obs['id']}"} for obs in observations],
        "occurredPeriod": {
            "start": observations[0]["effectiveDateTime"],
            "end": observations[-1].get("issued", observations[-1]["effectiveDateTime"]),
        },
        "recorded": _now(),
        "activity": {"text": "MIMIC-IV Demo row to FHIR R4 Observation transformation"},
        "agent": [{
            "type": {"text": "assembler"},
            "who": {"reference": f"Device/{device_id}"},
        }],
        "entity": [{
            "role": "source",
            "what": {
                "identifier": {
                    "system": "urn:bmed4702:sha256",
                    "value": sha256(database),
                },
                "display": "Prepared MIMIC-IV Demo v2.2 SQLite teaching database",
            },
        }],
    }
    return {
        "resourceType": "Bundle",
        "id": "bmed4702-creatinine-observations",
        "type": "collection",
        "timestamp": _now(),
        "entry": [_entry(patient), _entry(encounter_resource), _entry(device)]
        + [_entry(obs) for obs in observations] + [_entry(provenance)],
    }


MAPPING_ROWS = [
    ("labevents.labevent_id", "Observation.identifier", "Preserve source event identity"),
    ("labevents.subject_id", "Observation.subject", "Reference a minimal deidentified Patient"),
    ("labevents.hadm_id", "Observation.encounter", "Reference the admission context"),
    ("labevents.itemid + d_labitems", "Observation.code", "Use local coding plus LOINC 38483-4 for Blood creatinine"),
    ("labevents.charttime", "Observation.effectiveDateTime", "Clinical event time; attach explicit offset assumption"),
    ("labevents.storetime", "Observation.issued", "Availability time; attach explicit offset assumption"),
    ("labevents.valuenum", "Observation.valueQuantity.value", "Numeric result"),
    ("labevents.valueuom", "Observation.valueQuantity", "Map mg/dL to UCUM without conversion"),
    ("ref_range_lower/upper", "Observation.referenceRange", "Preserve source interval"),
    ("flag=abnormal", "Observation.interpretation", "Map source abnormal flag to v3 code A"),
    ("source lacks result status", "Observation.status=unknown", "Do not invent finality"),
    ("database/query/software", "Provenance", "Record source hash and transformation agent"),
]


def write_outputs(database: Path, project_root: Path, timezone_offset: str = "+00:00") -> dict[str, Any]:
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = build_bundle(database, project_root, timezone_offset)
    bundle_path = output_dir / "fhir_creatinine_bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    observations = [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Observation"]
    (output_dir / "fhir_observation_example.json").write_text(
        json.dumps(observations[0], indent=2), encoding="utf-8"
    )
    with (output_dir / "fhir_mapping_report.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["source", "fhir_target", "mapping_policy"])
        writer.writerows(MAPPING_ROWS)
    report = validate_bundle(bundle, expected_observations=36)
    (output_dir / "fhir_validation_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report
