from pathlib import Path

import pytest
import yaml

from clawimaging.datasets import get_dataset_entry, load_dataset_registry


def _dataset_entry(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "demo-dataset",
        "version": "1.0",
        "modality": "ct",
        "measurement_domain": "sinogram",
        "data_kind": "raw-measurements",
        "access": "open",
        "source": "Demo source",
        "redistribution_policy": "metadata only",
        "license_or_terms": "demo terms",
        "labels": [],
        "known_preprocessing_assumptions": ["none"],
        "card": "cards/demo.md",
        "notes": ["demo"],
    }
    payload.update(overrides)
    return payload


def _write_registry(tmp_path: Path, datasets: list[dict[str, object]]) -> Path:
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir(exist_ok=True)
    (cards_dir / "demo.md").write_text("# Demo\n", encoding="utf-8")
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(yaml.safe_dump({"datasets": datasets}, sort_keys=False), encoding="utf-8")
    return registry_path


def test_load_dataset_registry_repo_defaults() -> None:
    registry = load_dataset_registry()
    assert ("lodopab-ct", "1.0") in registry
    assert registry[("synthetic-phase-objects", "0.1")].data_kind == "synthetic-measurements"


def test_load_dataset_registry_missing_field(tmp_path: Path) -> None:
    broken = _dataset_entry()
    broken.pop("access")
    registry_path = _write_registry(tmp_path=tmp_path, datasets=[broken])
    with pytest.raises(ValueError, match="missing required fields: access"):
        load_dataset_registry(registry_path)


def test_load_dataset_registry_invalid_access(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path=tmp_path,
        datasets=[_dataset_entry(access="public")],
    )
    with pytest.raises(ValueError, match="access must be one of"):
        load_dataset_registry(registry_path)


def test_load_dataset_registry_invalid_data_kind(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path=tmp_path,
        datasets=[_dataset_entry(data_kind="images")],
    )
    with pytest.raises(ValueError, match="data_kind must be one of"):
        load_dataset_registry(registry_path)


def test_load_dataset_registry_duplicate_entry(tmp_path: Path) -> None:
    dataset = _dataset_entry()
    registry_path = _write_registry(tmp_path=tmp_path, datasets=[dataset, dataset])
    with pytest.raises(ValueError, match="duplicate entry"):
        load_dataset_registry(registry_path)


def test_load_dataset_registry_bad_card_path(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path=tmp_path,
        datasets=[_dataset_entry(card="cards/missing.md")],
    )
    with pytest.raises(ValueError, match="missing card path"):
        load_dataset_registry(registry_path)


def test_get_dataset_entry_missing() -> None:
    with pytest.raises(ValueError, match="not found"):
        get_dataset_entry("missing", "1.0")
