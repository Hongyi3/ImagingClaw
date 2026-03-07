import json
from pathlib import Path
import subprocess
import sys

import yaml

from clawimaging.artifacts import MINIMUM_BUNDLE_FILES


def test_benchmark_run_writes_resolved_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "skills" / "benchmark-run" / "benchmark_run.py"
    output_dir = tmp_path / "bundle"

    subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--input",
            str(repo_root / "benchmarks" / "specs" / "lodopab_ct_baselines.yaml"),
            "--output",
            str(output_dir),
        ],
        check=True,
    )

    for relative_path in MINIMUM_BUNDLE_FILES:
        assert (output_dir / relative_path).exists()

    manifest = yaml.safe_load((output_dir / "resolved_config.yaml").read_text(encoding="utf-8"))
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    report = (output_dir / "report.md").read_text(encoding="utf-8")

    assert manifest["dataset"]["registry_entry"]["data_kind"] == "raw-measurements"
    assert manifest["source_paths"]["benchmark_spec"] == "benchmarks/specs/lodopab_ct_baselines.yaml"
    assert metrics["benchmark"]["name"] == "lodopab-ct-baselines"
    assert metrics["environment_digest"]
    assert "## Dataset Provenance" in report
    assert "## Reproducibility Notes" in report
