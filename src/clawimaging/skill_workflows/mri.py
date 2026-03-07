from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from ..artifacts import init_artifact_bundle, sha256_text
from ..experiments import ExperimentRunConfig, load_experiment_config, resolve_support_path
from ..metrics import compute_metrics
from ..specs import DatasetRef, ExperimentSpec, ForwardModelSpec
from .common import (
    WorkflowResult,
    environment_snapshot,
    finalize_bundle,
    format_bullets,
    render_analysis_log,
    render_commands,
    stringify_paths,
    write_tsv,
)
from .ct import build_ct_phantom


DEFAULT_MRI_METHOD = "rss-zero-fill"
DEMO_DATASET_NAME = "mri-demo-kspace"
DEMO_DATASET_VERSION = "0.1"


def _fft2c(array: np.ndarray) -> np.ndarray:
    return np.fft.fftshift(
        np.fft.fft2(np.fft.ifftshift(array, axes=(-2, -1)), norm="ortho"),
        axes=(-2, -1),
    )


def _ifft2c(array: np.ndarray) -> np.ndarray:
    return np.fft.fftshift(
        np.fft.ifft2(np.fft.ifftshift(array, axes=(-2, -1)), norm="ortho"),
        axes=(-2, -1),
    )


def build_sensitivity_maps(*, coil_count: int, size: int) -> np.ndarray:
    axis = np.linspace(-1.0, 1.0, size)
    x, y = np.meshgrid(axis, axis, indexing="xy")
    maps = []
    for coil_index in range(coil_count):
        angle = 2.0 * np.pi * coil_index / coil_count
        center_x = 0.55 * np.cos(angle)
        center_y = 0.55 * np.sin(angle)
        magnitude = np.exp(-((x - center_x) ** 2 + (y - center_y) ** 2) / 0.8)
        phase = np.exp(1j * np.pi * (center_x * x + center_y * y))
        maps.append(magnitude * phase)
    sensitivities = np.asarray(maps, dtype=np.complex128)
    normalization = np.sqrt(np.sum(np.abs(sensitivities) ** 2, axis=0, keepdims=True))
    normalization = np.where(normalization == 0.0, 1.0, normalization)
    return np.asarray(sensitivities / normalization, dtype=np.complex128)


