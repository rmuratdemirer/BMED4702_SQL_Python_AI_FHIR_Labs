from __future__ import annotations

import json
import os
import re
from pathlib import Path


def deterministic_explanation(evidence: dict[str, object]) -> str:
    return (
        f"The query returned {evidence['event_count']} numeric {evidence['analyte']} events in "
        f"{evidence['unit']}. Observed values ranged from {evidence['minimum']} to "
        f"{evidence['maximum']}. The mean interval between chart time and store time was "
        f"{evidence['mean_availability_minutes']} minutes. These facts describe the extracted "
        "records and workflow timing. They do not establish a diagnosis or treatment decision."
    )


def allowed_numbers(evidence: dict[str, object]) -> set[str]:
    values: set[str] = set()
    for value in evidence.values():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            values.add(str(value))
            if isinstance(value, float) and value.is_integer():
                values.add(str(int(value)))
    return values


def assert_numeric_grounding(text: str, evidence: dict[str, object]) -> None:
    observed = set(re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", text))
    unsupported = observed - allowed_numbers(evidence)
    if unsupported:
        raise ValueError(f"AI introduced unsupported numeric claims: {sorted(unsupported)}")


def explain(summary_path: Path, destination: Path) -> str:
    evidence = json.loads(summary_path.read_text(encoding="utf-8"))
    if os.getenv("AI_ENABLED", "false").lower() != "true":
        text = deterministic_explanation(evidence)
        destination.write_text(text + "\n", encoding="utf-8")
        return text

    model = os.getenv("OPENAI_MODEL", "").strip()
    if not model:
        raise RuntimeError("Set OPENAI_MODEL when AI_ENABLED=true")
    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(
        model=model,
        instructions=(
            "Explain the supplied aggregate EHR evidence for an engineering class. "
            "Use only facts present in the JSON. Do not add numbers. Do not diagnose, "
            "recommend treatment, or imply population prevalence. State one data-quality limitation."
        ),
        input=json.dumps(evidence),
    )
    text = response.output_text.strip()
    assert_numeric_grounding(text, evidence)
    destination.write_text(text + "\n", encoding="utf-8")
    return text

