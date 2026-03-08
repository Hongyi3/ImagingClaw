import json
from pathlib import Path
import subprocess
import sys

from clawimaging.artifacts import validate_artifact_bundle


def _run_package(args: list[str], output_dir: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "paper" / "scripts" / "build_package.py"
    subprocess.run(
        [sys.executable, str(script_path), *args, "--output", str(output_dir)],
        check=True,
    )


def test_build_software_package_bundle(tmp_path: Path) -> None:
    output_dir = tmp_path / "software-package"
    _run_package(["--package", "software"], output_dir)

    validate_artifact_bundle(output_dir)
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))

    assert metrics["package_type"] == "software"
    assert (output_dir / "documents" / "release" / "v1.0.yaml").exists()
    assert (output_dir / "metadata" / "CITATION.cff").exists()
    assert (output_dir / "tables" / "release_readiness.tsv").exists()


def test_build_benchmark_package_demo_bundle(tmp_path: Path) -> None:
    output_dir = tmp_path / "benchmark-package"
    _run_package(["--package", "benchmark", "--demo"], output_dir)

    validate_artifact_bundle(output_dir)
    validate_artifact_bundle(output_dir / "runs" / "source-benchmark")
    validate_artifact_bundle(output_dir / "runs" / "paper-assets")
    validate_artifact_bundle(output_dir / "runs" / "repro-export")

    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["package_type"] == "benchmark"
    assert (output_dir / "figures" / "manuscript_preview.pgm").exists()
    assert (output_dir / "tables" / "benchmark_summary.tsv").exists()
    assert (output_dir / "tables" / "release_metadata_audit.tsv").exists()
    assert (output_dir / "documents" / "benchmarks" / "specs" / "lodopab_ct_baselines.yaml").exists()