def build_cartesian_mask(
    *,
    size: int,
    acceleration: int = 4,
    calibration_width: int = 8,
) -> np.ndarray:
    line_mask = np.zeros(size, dtype=float)
    line_mask[::acceleration] = 1.0
    center = size // 2
    half_width = max(1, calibration_width // 2)
    line_mask[max(0, center - half_width) : min(size, center + half_width)] = 1.0
    return np.repeat(line_mask[:, None], size, axis=1)


def generate_mri_demo_case(
    *,
    seed: int,
    size: int = 64,
    coil_count: int = 4,
    acceleration: int = 4,
) -> dict[str, Any]:
    _ = seed
    reference = build_ct_phantom(size=size)
    sensitivity_maps = build_sensitivity_maps(coil_count=coil_count, size=size)
    coil_images = sensitivity_maps * reference[None, :, :]
    full_kspace = _fft2c(coil_images)
    sampling_mask = build_cartesian_mask(size=size, acceleration=acceleration)
    measured_kspace = full_kspace * sampling_mask[None, :, :]
    return {
        "measurement": measured_kspace,
        "reference": reference.astype(float),
        "acquisition": {
            "sampling_mask": sampling_mask.astype(float),
            "coil_count": coil_count,
            "acceleration": acceleration,
            "coil_combination": "rss",
        },
    }


def _array_from_npy(path: Path) -> np.ndarray:
    data = np.load(path, allow_pickle=False)
    if not isinstance(data, np.ndarray):
        raise ValueError(f"Expected array data in {path}")
    return np.asarray(data)


def _load_npz_payload(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as payload:
        return {name: payload[name] for name in payload.files}


def _load_self_describing_input(path: Path) -> tuple[np.ndarray, np.ndarray, dict[str, Any], dict[str, Any]]:
    payload = _load_npz_payload(path)
    required = {"measurement", "reference", "sampling_mask", "provenance_json"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(
            f"Self-describing MRI input {path} missing required fields: {', '.join(missing)}"
        )
    provenance = json.loads(str(payload["provenance_json"].item()))
    acquisition = {
        "sampling_mask": np.asarray(payload["sampling_mask"], dtype=float),
        "coil_combination": "rss",
        "coil_count": int(np.asarray(payload["measurement"]).shape[0]),
    }
    return (
        np.asarray(payload["measurement"]),
        np.asarray(payload["reference"], dtype=float),
        acquisition,
        provenance,
    )


def _require_mri_provenance(provenance: dict[str, Any]) -> None:
    required_fields = ("data_kind", "measurement_domain", "source")
    missing = [
        field_name
        for field_name in required_fields
        if not str(provenance.get(field_name, "")).strip()
    ]
    if missing:
        raise ValueError("MRI provenance missing required fields: " + ", ".join(missing))


def _mri_experiment(
    *,
    experiment_id: str,
    title: str,
    dataset_name: str,
    dataset_version: str,
    split: str,
    access: str,
    task: str,
    metrics: list[str],
    seed: int,
    notes: list[str],
) -> tuple[ExperimentSpec, dict[str, Any]]:
    from ..datasets import get_dataset_entry

    dataset_entry = get_dataset_entry(dataset_name, dataset_version)
    experiment = ExperimentSpec(
        experiment_id=experiment_id,
        title=title,
        modality="mri",
        task=task,
        dataset=DatasetRef(
            name=dataset_name,
            version=dataset_version,
            split=split,
            access=access,
        ),
        forward_model=ForwardModelSpec(
            operator="fourier-encoding",
            geometry="cartesian",
            noise_model="acquisition-native",
        ),
        method=DEFAULT_MRI_METHOD,
        metrics=metrics,
        seed=seed,
        hardware={"reference_device": "cpu"},
        notes=notes,
    )
    experiment.validate_against_dataset(dataset_entry)
    return experiment, dataset_entry.to_dict()


def _mri_demo_spec(*, seed: int) -> tuple[ExperimentSpec, dict[str, Any]]:
    return _mri_experiment(
        experiment_id="mri-demo-rss-zero-fill",
        title="Synthetic MRI RSS zero-fill smoke run",
        dataset_name=DEMO_DATASET_NAME,
        dataset_version=DEMO_DATASET_VERSION,
        split="synthetic-smoke",
        access="open",
        task="synthetic-mri-reconstruction",
        metrics=["nmse", "psnr", "ssim"],
        seed=seed,
        notes=["Repository-local synthetic MRI demo."],
    )


def _mri_proxy_spec(benchmark_manifest: dict[str, Any]) -> tuple[ExperimentSpec, dict[str, Any]]:
    dataset = dict(benchmark_manifest["dataset"])
    return _mri_experiment(
        experiment_id=f"{benchmark_manifest['name']}-rss-zero-fill-proxy",
        title=f"Proxy MRI baseline for {benchmark_manifest['name']}",
        dataset_name=str(dataset["name"]),
        dataset_version=str(dataset["version"]),
        split=str(dataset["split"]),
        access=str(dataset["access"]),
        task=str(benchmark_manifest["task"]),
        metrics=[str(metric) for metric in benchmark_manifest["metrics"]],
        seed=int(benchmark_manifest["seeds"]["eval"]),
        notes=[
            "Benchmark protocol resolved against the registry.",
            "Executed with synthetic proxy k-space rather than the upstream benchmark dataset.",
        ],
    )


def _resolve_mri_config(
    *,
    input_path: str | Path | None,
    config_path: str | Path,
) -> ExperimentRunConfig:
    config = load_experiment_config(config_path)
    if input_path is not None:
        config = config.override_measurement_path(input_path)
    return config


def _resolve_sampling_mask(config: ExperimentRunConfig) -> np.ndarray:
    if "sampling_mask_path" in config.acquisition:
        mask_path = resolve_support_path(
            str(config.acquisition["sampling_mask_path"]),
            base_dir=config.source_path.parent,
        )
        return _array_from_npy(mask_path).astype(float)
    if "sampling_mask" in config.acquisition:
        return np.asarray(config.acquisition["sampling_mask"], dtype=float)
    raise ValueError("MRI acquisition metadata must declare sampling_mask_path or sampling_mask")


def _validate_mri_config(config: ExperimentRunConfig) -> None:
    if config.experiment.modality != "mri":
        raise ValueError("MRI workflow requires experiment.modality to be 'mri'")
    if config.experiment.method.lower() != DEFAULT_MRI_METHOD:
        raise ValueError(f"MRI Phase 2 supports only the `{DEFAULT_MRI_METHOD}` baseline")
    _require_mri_provenance(config.input_spec.provenance)
    _ = _resolve_sampling_mask(config)


def _load_mri_from_config(
    config: ExperimentRunConfig,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any], dict[str, Any]]:
    _validate_mri_config(config)
    measurement_path = config.input_spec.measurement_path
    if measurement_path.suffix == ".npy":
        if config.input_spec.reference_path is None:
            raise ValueError("MRI config runs require input.reference_path for metrics")
        acquisition = dict(config.acquisition)
        acquisition["sampling_mask"] = _resolve_sampling_mask(config)
        acquisition.setdefault("coil_combination", "rss")
        acquisition.setdefault("coil_count", int(_array_from_npy(measurement_path).shape[0]))
        return (
            _array_from_npy(measurement_path),
            _array_from_npy(config.input_spec.reference_path).astype(float),
            acquisition,
            dict(config.input_spec.provenance),
        )
    if measurement_path.suffix == ".npz":
        measurement, reference, acquisition, provenance = _load_self_describing_input(measurement_path)
        acquisition.update(dict(config.acquisition))
        if "sampling_mask_path" in acquisition:
            acquisition["sampling_mask"] = _resolve_sampling_mask(config)
        if config.input_spec.reference_path is not None:
            reference = _array_from_npy(config.input_spec.reference_path).astype(float)
        return measurement, reference, acquisition, {**provenance, **dict(config.input_spec.provenance)}
    raise ValueError("MRI input must be a .npy or .npz file")


def reconstruct_zero_filled(kspace: np.ndarray) -> np.ndarray:
    coil_images = _ifft2c(kspace)
    return np.asarray(np.sqrt(np.sum(np.abs(coil_images) ** 2, axis=0)), dtype=float)


def _method_config(method_config: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {"coil_combination": "rss", "transform": "ifft2c"}
    if method_config:
        payload.update(method_config)
    if str(payload["coil_combination"]).lower() != "rss":
        raise ValueError("MRI Phase 2 supports only RSS coil combination")
    return payload


def _report_sections(
    *,
    experiment: ExperimentSpec,
    dataset_entry: dict[str, Any],
    acquisition: dict[str, Any],
    provenance: dict[str, Any],
    metric_values: dict[str, float],
    environment_digest: str,
    proxy_for_benchmark: bool,
    run_mode: str,
) -> list[tuple[str, str]]:
    mask = np.asarray(acquisition["sampling_mask"], dtype=float)
    notes_block = format_bullets(list(experiment.notes)) if experiment.notes else "- none"
    return [
        (
            "Run Metadata",
            "\n".join(
                [
                    f"- Experiment: `{experiment.experiment_id}`",
                    f"- Title: {experiment.title}",
                    f"- Task: `{experiment.task}`",
                    f"- Run mode: `{run_mode}`",
                    f"- Method: `{experiment.method}`",
                ]
            ),
        ),
        (
            "Data Provenance",
            "\n".join(
                [
                    f"- Protocol dataset: `{experiment.dataset.name}` `{experiment.dataset.version}` ({experiment.dataset.split})",
                    f"- Registry data kind: `{dataset_entry['data_kind']}`",
                    f"- Executed input data kind: `{provenance['data_kind']}`",
                    f"- Measurement domain: `{provenance['measurement_domain']}`",
                    f"- Source: {provenance['source']}",
                    f"- Proxy for benchmark protocol: `{proxy_for_benchmark}`",
                ]
            ),
        ),
        (
            "Acquisition",
            "\n".join(
                [
                    f"- Forward operator: `{experiment.forward_model.operator}`",
                    f"- Geometry: `{experiment.forward_model.geometry}`",
                    f"- Noise model: `{experiment.forward_model.noise_model}`",
                    f"- Coil count: `{acquisition['coil_count']}`",
                    f"- Coil combination: `{acquisition['coil_combination']}`",
                    f"- Sampling fraction: `{float(np.mean(mask)):.4f}`",
                ]
            ),
        ),
        (
            "Metrics",
            format_bullets([f"{name}: {value:.6f}" for name, value in metric_values.items()]),
        ),
        (
            "Reproducibility Notes",
            "\n".join(
                [
                    f"- Environment digest: `{environment_digest}`",
                    f"- Requested metrics: {', '.join(experiment.metrics)}",
                    "Run notes:",
                    notes_block,
                ]
            ),
        ),
    ]


def _resolved_config(
    *,
    experiment: ExperimentSpec,
    dataset_entry: dict[str, Any],
    input_payload: dict[str, Any],
    acquisition: dict[str, Any],
    method_config: dict[str, Any],
    run_mode: str,
    proxy_for_benchmark: bool,
    benchmark_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "run_mode": run_mode,
        "experiment": asdict(experiment),
        "dataset_registry_entry": dataset_entry,
        "input": stringify_paths(input_payload),
        "acquisition": stringify_paths({**acquisition, "sampling_mask_mean": float(np.mean(acquisition["sampling_mask"]))}),
        "method_config": stringify_paths(method_config),
        "execution": {
            "skill_name": "mri-recon",
            "method_name": experiment.method,
            "proxy_for_benchmark": proxy_for_benchmark,
        },
    }
    if benchmark_manifest is not None:
        payload["benchmark_context"] = {
            "name": benchmark_manifest["name"],
            "version": benchmark_manifest["version"],
            "task": benchmark_manifest["task"],
        }
    return payload


def run_mri_reconstruction(
    output_dir: str | Path,
    *,
    demo: bool = False,
    input_path: str | Path | None = None,
    config_path: str | Path | None = None,
    reproduction_command: str,
    benchmark_manifest: dict[str, Any] | None = None,
) -> WorkflowResult:
    experiment: ExperimentSpec
    dataset_entry: dict[str, Any]
    measurement: np.ndarray
    reference: np.ndarray
    acquisition: dict[str, Any]
    provenance: dict[str, Any]
    method_config: dict[str, Any]
    input_payload: dict[str, Any]
    run_mode: str
    proxy_for_benchmark: bool
    summary: str

    if demo:
        experiment, dataset_entry = _mri_demo_spec(seed=19)
        case = generate_mri_demo_case(seed=experiment.seed)
        measurement = np.asarray(case["measurement"])
        reference = np.asarray(case["reference"], dtype=float)
        acquisition = dict(case["acquisition"])
        provenance = {
            "data_kind": "synthetic-measurements",
            "measurement_domain": "k-space",
            "source": "Repository-local deterministic MRI phantom and synthetic undersampled k-space.",
        }
        method_config = _method_config()
        input_payload = {
            "measurement_path": "synthetic://mri-demo-kspace/kspace",
            "reference_path": "synthetic://mri-demo-kspace/reference",
            "provenance": provenance,
        }
        run_mode = "demo"
        proxy_for_benchmark = False
        summary = (
            "Executed a deterministic zero-filled MRI baseline on synthetic undersampled k-space "
            "and emitted a structured artifact bundle with explicit sampling metadata and metrics."
        )
    elif benchmark_manifest is not None:
        experiment, dataset_entry = _mri_proxy_spec(benchmark_manifest)
        case = generate_mri_demo_case(seed=experiment.seed)
        measurement = np.asarray(case["measurement"])
        reference = np.asarray(case["reference"], dtype=float)
        acquisition = dict(case["acquisition"])
        provenance = {
            "data_kind": "synthetic-measurements",
            "measurement_domain": "k-space",
            "source": (
                "Synthetic proxy k-space generated locally because the benchmark protocol dataset "
                "was not executed directly in this smoke run."
            ),
            "proxy_for_benchmark": True,
        }
        method_config = _method_config({"proxy_generator": "deterministic-phantom"})
        input_payload = {
            "measurement_path": f"synthetic://{benchmark_manifest['name']}/mri-proxy-kspace",
            "reference_path": f"synthetic://{benchmark_manifest['name']}/mri-proxy-reference",
            "provenance": provenance,
        }
        run_mode = "benchmark-proxy"
        proxy_for_benchmark = True
        summary = (
            f"Executed the analytic MRI baseline for `{benchmark_manifest['name']}` using "
            "deterministic synthetic proxy k-space while preserving the benchmark protocol "
            "metadata separately from executed input provenance."
        )
    elif config_path is not None:
        config = _resolve_mri_config(input_path=input_path, config_path=config_path)
        measurement, reference, acquisition, provenance = _load_mri_from_config(config)
        experiment = config.experiment
        dataset_entry = config.dataset_entry.to_dict()
        method_config = _method_config(dict(config.method_config))
        input_payload = config.input_spec.to_dict()
        input_payload["provenance"] = provenance
        run_mode = "declared-config"
        proxy_for_benchmark = bool(provenance.get("proxy_for_benchmark", False))
        summary = (
            "Loaded a declared MRI experiment config, reconstructed the supplied undersampled "
            "k-space with zero-filled RSS, and emitted a provenance-heavy artifact bundle."
        )
    elif input_path is not None:
        measurement_path = Path(input_path).resolve()
        if measurement_path.suffix != ".npz":
            raise ValueError("MRI .npy inputs require --config with declared sampling metadata")
        measurement, reference, acquisition, provenance = _load_self_describing_input(measurement_path)
        _require_mri_provenance(provenance)
        experiment, dataset_entry = _mri_demo_spec(seed=19)
        method_config = _method_config()
        input_payload = {
            "measurement_path": str(measurement_path),
            "reference_path": str(measurement_path),
            "provenance": provenance,
        }
        run_mode = "self-describing-input"
        proxy_for_benchmark = bool(provenance.get("proxy_for_benchmark", False))
        summary = (
            "Loaded a self-describing MRI `.npz` input and reconstructed it with the Phase 2 "
            "analytic baseline."
        )
    else:
        raise ValueError("Provide --demo, --config, or --input.")

    mask = np.asarray(acquisition["sampling_mask"], dtype=float)
    if mask.ndim != 2:
        raise ValueError("MRI sampling_mask must be a 2D array")
    reconstruction = reconstruct_zero_filled(np.asarray(measurement))
    metric_values = compute_metrics(reference, reconstruction, experiment.metrics)

    resolved_config = _resolved_config(
        experiment=experiment,
        dataset_entry=dataset_entry,
        input_payload=input_payload,
        acquisition=acquisition,
        method_config=method_config,
        run_mode=run_mode,
        proxy_for_benchmark=proxy_for_benchmark,
        benchmark_manifest=benchmark_manifest,
    )
    environment_yaml = environment_snapshot(
        skill_name="mri-recon",
        run_mode=run_mode,
        extra={
            "coil_count": int(acquisition["coil_count"]),
            "sampling_fraction": float(np.mean(mask)),
        },
    )
    environment_digest = sha256_text(environment_yaml)

    bundle_root = init_artifact_bundle(
        output_dir,
        title=experiment.title,
        skill_name="mri-recon",
        summary=summary,
        metrics={
            "status": "completed",
            "skill": "mri-recon",
            "method": experiment.method,
            "task": experiment.task,
            "dataset": {
                "name": experiment.dataset.name,
                "version": experiment.dataset.version,
                "split": experiment.dataset.split,
                "access": experiment.dataset.access,
                "registry_data_kind": dataset_entry["data_kind"],
                "executed_data_kind": provenance["data_kind"],
                "proxy_for_benchmark": proxy_for_benchmark,
            },
            "acquisition": {
                "coil_count": int(acquisition["coil_count"]),
                "sampling_fraction": float(np.mean(mask)),
            },
            "metrics": metric_values,
            "environment_digest": environment_digest,
        },
        config_yaml=yaml.safe_dump(stringify_paths(resolved_config), sort_keys=False),
        report_sections=_report_sections(
            experiment=experiment,
            dataset_entry=dataset_entry,
            acquisition=acquisition,
            provenance=provenance,
            metric_values=metric_values,
            environment_digest=environment_digest,
            proxy_for_benchmark=proxy_for_benchmark,
            run_mode=run_mode,
        ),
        commands=render_commands(reproduction_command),
        analysis_log=render_analysis_log(
            [
                f"Run mode: {run_mode}",
                f"Dataset protocol: {experiment.dataset.name}@{experiment.dataset.version}",
                f"Coil count: {int(acquisition['coil_count'])}",
                f"Sampling fraction: {float(np.mean(mask)):.4f}",
                f"Proxy for benchmark: {proxy_for_benchmark}",
                f"Environment digest: {environment_digest}",
            ]
        ),
        environment_yaml=environment_yaml,
    )

    np.save(bundle_root / "figures" / "measurement.npy", measurement)
    np.save(bundle_root / "figures" / "reference.npy", reference)
    np.save(bundle_root / "figures" / "reconstruction.npy", reconstruction)
    np.save(bundle_root / "figures" / "sampling_mask.npy", mask)
    write_tsv(
        bundle_root / "tables" / "metrics.tsv",
        headers=["metric", "value"],
        rows=[[metric_name, f"{metric_value:.6f}"] for metric_name, metric_value in metric_values.items()],
    )
    finalize_bundle(bundle_root)

    return WorkflowResult(
        bundle_path=bundle_root,
        skill_name="mri-recon",
        method_name=experiment.method,
        title=experiment.title,
        summary=summary,
        metrics={
            "metrics": metric_values,
            "environment_digest": environment_digest,
            "proxy_for_benchmark": proxy_for_benchmark,
        },
        resolved_config=resolved_config,
        proxy_for_benchmark=proxy_for_benchmark,
    )
