import json
from pathlib import Path
import subprocess
import sys

from clawimaging.release_audit import audit_release_metadata, evaluate_release_readiness


def test_audit_release_metadata_flags_placeholders() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    payload = audit_release_metadata(repo_root)

    assert payload["status"] == "warning"
    assert any("placeholder" in warning for warning in payload["warnings"])


def test_evaluate_release_readiness_repo_defaults() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    payload = evaluate_release_readiness(repo_root)

    assert payload["status"] == "warning"
    assert any(check["name"] == "benchmark_specs_valid" for check in payload["checks"])


def test_check_release_readiness_script_reports_warning() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "check_release_readiness.py")],
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["status"] == "warning"
