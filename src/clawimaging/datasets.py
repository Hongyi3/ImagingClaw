from __future__ import annotations

from pathlib import Path

import yaml

from .paths import find_repo_root
from .specs import DatasetEntry


def _resolve_registry_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path).resolve()
    return (find_repo_root() / "datasets" / "registry.yaml").resolve()


def _candidate_support_paths(registry_path: Path, raw_path: str) -> list[Path]:
    support_path = Path(raw_path)
    if support_path.is_absolute():
        return [support_path]

    candidates = [(registry_path.parent / support_path).resolve()]
    try:
        repo_root = find_repo_root(registry_path)
    except FileNotFoundError:
        repo_root = None
    if repo_root is not None:
        repo_candidate = (repo_root / support_path).resolve()
        if repo_candidate not in candidates:
            candidates.append(repo_candidate)
    return candidates


def _validate_dataset_card(entry: DatasetEntry, *, registry_path: Path) -> None:
    if any(candidate.exists() for candidate in _candidate_support_paths(registry_path, entry.card)):
        return
    raise ValueError(
        f"Dataset registry entry {entry.name}@{entry.version} references missing card path: "
        f"{entry.card}"
    )


def load_dataset_registry(path: str | Path | None = None) -> dict[tuple[str, str], DatasetEntry]:
    registry_path = _resolve_registry_path(path)
    with registry_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    if not isinstance(payload, dict):
        raise ValueError("Dataset registry must be a mapping")
    datasets_raw = payload.get("datasets", [])
    if not isinstance(datasets_raw, list):
        raise ValueError("Dataset registry 'datasets' field must be a list")

    registry: dict[tuple[str, str], DatasetEntry] = {}
    for index, dataset_raw in enumerate(datasets_raw):
        try:
            entry = DatasetEntry.from_dict(dataset_raw)
        except ValueError as exc:
            raise ValueError(f"Dataset registry entry #{index + 1}: {exc}") from exc
        key = (entry.name, entry.version)
        if key in registry:
            raise ValueError(f"Dataset registry contains duplicate entry for {entry.name}@{entry.version}")
        _validate_dataset_card(entry, registry_path=registry_path)
        registry[key] = entry

    return registry


def get_dataset_entry(
    name: str,
    version: str,
    path: str | Path | None = None,
) -> DatasetEntry:
    registry = load_dataset_registry(path)
    key = (name, version)
    if key not in registry:
        raise ValueError(f"Dataset registry entry not found for {name}@{version}")
    return registry[key]
