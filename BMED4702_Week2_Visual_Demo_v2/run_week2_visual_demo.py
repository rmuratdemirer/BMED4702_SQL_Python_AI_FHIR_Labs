"""BMED4702 Week 2 visual classroom demo: MIMIC-IV -> FHIR Observation.

Run this file (not src/db.py) from PyCharm.  It prints every teaching step,
saves evidence under output/week2_visual_demo, and opens three plot windows.
The SQLite database is opened read-only. If it is not found, a transparent
built-in teaching row is used so the lesson still runs.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import matplotlib.pyplot as plt
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Missing package. In the PyCharm Terminal run:\n"
        r".\.venv\Scripts\python.exe -m pip install pandas matplotlib"
    ) from exc


UCUM = {
    "mg/dL": "mg/dL",
    "mmol/L": "mmol/L",
    "umol/L": "umol/L",
    "µmol/L": "umol/L",
}

SAMPLE_ROW = {
    "labevent_id": 1001,
    "subject_id": 10000032,
    "hadm_id": None,
    "itemid": 50912,
    "label": "Creatinine",
    "fluid": "Blood",
    "charttime": "2180-03-23 11:51:00",
    "storetime": "2180-03-23 12:18:00",
    "valuenum": 2.1,
    "valueuom": "mg/dL",
    "flag": "abnormal",
}


def banner(number: int, title: str, slide: str) -> None:
    print("\n" + "=" * 78)
    print(f"DEMO {number}: {title}  |  Related slides: {slide}")
    print("=" * 78)


def locate_project_root() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents[:5]]:
        if (candidate / "data").is_dir() or any(candidate.glob("*.sqlite")):
            return candidate
    return here


def locate_database(root: Path) -> Path | None:
    candidates = [
        root / "data" / "mimic_demo.sqlite",
        root / "output" / "mimic_demo.sqlite",
        root / "mimic_demo.sqlite",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    found = list(root.rglob("mimic_demo.sqlite"))
    return found[0] if found else None


def connect_read_only(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def get_source_rows(database: Path | None) -> pd.DataFrame:
    if database is None:
        return pd.DataFrame([SAMPLE_ROW])
    query = (Path(__file__).parent / "sql" / "01_creatinine_source_rows.sql").read_text(
        encoding="utf-8"
    )
    with connect_read_only(database) as connection:
        frame = pd.read_sql_query(query, connection)
    return frame if not frame.empty else pd.DataFrame([SAMPLE_ROW])


def source_identifier(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "system": "urn:physionet:mimic-iv:labevents",
        "value": str(row["labevent_id"]),
    }


def to_fhir_observation(row: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Conservative mapping: preserve evidence; never invent certainty."""
    warnings: list[str] = []
    obs: dict[str, Any] = {
        "resourceType": "Observation",
        "id": f"mimic-lab-{row['labevent_id']}",
        "status": "unknown",  # MIMIC row does not establish a FHIR final status.
        "identifier": [source_identifier(row)],
        "code": {
            "coding": [{
                "system": "urn:physionet:mimic-iv:d_labitems",
                "code": str(row["itemid"]),
                "display": row.get("label") or "Unknown laboratory item",
            }],
            "text": row.get("label") or "Unknown laboratory item",
        },
        "subject": {"reference": f"Patient/{row['subject_id']}"},
        "extension": [{
            "url": "https://example.edu/fhir/StructureDefinition/mimic-charttime-no-timezone",
            "valueString": str(row.get("charttime") or "unknown"),
        }],
    }
    if row.get("hadm_id") not in (None, "", float("nan")) and pd.notna(row.get("hadm_id")):
        obs["encounter"] = {"reference": f"Encounter/{int(row['hadm_id'])}"}

    if pd.notna(row.get("valuenum")):
        display = row.get("valueuom")
        quantity: dict[str, Any] = {"value": float(row["valuenum"])}
        if display:
            quantity["unit"] = str(display)
        if display in UCUM:
            quantity.update({"system": "http://unitsofmeasure.org", "code": UCUM[display]})
        else:
            warnings.append("Unit is not in the local UCUM allow-list; display preserved only.")
        obs["valueQuantity"] = quantity

    if row.get("flag") in {"abnormal", "normal"}:
        obs["interpretation"] = [{"text": row["flag"]}]
    elif row.get("flag"):
        warnings.append("Unmapped source flag was not asserted as a standard interpretation.")
    return obs, warnings


