from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.fhir_observation import write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert the real Demo creatinine series to FHIR R4")
    parser.add_argument(
        "--timezone-offset", default="+00:00",
        help="Explicit serialization assumption because MIMIC timestamps contain no offset",
    )
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parent
    report = write_outputs(project_root / "data" / "mimic_demo.sqlite", project_root, args.timezone_offset)
    print(json.dumps(report, indent=2))
    if not report["valid_for_lab_contract"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
