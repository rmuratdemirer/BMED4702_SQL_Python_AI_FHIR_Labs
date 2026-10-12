from __future__ import annotations

import hashlib
import json
import platform
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_manifest(
    destination: Path,
    database: Path,
    query: Path,
    script: Path,
    outputs: list[Path],
    parameters: dict[str, int],
    started_at: str,
    project_root: Path,
) -> None:
    def portable_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(project_root.resolve()).as_posix()
        except ValueError:
            return path.name

    ended_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "standard": "W3C PROV-inspired educational manifest",
        "entity": {
            "database": {"path": portable_path(database), "sha256": sha256(database)},
            "query": {"path": portable_path(query), "sha256": sha256(query)},
            "script": {"path": portable_path(script), "sha256": sha256(script)},
            "outputs": [
                {"path": portable_path(path), "sha256": sha256(path)} for path in outputs
            ],
        },
        "activity": {
            "id": "creatinine_lab_run",
            "started_at": started_at,
            "ended_at": ended_at,
            "used": ["database", "query", "script"],
            "generated": [portable_path(path) for path in outputs],
            "parameters": parameters,
        },
        "agent": {
            "software": "Python",
            "python_version": platform.python_version(),
            "sqlite_version": sqlite3.sqlite_version,
            "platform": platform.platform(),
            "human_role": "student_or_instructor",
        },
    }
    destination.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