def unsafe_observation(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "resourceType": "Observation",
        "id": f"mimic-lab-{row['labevent_id']}",
        "status": "final",  # invented
        "code": {"text": row.get("label")},  # source code dropped
        "subject": {"reference": f"Patient/{row['subject_id']}"},
        "encounter": {"reference": "Encounter/UNKNOWN"},  # invented
        "effectiveDateTime": row.get("charttime"),  # timezone uncertainty hidden
        "valueQuantity": {
            "value": row.get("valuenum"),
            "unit": row.get("valueuom"),
            "system": "http://unitsofmeasure.org",
            "code": row.get("valueuom"),  # asserted without validation
        },
    }


def validate(resource: dict[str, Any], source: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    def add(severity: str, rule: str, message: str) -> None:
        issues.append({"severity": severity, "rule": rule, "message": message})
    if resource.get("resourceType") != "Observation":
        add("error", "structure", "resourceType must be Observation")
    if resource.get("status") not in {"registered", "preliminary", "final", "unknown"}:
        add("error", "status", "Unsupported Observation.status")
    if resource.get("status") == "final":
        add("warning", "status-evidence", "Source row does not prove final status")
    identifiers = resource.get("identifier", [])
    if not any(x.get("value") == str(source["labevent_id"]) for x in identifiers):
        add("error", "provenance", "Source labevent_id is not recoverable")
    if source.get("hadm_id") is None and "encounter" in resource:
        add("error", "no-invention", "Encounter was invented although hadm_id is null")
    coding = resource.get("code", {}).get("coding", [])
    if not any(x.get("code") == str(source["itemid"]) for x in coding):
        add("error", "terminology", "Local item code was dropped")
    quantity = resource.get("valueQuantity", {})
    if quantity.get("system") == "http://unitsofmeasure.org":
        expected = UCUM.get(source.get("valueuom"))
        if not expected or quantity.get("code") != expected:
            add("error", "ucum", "UCUM was asserted without validated evidence")
    if "effectiveDateTime" in resource and "+" not in str(resource["effectiveDateTime"])[10:] and not str(resource["effectiveDateTime"]).endswith("Z"):
        add("warning", "time", "Timezone-free source time was presented as FHIR dateTime")
    return issues


def save_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def flatten_json(value: Any, prefix: str = "Observation", depth: int = 0) -> list[tuple[str, str, int]]:
    """Turn JSON into labelled tree rows without an extra plotting dependency."""
    rows: list[tuple[str, str, int]] = []
    if isinstance(value, dict):
        rows.append((prefix, "object", depth))
        for key, child in value.items():
            rows.extend(flatten_json(child, key, depth + 1))
    elif isinstance(value, list):
        rows.append((prefix, f"array[{len(value)}]", depth))
        for index, child in enumerate(value):
            rows.extend(flatten_json(child, f"[{index}]", depth + 1))
    else:
        rows.append((prefix, json.dumps(value, ensure_ascii=False), depth))
    return rows


def plot_json_tree(resource: dict[str, Any], output: Path) -> None:
    rows = flatten_json(resource)
    height = max(8, min(18, len(rows) * 0.34))
    fig, ax = plt.subplots(figsize=(12, height))
    ax.set_xlim(0, 1)
    ax.set_ylim(-1, len(rows))
    ax.axis("off")
    colors = {"object": "#075985", "array": "#7c3aed"}
    for index, (name, kind_or_value, depth) in enumerate(rows):
        y = len(rows) - index - 1
        x = 0.04 + depth * 0.055
        if index > 0:
            ax.plot([x - 0.025, x - 0.008], [y, y], color="#94a3b8", lw=1)
        is_container = kind_or_value.startswith("object") or kind_or_value.startswith("array")
        color = colors.get(kind_or_value.split("[")[0], "#334155")
        label = f"{name}  {kind_or_value}" if is_container else f"{name}: {kind_or_value}"
        ax.text(
            x, y, textwrap.shorten(label, width=92, placeholder="..."),
            va="center", fontsize=8.5, family="monospace", color=color,
            bbox=dict(boxstyle="round,pad=.22", facecolor="#f8fafc", edgecolor="#cbd5e1")
        )
    ax.set_title("FHIR Observation as a typed JSON resource tree", fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(output / "06_fhir_json_tree.png", dpi=180, bbox_inches="tight")


def plot_student_score(issues: list[dict[str, str]], output: Path) -> int:
    errors = sum(x["severity"] == "error" for x in issues)
    warnings = sum(x["severity"] == "warning" for x in issues)
    score = max(0, 100 - 20 * errors - 5 * warnings)
    categories = ["Structure", "Terminology", "Provenance", "No invention", "Time evidence"]
    rule_to_category = {
        "structure": "Structure", "status": "Structure", "terminology": "Terminology",
        "ucum": "Terminology", "provenance": "Provenance", "no-invention": "No invention",
        "status-evidence": "No invention", "time": "Time evidence",
    }
    deductions = {category: 0 for category in categories}
    for issue in issues:
        category = rule_to_category.get(issue["rule"], "Structure")
        deductions[category] += 20 if issue["severity"] == "error" else 5
    category_scores = [max(0, 20 - deductions[c]) for c in categories]

    fig, (gauge, bars) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1, 2]})
    gauge.axis("off")
    gauge.text(.5, .67, str(score), ha="center", va="center", fontsize=64, weight="bold", color="#075985")
    gauge.text(.5, .47, "/ 100", ha="center", fontsize=18, color="#475569")
    gauge.text(.5, .25, f"{errors} error(s) · {warnings} warning(s)", ha="center", fontsize=11)
    gauge.set_title("Student mapping score", weight="bold")
    bars.barh(categories, category_scores, color=["#0f766e", "#2563eb", "#7c3aed", "#d97706", "#475569"])
    bars.set_xlim(0, 20)
    bars.set_xlabel("Points retained (maximum 20 per criterion)")
    bars.invert_yaxis()
    bars.grid(axis="x", alpha=.25)
    for y, value in enumerate(category_scores):
        bars.text(value + .3, y, str(value), va="center", fontsize=9)
    fig.suptitle("FHIR Mapping Rubric Dashboard", fontsize=15, weight="bold")
    fig.tight_layout()
    fig.savefig(output / "07_student_score_dashboard.png", dpi=180, bbox_inches="tight")
    return score


