from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping

import yaml

from .datasets import get_dataset_entry
from .specs import DatasetEntry, ExperimentSpec


def _as_mapping(data: Any, *, context: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{context} must be a mapping")
    return dict(data)


def _as_non_empty_string(value: Any, *, context: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{context} must not be blank")
    return text


def resolve_support_path(raw_path: str | Path, *, base_dir: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    return (Path(base_dir).resolve() / path).resolve()


@dataclass(frozen=True)
class RunInputSpec:
    measurement_path: Path
    reference_path: Path | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "measurement_path": str(self.measurement_path),
            "provenance": dict(self.provenance),
        }
        if self.reference_path is not None:
            payload["reference_path"] = str(self.reference_path)
        return payload


@dataclass(frozen=True)
class ExperimentRunConfig:
    source_path: Path
    experiment: ExperimentSpec
    dataset_entry: DatasetEntry
    input_spec: RunInputSpec
    acquisition: dict[str, Any]
    method_config: dict[str, Any]

    def override_measurement_path(self, measurement_path: str | Path) -> "ExperimentRunConfig":
        resolved = Path(measurement_path).resolve()
        if not resolved.exists():
            raise ValueError(f"Measurement path does not exist: {resolved}")
        return replace(
            self,
            input_spec=replace(self.input_spec, measurement_path=resolved),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_path": str(self.source_path),
            "experiment": self.experiment.to_dict(),
            "dataset_registry_entry": self.dataset_entry.to_dict(),
            "input": self.input_spec.to_dict(),
            "acquisition": dict(self.acquisition),
            "method_config": dict(self.method_config),
        }


def _validate_required_paths(input_payload: Mapping[str, Any], *, base_dir: Path) -> RunInputSpec:
    if "measurement_path" not in input_payload:
        raise ValueError("Experiment config input missing required field: measurement_path")

    measurement_path = resolve_support_path(
        _as_non_empty_string(input_payload["measurement_path"], context="input.measurement_path"),
        base_dir=base_dir,
    )
    if not measurement_path.exists():
        raise ValueError(f"Measurement path does not exist: {measurement_path}")

    reference_path: Path | None = None
    if "reference_path" in input_payload and input_payload["reference_path"] is not None:
        reference_path = resolve_support_path(
            _as_non_empty_string(input_payload["reference_path"], context="input.reference_path"),
            base_dir=base_dir,
        )
        if not reference_path.exists():
            raise ValueError(f"Reference path does not exist: {reference_path}")

    provenance = _as_mapping(input_payload.get("provenance", {}), context="input.provenance")
    return RunInputSpec(
        measurement_path=measurement_path,
        reference_path=reference_path,
        provenance=provenance,
    )


def load_experiment_config(
    path: str | Path,
    *,
    registry_path: str | Path | None = None,
) -> ExperimentRunConfig:
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    top_level = _as_mapping(payload, context="experiment config")
    required_fields = ("experiment", "input", "acquisition", "method_config")
    missing = [field_name for field_name in required_fields if field_name not in top_level]
    if missing:
        raise ValueError(
            "Experiment config missing required fields: " + ", ".join(missing)
        )

    experiment = ExperimentSpec.from_dict(_as_mapping(top_level["experiment"], context="experiment"))
    dataset_entry = get_dataset_entry(
        experiment.dataset.name,
        experiment.dataset.version,
        path=registry_path,
    )
    experiment.validate_against_dataset(dataset_entry)

    base_dir = config_path.parent
    input_spec = _validate_required_paths(
        _as_mapping(top_level["input"], context="input"),
        base_dir=base_dir,
    )
    acquisition = _as_mapping(top_level["acquisition"], context="acquisition")
    method_config = _as_mapping(top_level["method_config"], context="method_config")

    return ExperimentRunConfig(
        source_path=config_path,
        experiment=experiment,
        dataset_entry=dataset_entry,
        input_spec=input_spec,
        acquisition=acquisition,
        method_config=method_config,
    )
