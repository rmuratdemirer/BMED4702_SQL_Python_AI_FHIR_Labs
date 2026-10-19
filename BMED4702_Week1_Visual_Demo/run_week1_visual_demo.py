"""BMED4702 Week 1: visible SQL + Python classroom demonstration.

Run this file from PyCharm. It deliberately prints the SQL, displays the
result tables in the Run window, saves CSV/PNG files, and opens plots.
The existing database and project files are never modified.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import pandas as pd
except ImportError as exc:
    raise SystemExit(
        "Missing package. In PyCharm open requirements.txt and install "
        "pandas and matplotlib, then run this file again."
    ) from exc


SCRIPT_DIR = Path(__file__).resolve().parent


def find_project_root() -> Path:
    """Allow the visual-demo folder to sit safely inside the existing project."""
    search_locations = [SCRIPT_DIR, *list(SCRIPT_DIR.parents)[:4]]
    for folder in search_locations:
        data_folder = folder / "data"
        if data_folder.is_dir() and list(data_folder.glob("*.sqlite")):
            return folder
    return SCRIPT_DIR


PROJECT_ROOT = find_project_root()
OUTPUT_DIR = PROJECT_ROOT / "output"


def find_database() -> Path:
    """Find the existing SQLite database without relying on working directory."""
    preferred = [
        PROJECT_ROOT / "data" / "mimic_demo.sqlite",
        PROJECT_ROOT / "data" / "mimiciv_demo.sqlite",
        PROJECT_ROOT / "data" / "mimic_iv_demo.sqlite",
    ]
    for candidate in preferred:
        if candidate.is_file():
            return candidate

    candidates = sorted((PROJECT_ROOT / "data").glob("*.sqlite"))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise FileNotFoundError(
            "No SQLite database was found under the data folder. Expected: "
            "data\\mimic_demo.sqlite"
        )
    raise RuntimeError(
        "More than one SQLite database was found: "
        + ", ".join(path.name for path in candidates)
    )


def safe_output_path(name: str) -> Path:
    """Avoid PermissionError when an earlier CSV/PNG is open in Excel/Photos."""
    target = OUTPUT_DIR / name
    if not target.exists():
        return target
    try:
        with target.open("a", encoding="utf-8"):
            pass
        return target
    except PermissionError:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return target.with_name(f"{target.stem}_{stamp}{target.suffix}")


def print_section(number: int, title: str, sql: str, result: pd.DataFrame) -> None:
    line = "=" * 78
    print(f"\n{line}\nDEMO {number}: {title}\n{line}")
    print("SQL USED:\n")
    print(sql.strip())
    print("\nPYTHON/PANDAS RESULT:\n")
    if result.empty:
        print("No rows returned.")
    else:
        print(result.to_string(index=False))


def table_counts(connection: sqlite3.Connection) -> tuple[pd.DataFrame, plt.Figure]:
    discovery_sql = """
SELECT name AS table_name
FROM sqlite_master
WHERE type = 'table'
  AND name NOT LIKE 'sqlite_%'
ORDER BY name;
"""
    tables = pd.read_sql_query(discovery_sql, connection)["table_name"].tolist()
    rows: list[dict[str, object]] = []
    for table in tables:
        escaped = table.replace('"', '""')
        count = connection.execute(f'SELECT COUNT(*) FROM "{escaped}"').fetchone()[0]
        rows.append({"table_name": table, "row_count": int(count)})

    result = pd.DataFrame(rows).sort_values("row_count", ascending=False)
    print_section(1, "What tables exist and how many rows do they contain?", discovery_sql, result)

    csv_path = safe_output_path("week1_01_table_counts.csv")
    result.to_csv(csv_path, index=False, encoding="utf-8-sig")

    display = result.head(15).sort_values("row_count")
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.barh(display["table_name"], display["row_count"], color="#1666a8")
    ax.set_title("MIMIC-IV Demo — Row Count by Table (Top 15)")
    ax.set_xlabel("Number of rows")
    ax.grid(axis="x", alpha=0.25)
    if not display.empty and display["row_count"].max() > 100 * max(1, display["row_count"].min()):
        ax.set_xscale("log")
        ax.set_xlabel("Number of rows (log scale)")
    fig.tight_layout()
    png_path = safe_output_path("week1_01_table_counts.png")
    fig.savefig(png_path, dpi=180, bbox_inches="tight")
    print(f"\nCSV saved: {csv_path}")
    print(f"Plot saved: {png_path}")
    return result, fig


def table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    escaped = table.replace('"', '""')
    rows = connection.execute(f'PRAGMA table_info("{escaped}")').fetchall()
    return {str(row[1]).lower() for row in rows}


def missingness_demo(connection: sqlite3.Connection) -> tuple[pd.DataFrame | None, plt.Figure | None]:
    tables = {
        row[0].lower(): row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "labevents" not in tables:
        print("\nDEMO 2 skipped: labevents table was not found.")
        return None, None

    actual_table = tables["labevents"]
    columns = table_columns(connection, actual_table)
    candidates = [column for column in ("value", "valuenum", "valueuom", "flag") if column in columns]
    if not candidates:
        print("\nDEMO 2 skipped: expected nullable labevents columns were not found.")
        return None, None

    total = connection.execute(f'SELECT COUNT(*) FROM "{actual_table}"').fetchone()[0]
    rows = []
    for column in candidates:
        missing = connection.execute(
            f'SELECT COUNT(*) FROM "{actual_table}" WHERE "{column}" IS NULL'
        ).fetchone()[0]
        rows.append(
            {
                "column_name": column,
                "total_rows": int(total),
                "missing_rows": int(missing),
                "missing_percent": round(100.0 * missing / total, 2) if total else 0.0,
            }
        )
    result = pd.DataFrame(rows)
    sql = f"""
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN valuenum IS NULL THEN 1 ELSE 0 END) AS missing_valuenum
FROM {actual_table};
"""
    print_section(2, "Missingness is a numerator divided by a declared denominator", sql, result)
    csv_path = safe_output_path("week1_02_missingness.csv")
    result.to_csv(csv_path, index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.bar(result["column_name"], result["missing_percent"], color="#e07b39")
    ax.bar_label(bars, fmt="%.1f%%", padding=3)
    ax.set_ylim(0, max(100, float(result["missing_percent"].max()) * 1.15))
    ax.set_ylabel("Missing values (%)")
    ax.set_title("MIMIC-IV Demo — Missingness Profile in labevents")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    png_path = safe_output_path("week1_02_missingness.png")
    fig.savefig(png_path, dpi=180, bbox_inches="tight")
    print(f"\nCSV saved: {csv_path}")
    print(f"Plot saved: {png_path}")
    return result, fig


def availability_lag_demo(
    connection: sqlite3.Connection,
) -> tuple[pd.DataFrame | None, plt.Figure | None]:
    tables = {
        row[0].lower(): row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "labevents" not in tables:
        print("\nDEMO 3 skipped: labevents table was not found.")
        return None, None

    actual_table = tables["labevents"]
    columns = table_columns(connection, actual_table)
    if not {"charttime", "storetime"}.issubset(columns):
        print("\nDEMO 3 skipped: charttime/storetime columns were not found.")
        return None, None

    sql = f"""