def main() -> None:
    root = locate_project_root()
    database = locate_database(root)
    output = root / "output" / "week2_visual_demo"
    output.mkdir(parents=True, exist_ok=True)
    print("BMED4702 WEEK 2 VISUAL DEMO")
    print("Run mode:", "REAL MIMIC-IV Demo SQLite" if database else "BUILT-IN TEACHING ROW")
    print("Database:", database or "Not found - no failure; sample row will be used")
    print("Output folder:", output)

    banner(1, "SOURCE EVIDENCE BEFORE FHIR", "15, 33-35")
    rows = get_source_rows(database)
    row = rows.iloc[0].where(pd.notna(rows.iloc[0]), None).to_dict()
    print("SQL file: sql/01_creatinine_source_rows.sql")
    print(rows.head(8).to_string(index=False))
    print("\nQuestion: Which fields may be omitted, and which must never be invented?")
    rows.to_csv(output / "01_creatinine_source_rows.csv", index=False)

    banner(2, "CONSERVATIVE FHIR TRANSFORMATION", "21, 33-36")
    safe, warnings = to_fhir_observation(row)
    unsafe = unsafe_observation(row)
    print("SAFE RESOURCE (unknown status; local coding retained; null encounter omitted):")
    print(json.dumps(safe, indent=2, ensure_ascii=False))
    if warnings:
        print("Mapping warning(s):", *warnings, sep="\n- ")
    save_json(output / "02_safe_observation.json", safe)
    save_json(output / "02_unsafe_observation.json", unsafe)

    banner(3, "FOUR-LAYER VALIDATION", "37, 43-45")
    safe_issues = validate(safe, row)
    unsafe_issues = validate(unsafe, row)
    issue_frame = pd.DataFrame([
        *[{"resource": "SAFE", **x} for x in safe_issues],
        *[{"resource": "UNSAFE", **x} for x in unsafe_issues],
    ])
    print(issue_frame.to_string(index=False) if not issue_frame.empty else "No issues detected")
    print("\nTeaching point: valid JSON is only validation layer 1 of 4.")
    issue_frame.to_csv(output / "03_validation_issues.csv", index=False)
    save_json(output / "03_validation_issues.json", issue_frame.to_dict("records"))

    counts = pd.DataFrame({
        "resource": ["SAFE", "UNSAFE"],
        "errors": [sum(x["severity"] == "error" for x in safe_issues), sum(x["severity"] == "error" for x in unsafe_issues)],
        "warnings": [sum(x["severity"] == "warning" for x in safe_issues), sum(x["severity"] == "warning" for x in unsafe_issues)],
    }).set_index("resource")
    ax = counts.plot(kind="bar", color=["#b91c1c", "#d97706"], rot=0, figsize=(8, 5))
    ax.set_title("Validation evidence: safe vs unsafe mapping")
    ax.set_ylabel("Number of detected issues")
    ax.set_xlabel("")
    ax.grid(axis="y", alpha=.25)
    plt.tight_layout()
    plt.savefig(output / "03_safe_vs_unsafe_validation.png", dpi=180)

    banner(4, "TERMINOLOGY AND UCUM DECISIONS", "24-32")
    unit_counts = rows.assign(
        ucum_status=rows["valueuom"].map(lambda x: "recognized" if x in UCUM else "not asserted")
    )["ucum_status"].value_counts()
    print(unit_counts.rename("rows").to_string())
    print("\nRule: preserve unit display; assert UCUM system/code only after recognition.")
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    unit_counts.plot(kind="bar", ax=ax2, color=["#047857", "#9ca3af"], rot=0)
    ax2.set_title("UCUM assertion decision for selected source rows")
    ax2.set_ylabel("Rows")
    ax2.grid(axis="y", alpha=.25)
    plt.tight_layout()
    plt.savefig(output / "04_ucum_decisions.png", dpi=180)

    banner(5, "CLINICALLY COHERENT TIME SERIES", "40-42")
    timeline = rows[(rows["label"].fillna("").str.lower() == "creatinine") & rows["valuenum"].notna()].copy()
    timeline["charttime_parsed"] = pd.to_datetime(timeline["charttime"], errors="coerce")
    timeline = timeline.dropna(subset=["charttime_parsed"]).sort_values("charttime_parsed")
    print(timeline[["subject_id", "charttime", "valuenum", "valueuom"]].head(12).to_string(index=False))
    fig3, ax3 = plt.subplots(figsize=(9, 5))
    if not timeline.empty:
        for subject, group in timeline.groupby("subject_id"):
            ax3.plot(group["charttime_parsed"], group["valuenum"], marker="o", label=f"Patient/{subject}")
        if timeline["subject_id"].nunique() <= 6:
            ax3.legend(fontsize=8)
    ax3.set_title("Creatinine timeline - source time, value, and unit kept visible")
    ax3.set_ylabel(f"Value ({', '.join(map(str, timeline['valueuom'].dropna().unique())) or 'unit unknown'})")
    ax3.set_xlabel("charttime (timezone not supplied by source)")
    ax3.grid(alpha=.25)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(output / "05_creatinine_timeline.png", dpi=180)

    banner(6, "FHIR JSON TREE", "10-14, 21")
    plot_json_tree(safe, output)
    print("The fourth graphic displays the real generated resource as a typed JSON tree.")

    banner(7, "STUDENT SCORING DASHBOARD", "43-45")
    student_score = plot_student_score(unsafe_issues, output)
    print(f"Starter unsafe mapping score: {student_score}/100")
    print("Formula: score = max(0, 100 - 20*errors - 5*warnings)")

    canonical = json.dumps(row, sort_keys=True, default=str).encode("utf-8")
    provenance = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(database) if database else "built-in teaching row",
        "source_open_mode": "read-only" if database else "not applicable",
        "source_record": {"table": "labevents + d_labitems", "labevent_id": row["labevent_id"]},
        "source_sha256": hashlib.sha256(canonical).hexdigest(),
        "transform": {"name": "week2_conservative_fhir_mapper", "version": "1.0.0"},
        "warnings": warnings,
        "starter_student_score": student_score,
        "outputs": sorted(p.name for p in output.iterdir()),
    }
    save_json(output / "06_provenance.json", provenance)

    print("\n" + "=" * 78)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY")
    print("Five plots are open in PyCharm's Plots window.")
    print("Text results are above: scroll UP in the Run window.")
    print("Files saved in:", output)
    print("NOTE: 'Process finished with exit code 0' means SUCCESS, not an error.")
    print("=" * 78)
    plt.show(block=True)


if __name__ == "__main__":
    main()
