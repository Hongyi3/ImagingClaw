import json
import stat
from pathlib import Path

import pytest

from clawimaging.artifacts import (
    MINIMUM_BUNDLE_FILES,
    init_artifact_bundle,
    refresh_checksums,
    validate_artifact_bundle,
)


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
    commands_mode = (bundle / "reproducibility" / "commands.sh").stat().st_mode

    validate_artifact_bundle(bundle)
    assert "## Dataset Provenance" in report
    assert metrics["status"] == "validated"
    assert commands_mode & stat.S_IXUSR


def test_validate_artifact_bundle_detects_tampering(tmp_path: Path) -> None:
    bundle = init_artifact_bundle(
        tmp_path / "bundle",
        title="Tamper Test",
        skill_name="benchmark-run",
        summary="Smoke test bundle.",
    )

    (bundle / "report.md").write_text("# Mutated report\n", encoding="utf-8")

    with pytest.raises(ValueError, match="checksum mismatch for report.md"):
        validate_artifact_bundle(bundle)


def test_refresh_checksums_tracks_generated_files_in_sorted_order(tmp_path: Path) -> None:
    bundle = init_artifact_bundle(
        tmp_path / "bundle",
        title="Checksum Test",
        skill_name="benchmark-run",
        summary="Smoke test bundle.",
    )
    (bundle / "figures" / "preview.txt").write_text("preview\n", encoding="utf-8")
    (bundle / "tables" / "summary.tsv").write_text("metric\tvalue\npsnr\t32.1\n", encoding="utf-8")

    refresh_checksums(bundle)
    validate_artifact_bundle(bundle)

    checksum_lines = (bundle / "reproducibility" / "checksums.sha256").read_text(
        encoding="utf-8"
    ).splitlines()
    relative_paths = [line.split("  ", 1)[1] for line in checksum_lines]

    assert relative_paths == sorted(relative_paths)
    assert "figures/preview.txt" in relative_paths
    assert "tables/summary.tsv" in relative_paths
    assert "reproducibility/checksums.sha256" not in relative_paths