SELECT
    (julianday(storetime) - julianday(charttime)) * 24.0 * 60.0
        AS availability_lag_minutes
FROM {actual_table}
WHERE charttime IS NOT NULL
  AND storetime IS NOT NULL;
"""
    lags = pd.read_sql_query(sql, connection)["availability_lag_minutes"].dropna()
    plausible = lags[(lags >= -1440) & (lags <= 10080)]
    summary = pd.DataFrame(
        [
            {
                "available_pairs": int(lags.size),
                "plausible_pairs_used": int(plausible.size),
                "median_minutes": round(float(plausible.median()), 2) if not plausible.empty else None,
                "mean_minutes": round(float(plausible.mean()), 2) if not plausible.empty else None,
                "p95_minutes": round(float(plausible.quantile(0.95)), 2) if not plausible.empty else None,
            }
        ]
    )
    print_section(3, "charttime is not the same as storetime", sql, summary)
    csv_path = safe_output_path("week1_03_availability_lag_summary.csv")
    summary.to_csv(csv_path, index=False, encoding="utf-8-sig")

    if plausible.empty:
        print("No plausible lag values were available for plotting.")
        return summary, None

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.hist(plausible, bins=35, color="#2a9d8f", edgecolor="white")
    ax.axvline(plausible.median(), color="#b22222", linestyle="--", linewidth=2,
               label=f"Median = {plausible.median():.1f} min")
    ax.set_xlabel("storetime − charttime (minutes)")
    ax.set_ylabel("Number of laboratory events")
    ax.set_title("MIMIC-IV Demo — Laboratory Result Availability Lag")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    png_path = safe_output_path("week1_03_availability_lag.png")
    fig.savefig(png_path, dpi=180, bbox_inches="tight")
    print(f"\nCSV saved: {csv_path}")
    print(f"Plot saved: {png_path}")
    return summary, fig


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    database = find_database()

    print("\nBMED4702 — WEEK 1 VISUAL SQL + PYTHON DEMONSTRATION")
    print("This program is read-only: it never changes the MIMIC-IV database.")
    print(f"Database: {database}")
    print(f"Output folder: {OUTPUT_DIR}")

    figures: list[plt.Figure] = []
    with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as connection:
        counts, figure = table_counts(connection)
        figures.append(figure)

        _, figure = missingness_demo(connection)
        if figure is not None:
            figures.append(figure)

        _, figure = availability_lag_demo(connection)
        if figure is not None:
            figures.append(figure)

    provenance = {
        "course": "BMED4702 Medical Information Systems",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "database_path": str(database),
        "database_open_mode": "read-only",
        "script": Path(__file__).name,
        "tables_counted": int(len(counts)),
        "outputs": sorted(path.name for path in OUTPUT_DIR.glob("week1_*")),
    }
    provenance_path = safe_output_path("week1_demo_provenance.json")
    provenance_path.write_text(json.dumps(provenance, indent=2), encoding="utf-8")

    print("\n" + "=" * 78)
    print("DEMONSTRATION COMPLETED")
    print(f"Provenance saved: {provenance_path}")
    print("The plot window(s) are now displayed. Close them to finish the program.")
    print("=" * 78 + "\n")

    if figures:
        plt.show(block=True)


if __name__ == "__main__":
    main()
