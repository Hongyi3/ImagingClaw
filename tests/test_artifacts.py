import json
from pathlib import Path

from clawimaging.artifacts import MINIMUM_BUNDLE_FILES, init_artifact_bundle


def test_init_artifact_bundle_supports_report_sections(tmp_path: Path) -> None:
    bundle = init_artifact_bundle(
        tmp_path / "bundle",
        title="Test Bundle",
        skill_name="benchmark-run",
        summary="Smoke test bundle.",
        report_sections=[("Dataset Provenance", "- Data kind: `raw-measurements`")],
        environment_yaml="python: '>=3.10'\n",
        metrics={"status": "validated"},
    )
    for relative_path in MINIMUM_BUNDLE_FILES:
        assert (bundle / relative_path).exists()

    report = (bundle / "report.md").read_text(encoding="utf-8")
    metrics = json.loads((bundle / "metrics.json").read_text(encoding="utf-8"))
    assert "## Dataset Provenance" in report
    assert metrics["status"] == "validated"
