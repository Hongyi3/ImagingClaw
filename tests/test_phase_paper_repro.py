import json
from pathlib import Path
import subprocess
import sys

import numpy as np

from clawimaging.artifacts import validate_artifact_bundle
from clawimaging.skill_workflows.phase import generate_phase_demo_case, run_phase_retrieval


def _run_script(script_path: Path, args: list[str], output_dir: Path) -> None:
    subprocess.run(
        [sys.executable, str(script_path), *args, "--output", str(output_dir)],
        check=True,
    )


def test_phase_demo_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "phase-demo"
    _run_script(repo_root / "skills" / "phase-retrieve" / "phase_retrieve.py", ["--demo"], output_dir)

    validate_artifact_bundle(output_dir)
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    report = (output_dir / "report.md").read_text(encoding="utf-8")

    assert metrics["status"] == "completed"
    assert metrics["skill"] == "phase-retrieve"
    assert "relative-error" in metrics["metrics"]
    assert "measurement_residual" in metrics["optical_diagnostics"]
    assert "## Forward Model Assumptions" in report
    assert "## Optical Diagnostics" in report
    assert (output_dir / "tables" / "optical_diagnostics.tsv").exists()


def test_phase_declared_config_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "phase-config"
    _run_script(
        repo_root / "skills" / "phase-retrieve" / "phase_retrieve.py",
        ["--config", str(repo_root / "experiments" / "specs" / "phase_gs_example.yaml")],
        output_dir,
    )

    validate_artifact_bundle(output_dir)
    report = (output_dir / "report.md").read_text(encoding="utf-8")
    assert "## Priors" in report
    assert (output_dir / "figures" / "reconstruction_phase.npy").exists()


def test_phase_self_describing_input_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    case = generate_phase_demo_case(seed=17)
    input_path = tmp_path / "phase_input.npz"
    np.savez(
        input_path,
        measurement=case["measurement"],
        reference_phase=case["reference_phase"],
        support=case["support"],
        provenance_json=json.dumps(
            {
                "data_kind": "synthetic-measurements",
                "measurement_domain": "fourier-magnitude",
                "source": "unit test",
            }
        ),
    )

    output_dir = tmp_path / "phase-input"
    _run_script(
        repo_root / "skills" / "phase-retrieve" / "phase_retrieve.py",
        ["--input", str(input_path)],
        output_dir,
    )

    validate_artifact_bundle(output_dir)
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["run_mode"] == "self-describing-input"


def test_phase_plain_npy_requires_declared_metadata(tmp_path: Path) -> None:
    measurement_path = tmp_path / "measurement.npy"
    np.save(measurement_path, np.zeros((8, 8), dtype=float))

    try:
        run_phase_retrieval(
            tmp_path / "bundle",
            input_path=measurement_path,
            reproduction_command="python3 skills/phase-retrieve/phase_retrieve.py --input measurement.npy",
        )
    except ValueError as exc:
        assert "require --config" in str(exc)
    else:
        raise AssertionError("Expected bare phase input to require --config metadata")


def test_paper_figure_demo_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "paperfig-demo"
    _run_script(repo_root / "skills" / "paper-figure" / "paper_figure.py", ["--demo"], output_dir)

    validate_artifact_bundle(output_dir)
    assert (output_dir / "figures" / "manuscript_preview.pgm").exists()
    assert (output_dir / "tables" / "manuscript_metrics.tsv").exists()
    assert (output_dir / "reproducibility" / "figure_provenance.json").exists()


def test_paper_script_demo_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "paper-script-demo"
    _run_script(repo_root / "paper" / "scripts" / "regenerate_assets.py", ["--demo"], output_dir)

    validate_artifact_bundle(output_dir)
    assert (output_dir / "figures" / "manuscript_preview.pgm").exists()


def test_repro_export_demo_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "repro-demo"
    _run_script(repo_root / "skills" / "repro-export" / "repro_export.py", ["--demo"], output_dir)

    validate_artifact_bundle(output_dir)
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["metadata_audit_status"] == "warning"
    assert (output_dir / "tables" / "source_inventory.tsv").exists()
    assert (output_dir / "reproducibility" / "metadata_audit.json").exists()
