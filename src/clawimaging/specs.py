from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


ALLOWED_DATASET_ACCESS = {"open", "application-required", "restricted", "private"}
ALLOWED_DATA_KINDS = {
    "raw-measurements",
    "partially-processed-measurements",
    "reconstructed-images",
    "synthetic-measurements",
}
REQUIRED_BASELINE_CLASSES = {"analytic", "iterative", "learned"}


def _as_mapping(data: Any, *, context: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{context} must be a mapping")
    return dict(data)


def _require_fields(data: Mapping[str, Any], *, context: str, fields: tuple[str, ...]) -> None:
    missing = [field_name for field_name in fields if field_name not in data]
    if missing:
        missing_fields = ", ".join(missing)
        raise ValueError(f"{context} missing required fields: {missing_fields}")


def _as_non_empty_string(value: Any, *, context: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{context} must not be blank")
    return text


def _as_string_list(values: Any, *, context: str) -> list[str]:
    if not isinstance(values, list):
        raise ValueError(f"{context} must be a list")
    result: list[str] = []
    for index, value in enumerate(values):
        result.append(_as_non_empty_string(value, context=f"{context}[{index}]"))
    return result


def _as_int(value: Any, *, context: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context} must be an integer") from exc


def _validate_non_empty_list(values: list[str], *, context: str) -> list[str]:
    if not values:
        raise ValueError(f"{context} must not be empty")
    return values


@dataclass
class DatasetRef:
    name: str
    version: str
    split: str
    access: str
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DatasetRef":
        payload = _as_mapping(data, context="DatasetRef")
        _require_fields(
            payload,
            context="DatasetRef",
            fields=("name", "version", "split", "access"),
        )
        access = str(payload["access"])
        if access not in ALLOWED_DATASET_ACCESS:
            allowed = ", ".join(sorted(ALLOWED_DATASET_ACCESS))
            raise ValueError(f"DatasetRef access must be one of: {allowed}")
        return cls(
            name=_as_non_empty_string(payload["name"], context="DatasetRef.name"),
            version=_as_non_empty_string(payload["version"], context="DatasetRef.version"),
            split=_as_non_empty_string(payload["split"], context="DatasetRef.split"),
            access=access,
            notes=_as_string_list(payload.get("notes", []), context="DatasetRef.notes"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DatasetEntry:
    name: str
    version: str
    modality: str
    measurement_domain: str
    data_kind: str
    access: str
    source: str
    redistribution_policy: str
    license_or_terms: str
    labels: list[str]
    known_preprocessing_assumptions: list[str]
    card: str
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DatasetEntry":
        payload = _as_mapping(data, context="DatasetEntry")
        _require_fields(
            payload,
            context="DatasetEntry",
            fields=(
                "name",
                "version",
                "modality",
                "measurement_domain",
                "data_kind",
                "access",
                "source",
                "redistribution_policy",
                "license_or_terms",
                "labels",
                "known_preprocessing_assumptions",
                "card",
                "notes",
            ),
        )
        data_kind = str(payload["data_kind"])
        if data_kind not in ALLOWED_DATA_KINDS:
            allowed = ", ".join(sorted(ALLOWED_DATA_KINDS))
            raise ValueError(f"DatasetEntry data_kind must be one of: {allowed}")
        access = str(payload["access"])
        if access not in ALLOWED_DATASET_ACCESS:
            allowed = ", ".join(sorted(ALLOWED_DATASET_ACCESS))
            raise ValueError(f"DatasetEntry access must be one of: {allowed}")
        return cls(
            name=_as_non_empty_string(payload["name"], context="DatasetEntry.name"),
            version=_as_non_empty_string(payload["version"], context="DatasetEntry.version"),
            modality=_as_non_empty_string(payload["modality"], context="DatasetEntry.modality"),
            measurement_domain=_as_non_empty_string(
                payload["measurement_domain"],
                context="DatasetEntry.measurement_domain",
            ),
            data_kind=data_kind,
            access=access,
            source=_as_non_empty_string(payload["source"], context="DatasetEntry.source"),
            redistribution_policy=_as_non_empty_string(
                payload["redistribution_policy"],
                context="DatasetEntry.redistribution_policy",
            ),
            license_or_terms=_as_non_empty_string(
                payload["license_or_terms"],
                context="DatasetEntry.license_or_terms",
            ),
            labels=_as_string_list(payload["labels"], context="DatasetEntry.labels"),
            known_preprocessing_assumptions=_as_string_list(
                payload["known_preprocessing_assumptions"],
                context="DatasetEntry.known_preprocessing_assumptions",
            ),
            card=_as_non_empty_string(payload["card"], context="DatasetEntry.card"),
            notes=_as_string_list(payload["notes"], context="DatasetEntry.notes"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ForwardModelSpec:
    operator: str
    geometry: str
    noise_model: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ForwardModelSpec":
        payload = _as_mapping(data, context="ForwardModelSpec")
        _require_fields(
            payload,
            context="ForwardModelSpec",
            fields=("operator", "geometry", "noise_model"),
        )
        return cls(
            operator=_as_non_empty_string(payload["operator"], context="ForwardModelSpec.operator"),
            geometry=_as_non_empty_string(payload["geometry"], context="ForwardModelSpec.geometry"),
            noise_model=_as_non_empty_string(
                payload["noise_model"],
                context="ForwardModelSpec.noise_model",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MethodSpec:
    name: str
    method_class: str
    config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MethodSpec":
        payload = _as_mapping(data, context="MethodSpec")
        _require_fields(payload, context="MethodSpec", fields=("name", "class"))
        return cls(
            name=_as_non_empty_string(payload["name"], context="MethodSpec.name"),
            method_class=_as_non_empty_string(payload["class"], context="MethodSpec.class"),
            config=_as_mapping(payload.get("config", {}), context="MethodSpec.config"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["class"] = payload.pop("method_class")
        return payload


@dataclass
class ExperimentSpec:
    experiment_id: str
    title: str
    modality: str
    task: str
    dataset: DatasetRef
    forward_model: ForwardModelSpec
    method: str
    metrics: list[str]
    seed: int
    hardware: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentSpec":
        payload = _as_mapping(data, context="ExperimentSpec")
        _require_fields(
            payload,
            context="ExperimentSpec",
            fields=(
                "experiment_id",
                "title",
                "modality",
                "task",
                "dataset",
                "forward_model",
                "method",
                "metrics",
                "seed",
            ),
        )
        return cls(
            experiment_id=_as_non_empty_string(
                payload["experiment_id"],
                context="ExperimentSpec.experiment_id",
            ),
            title=_as_non_empty_string(payload["title"], context="ExperimentSpec.title"),
            modality=_as_non_empty_string(payload["modality"], context="ExperimentSpec.modality"),
            task=_as_non_empty_string(payload["task"], context="ExperimentSpec.task"),
            dataset=DatasetRef.from_dict(payload["dataset"]),
            forward_model=ForwardModelSpec.from_dict(payload["forward_model"]),
            method=_as_non_empty_string(payload["method"], context="ExperimentSpec.method"),
            metrics=_validate_non_empty_list(
                _as_string_list(payload["metrics"], context="ExperimentSpec.metrics"),
                context="ExperimentSpec.metrics",
            ),
            seed=_as_int(payload["seed"], context="ExperimentSpec.seed"),
            hardware=_as_mapping(payload.get("hardware", {}), context="ExperimentSpec.hardware"),
            notes=_as_string_list(payload.get("notes", []), context="ExperimentSpec.notes"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate_against_dataset(self, dataset_entry: DatasetEntry) -> None:
        if dataset_entry.modality != self.modality:
            raise ValueError(
                "ExperimentSpec modality does not match dataset registry entry: "
                f"{self.modality} != {dataset_entry.modality}"
            )
        if dataset_entry.access != self.dataset.access:
            raise ValueError(
                "ExperimentSpec dataset access does not match dataset registry entry: "
                f"{self.dataset.access} != {dataset_entry.access}"
            )


@dataclass
class BenchmarkSpec:
    name: str
    version: str
    modality: str
    task: str
    dataset: DatasetRef
    forward_model: ForwardModelSpec
    preprocessing: list[str]
    calibration_assumptions: list[str]
    methods: list[MethodSpec]
    metrics: list[str]
    seeds: dict[str, int] = field(default_factory=dict)
    hardware: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    notes: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BenchmarkSpec":
        payload = _as_mapping(data, context="BenchmarkSpec")
        _require_fields(
            payload,
            context="BenchmarkSpec",
            fields=(
                "name",
                "version",
                "modality",
                "task",
                "dataset",
                "forward_model",
                "preprocessing",
                "calibration_assumptions",
                "methods",
                "metrics",
                "seeds",
                "hardware",
                "environment",
            ),
        )

        methods_raw = payload["methods"]
        if not isinstance(methods_raw, list):
            raise ValueError("BenchmarkSpec.methods must be a list")
        methods = [MethodSpec.from_dict(method) for method in methods_raw]
        seeds = _as_mapping(payload["seeds"], context="BenchmarkSpec.seeds")
        hardware = _as_mapping(payload["hardware"], context="BenchmarkSpec.hardware")
        environment = _as_mapping(payload["environment"], context="BenchmarkSpec.environment")
        notes = _as_mapping(payload.get("notes", {}), context="BenchmarkSpec.notes")
        benchmark = cls(
            name=_as_non_empty_string(payload["name"], context="BenchmarkSpec.name"),
            version=_as_non_empty_string(payload["version"], context="BenchmarkSpec.version"),
            modality=_as_non_empty_string(payload["modality"], context="BenchmarkSpec.modality"),
            task=_as_non_empty_string(payload["task"], context="BenchmarkSpec.task"),
            dataset=DatasetRef.from_dict(payload["dataset"]),
            forward_model=ForwardModelSpec.from_dict(payload["forward_model"]),
            preprocessing=_validate_non_empty_list(
                _as_string_list(payload["preprocessing"], context="BenchmarkSpec.preprocessing"),
                context="BenchmarkSpec.preprocessing",
            ),
            calibration_assumptions=_validate_non_empty_list(
                _as_string_list(
                    payload["calibration_assumptions"],
                    context="BenchmarkSpec.calibration_assumptions",
                ),
                context="BenchmarkSpec.calibration_assumptions",
            ),
            methods=methods,
            metrics=_validate_non_empty_list(
                _as_string_list(payload["metrics"], context="BenchmarkSpec.metrics"),
                context="BenchmarkSpec.metrics",
            ),
            seeds={
                _as_non_empty_string(key, context="BenchmarkSpec.seeds key"): _as_int(
                    value,
                    context=f"BenchmarkSpec.seeds[{key}]",
                )
                for key, value in seeds.items()
            },
            hardware=hardware,
            environment=environment,
            notes=notes,
        )
        benchmark.validate()
        return benchmark

    def validate(self) -> None:
        if not self.seeds:
            raise ValueError("BenchmarkSpec.seeds must not be empty")
        unknown_classes = {method.method_class for method in self.methods}
        unsupported_classes = unknown_classes - REQUIRED_BASELINE_CLASSES
        if unsupported_classes:
            unsupported = ", ".join(sorted(unsupported_classes))
            raise ValueError(f"BenchmarkSpec.methods contain unsupported classes: {unsupported}")
        method_names: dict[str, str] = {}
        duplicate_names: set[str] = set()
        for method in self.methods:
            normalized_name = method.name.lower()
            if normalized_name in method_names:
                duplicate_names.add(method.name)
                duplicate_names.add(method_names[normalized_name])
                continue
            method_names[normalized_name] = method.name
        if duplicate_names:
            duplicates = ", ".join(sorted(duplicate_names, key=str.lower))
            raise ValueError(f"BenchmarkSpec.methods contain duplicate method names: {duplicates}")
        baseline_classes = {method.method_class for method in self.methods}
        missing_classes = REQUIRED_BASELINE_CLASSES - baseline_classes
        if missing_classes:
            missing = ", ".join(sorted(missing_classes))
            raise ValueError(f"BenchmarkSpec.methods missing required baseline classes: {missing}")

    def validate_against_dataset(self, dataset_entry: DatasetEntry) -> None:
        if dataset_entry.modality != self.modality:
            raise ValueError(
                "BenchmarkSpec modality does not match dataset registry entry: "
                f"{self.modality} != {dataset_entry.modality}"
            )
        if dataset_entry.access != self.dataset.access:
            raise ValueError(
                "BenchmarkSpec dataset access does not match dataset registry entry: "
                f"{self.dataset.access} != {dataset_entry.access}"
            )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["methods"] = [method.to_dict() for method in self.methods]
        return payload
