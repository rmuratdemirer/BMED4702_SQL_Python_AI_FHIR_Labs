from __future__ import annotations

import os
from pathlib import Path

from src.ai_explain import explain
from src.lab_creatinine import run


def load_local_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    project_root = Path(__file__).resolve().parent
    load_local_env(project_root / ".env")
    database = project_root / "data" / "mimic_demo.sqlite"
    summary = run(database, project_root)
    explanation = explain(
        project_root / "output" / "evidence_summary.json",
        project_root / "output" / "ai_explanation.txt",
    )
    print("Evidence summary:", summary)
    print("Explanation:", explanation)
    print("Outputs:", project_root / "output")


if __name__ == "__main__":
    main()
