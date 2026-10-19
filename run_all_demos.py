"""Run all six Week 1 demonstrations and create one provenance manifest."""

from pathlib import Path

from src.presentation_demos import run


def main() -> None:
    project_root = Path(__file__).resolve().parent
    output_directory = run(project_root, "all")
    print("All six Week 1 demonstrations completed.")
    print("New output directory:", output_directory)
    print("Provenance manifest:", output_directory / "provenance.json")
    print("Aggregate-only AI packet:", output_directory / "ai_evidence_packet.json")


if __name__ == "__main__":
    main()
