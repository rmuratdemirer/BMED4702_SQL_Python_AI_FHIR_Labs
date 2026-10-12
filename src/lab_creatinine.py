from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

import matplotlib.pyplot as plt

from .db import read_only_connection
from .provenance import write_manifest


PARAMETERS = {"subject_id": 10035631, "hadm_id": 29276678, "itemid": 50912}


def run(database: Path, project_root: Path) -> dict[str, object]:
    started_at = datetime.now(timezone.utc).isoformat()
    query_path = project_root / "sql" / "02_creatinine_timeline.sql"
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    query = query_path.read_text(encoding="utf-8")

    with read_only_connection(database) as con:
        rows = [dict(row) for row in con.execute(query, PARAMETERS).fetchall()]

    if not rows:
        raise RuntimeError("The parameterized query returned no rows")
    event_ids = [row["labevent_id"] for row in rows]
    if len(event_ids) != len(set(event_ids)):
        raise AssertionError("The query changed the intended grain: duplicate labevent_id")

    csv_path = output_dir / "creatinine_timeline.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    values = [float(row["valuenum"]) for row in rows]
    lags = [float(row["availability_minutes"]) for row in rows if row["availability_minutes"] is not None]
    summary = {
        "analyte": rows[0]["label"],
        "unit": rows[0]["valueuom"],
        "event_count": len(rows),
        "first_value": values[0],
        "last_value": values[-1],
        "minimum": min(values),
        "maximum": max(values),
        "median": median(values),
        "abnormal_flag_count": sum(row["flag"] == "abnormal" for row in rows),
        "mean_availability_minutes": round(mean(lags), 2),
        "interpretation_boundary": "Engineering summary only. No diagnosis or treatment inference.",
    }
    summary_path = output_dir / "evidence_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    figure_path = output_dir / "creatinine_timeline.png"
    times = [datetime.fromisoformat(str(row["charttime"])) for row in rows]
    lower = rows[0]["ref_range_lower"]
    upper = rows[0]["ref_range_upper"]
    fig, ax = plt.subplots(figsize=(10, 4.8), constrained_layout=True)
    ax.plot(times, values, marker="o", color="#0F766E", linewidth=2)
    if lower is not None and upper is not None:
        ax.axhspan(float(lower), float(upper), color="#14B8A6", alpha=0.14, label="source reference range")
    ax.set_title("Creatinine timeline: deidentified MIMIC-IV Demo admission")
    ax.set_xlabel("Chart time")
    ax.set_ylabel(f"Creatinine ({summary['unit']})")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left")
    fig.autofmt_xdate()
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    manifest_path = output_dir / "provenance.json"
    write_manifest(
        manifest_path,
        database,
        query_path,
        Path(__file__),
        [csv_path, summary_path, figure_path],
        PARAMETERS,
        started_at,
        project_root,
    )
    return summary
