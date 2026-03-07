from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from ..artifacts import init_artifact_bundle, sha256_text
from ..datasets import get_dataset_entry
from ..experiments import ExperimentRunConfig, load_experiment_config
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


DEFAULT_CT_METHOD = "fbp"
DEMO_DATASET_NAME = "ct-demo-phantoms"
DEMO_DATASET_VERSION = "0.1"


def _grid(size: int) -> tuple[np.ndarray, np.ndarray]:
    axis = np.linspace(-1.0, 1.0, size)
    x = np.repeat(axis[None, :], size, axis=0)
    y = np.repeat(axis[:, None], size, axis=1)
    return x, y


def _ellipse(
    x: np.ndarray,
    y: np.ndarray,
    *,
    center_x: float,
    center_y: float,
    axis_x: float,
    axis_y: float,
    angle_deg: float,
    amplitude: float,
) -> np.ndarray:
    theta = np.deg2rad(angle_deg)
    x_shifted = x - center_x
    y_shifted = y - center_y
    x_rotated = x_shifted * np.cos(theta) + y_shifted * np.sin(theta)
    y_rotated = -x_shifted * np.sin(theta) + y_shifted * np.cos(theta)
    mask = (x_rotated / axis_x) ** 2 + (y_rotated / axis_y) ** 2 <= 1.0
    return np.asarray(amplitude * mask.astype(float), dtype=float)


def build_ct_phantom(size: int = 64) -> np.ndarray:
    x, y = _grid(size)
    phantom = np.zeros((size, size), dtype=float)
    phantom += _ellipse(
        x,
        y,
        center_x=0.0,
        center_y=0.0,
        axis_x=0.82,
        axis_y=0.98,
        angle_deg=0.0,
        amplitude=0.65,
    )
    phantom += _ellipse(
        x,
        y,
        center_x=0.0,
        center_y=-0.02,
        axis_x=0.72,
        axis_y=0.88,
        angle_deg=0.0,
        amplitude=-0.18,
    )
    phantom += _ellipse(
        x,
        y,
        center_x=-0.22,
        center_y=0.0,
        axis_x=0.12,
        axis_y=0.32,
        angle_deg=18.0,
        amplitude=0.18,
    )
    phantom += _ellipse(
        x,
        y,
        center_x=0.24,
        center_y=-0.1,
        axis_x=0.18,
        axis_y=0.22,
        angle_deg=-12.0,
        amplitude=0.12,
    )
    phantom += _ellipse(
        x,
        y,
        center_x=0.0,
        center_y=0.34,
        axis_x=0.28,
        axis_y=0.09,
        angle_deg=0.0,
        amplitude=0.1,
    )
    return np.asarray(np.clip(phantom, 0.0, 1.0), dtype=float)


def _bilinear_sample(image: np.ndarray, y_coords: np.ndarray, x_coords: np.ndarray) -> np.ndarray:
    height, width = image.shape
    x0 = np.floor(x_coords).astype(int)
    y0 = np.floor(y_coords).astype(int)
    x1 = x0 + 1
    y1 = y0 + 1

    x0_clipped = np.clip(x0, 0, width - 1)
    x1_clipped = np.clip(x1, 0, width - 1)
    y0_clipped = np.clip(y0, 0, height - 1)
    y1_clipped = np.clip(y1, 0, height - 1)

    wa = (x1 - x_coords) * (y1 - y_coords)
    wb = (x_coords - x0) * (y1 - y_coords)
    wc = (x1 - x_coords) * (y_coords - y0)
    wd = (x_coords - x0) * (y_coords - y0)

    sampled = (
        wa * image[y0_clipped, x0_clipped]
        + wb * image[y0_clipped, x1_clipped]
        + wc * image[y1_clipped, x0_clipped]
        + wd * image[y1_clipped, x1_clipped]
    )
    valid = (
        (x_coords >= 0.0)
        & (x_coords <= width - 1)
        & (y_coords >= 0.0)
        & (y_coords <= height - 1)
    )
    return np.where(valid, sampled, 0.0)


def _rotate_image(image: np.ndarray, angle_deg: float) -> np.ndarray:
    height, width = image.shape
    y_coords, x_coords = np.indices((height, width), dtype=float)
    center_y = (height - 1) / 2.0
    center_x = (width - 1) / 2.0
    y_shifted = y_coords - center_y
    x_shifted = x_coords - center_x

    theta = np.deg2rad(angle_deg)
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    source_x = cos_theta * x_shifted + sin_theta * y_shifted + center_x
    source_y = -sin_theta * x_shifted + cos_theta * y_shifted + center_y
    return _bilinear_sample(image, source_y, source_x)


def radon_transform(image: np.ndarray, angles_degrees: np.ndarray) -> np.ndarray:
    projections = []
    for angle in angles_degrees:
        projections.append(np.sum(_rotate_image(image, float(angle)), axis=0))
    return np.asarray(projections, dtype=float)


def _ramp_filter(sinogram: np.ndarray) -> np.ndarray:
    detector_count = sinogram.shape[1]
    frequencies = np.fft.fftfreq(detector_count)
    ramp = 2.0 * np.abs(frequencies)
    filtered = np.fft.ifft(np.fft.fft(sinogram, axis=1) * ramp[None, :], axis=1)
    return np.real(filtered)


def filtered_backprojection(sinogram: np.ndarray, angles_degrees: np.ndarray) -> np.ndarray:
    detector_count = sinogram.shape[1]
    filtered = _ramp_filter(sinogram)
    reconstruction = np.zeros((detector_count, detector_count), dtype=float)
    for angle, projection in zip(angles_degrees, filtered):
        tiled_projection = np.repeat(projection[None, :], detector_count, axis=0)
        reconstruction += _rotate_image(tiled_projection, -float(angle))
    reconstruction *= np.pi / max(1, len(angles_degrees))
    return np.clip(reconstruction, 0.0, None)


def generate_ct_demo_case(
    *,
    seed: int,
    size: int = 64,
    angle_count: int = 45,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    reference = build_ct_phantom(size=size)
    angles_degrees = np.linspace(0.0, 180.0, angle_count, endpoint=False)
    noiseless_sinogram = radon_transform(reference, angles_degrees)
    normalized_sinogram = noiseless_sinogram / max(float(np.max(noiseless_sinogram)), 1.0) * 1.6
    intensity_scale = 12_000.0
    counts = rng.poisson(intensity_scale * np.exp(-normalized_sinogram))
    measurement = -np.log(np.clip(counts, 1.0, None) / intensity_scale)
    return {
        "measurement": measurement.astype(float),
        "reference": reference.astype(float),
        "acquisition": {
            "angles_degrees": angles_degrees.tolist(),
            "detector_count": int(measurement.shape[1]),
            "intensity_scale": intensity_scale,
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
    required = {"measurement", "reference", "angles_degrees", "provenance_json"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(
            f"Self-describing CT input {path} missing required fields: {', '.join(missing)}"
        )
    provenance = json.loads(str(payload["provenance_json"].item()))
    acquisition = {"angles_degrees": payload["angles_degrees"].astype(float).tolist()}
    return (
        np.asarray(payload["measurement"], dtype=float),
        np.asarray(payload["reference"], dtype=float),
        acquisition,
        provenance,
    )


def _require_ct_provenance(provenance: dict[str, Any]) -> None:
    required_fields = ("data_kind", "measurement_domain", "source")
    missing = [
        field_name
        for field_name in required_fields
        if not str(provenance.get(field_name, "")).strip()
    ]
    if missing:
        raise ValueError("CT provenance missing required fields: " + ", ".join(missing))


def _resolve_ct_config(
    *,
    input_path: str | Path | None,
    config_path: str | Path,
) -> ExperimentRunConfig:
    config = load_experiment_config(config_path)
    if input_path is not None:
        config = config.override_measurement_path(input_path)
    return config


def _validate_ct_config(config: ExperimentRunConfig) -> None:
    if config.experiment.modality != "ct":
        raise ValueError("CT workflow requires experiment.modality to be 'ct'")
    if config.experiment.method.lower() != DEFAULT_CT_METHOD:
        raise ValueError(f"CT Phase 2 supports only the `{DEFAULT_CT_METHOD}` baseline")
    if "angles_degrees" not in config.acquisition:
        raise ValueError("CT acquisition metadata must declare angles_degrees")
    _require_ct_provenance(config.input_spec.provenance)


def _load_ct_from_config(
    config: ExperimentRunConfig,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any], dict[str, Any]]:
    _validate_ct_config(config)
    measurement_path = config.input_spec.measurement_path
    if measurement_path.suffix == ".npy":
        if config.input_spec.reference_path is None:
            raise ValueError("CT config runs require input.reference_path for metrics")
        return (
            _array_from_npy(measurement_path).astype(float),
            _array_from_npy(config.input_spec.reference_path).astype(float),
            dict(config.acquisition),
            dict(config.input_spec.provenance),
        )
    if measurement_path.suffix == ".npz":
        measurement, reference, acquisition, provenance = _load_self_describing_input(measurement_path)
        if config.input_spec.reference_path is not None:
            reference = _array_from_npy(config.input_spec.reference_path).astype(float)
        return measurement, reference, {**acquisition, **dict(config.acquisition)}, {
            **provenance,
            **dict(config.input_spec.provenance),
        }
    raise ValueError("CT input must be a .npy or .npz file")


def _ct_experiment(
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
    dataset_entry = get_dataset_entry(dataset_name, dataset_version)
    experiment = ExperimentSpec(
        experiment_id=experiment_id,
        title=title,
        modality="ct",
        task=task,
        dataset=DatasetRef(
            name=dataset_name,
            version=dataset_version,
            split=split,
            access=access,
        ),
        forward_model=ForwardModelSpec(
            operator="x-ray-transform",
            geometry="parallel-beam",
            noise_model="poisson-count-proxy",
        ),
        method=DEFAULT_CT_METHOD,
        metrics=metrics,
        seed=seed,
        hardware={"reference_device": "cpu"},
        notes=notes,
    )
    experiment.validate_against_dataset(dataset_entry)
    return experiment, dataset_entry.to_dict()


def _ct_demo_spec(*, seed: int) -> tuple[ExperimentSpec, dict[str, Any]]:
    return _ct_experiment(
        experiment_id="ct-demo-fbp",
        title="Synthetic CT FBP smoke run",
        dataset_name=DEMO_DATASET_NAME,
        dataset_version=DEMO_DATASET_VERSION,
        split="synthetic-smoke",
        access="open",
        task="synthetic-ct-reconstruction",
        metrics=["psnr", "ssim", "nrmse"],
        seed=seed,
        notes=["Repository-local synthetic CT demo."],
    )


def _ct_proxy_spec(benchmark_manifest: dict[str, Any]) -> tuple[ExperimentSpec, dict[str, Any]]:
    dataset = dict(benchmark_manifest["dataset"])
    return _ct_experiment(
        experiment_id=f"{benchmark_manifest['name']}-fbp-proxy",
        title=f"Proxy CT baseline for {benchmark_manifest['name']}",
        dataset_name=str(dataset["name"]),
        dataset_version=str(dataset["version"]),
        split=str(dataset["split"]),
        access=str(dataset["access"]),
        task=str(benchmark_manifest["task"]),
        metrics=[str(metric) for metric in benchmark_manifest["metrics"]],
        seed=int(benchmark_manifest["seeds"]["eval"]),
        notes=[
            "Benchmark protocol resolved against the registry.",
            "Executed with synthetic proxy sinograms rather than the upstream benchmark dataset.",
        ],
    )


def _method_config(method_config: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {"filter": "ramp", "clip_min": 0.0}
    if method_config:
        payload.update(method_config)
    if str(payload["filter"]).lower() != "ramp":
        raise ValueError("CT Phase 2 supports only the `ramp` FBP filter")
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
                    f"- Angle count: `{len(acquisition['angles_degrees'])}`",
                    f"- Detector count: `{acquisition.get('detector_count', 'derived-from-measurement')}`",
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
        "acquisition": stringify_paths(acquisition),
        "method_config": stringify_paths(method_config),
        "execution": {
            "skill_name": "ct-recon",
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


def run_ct_reconstruction(
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
        experiment, dataset_entry = _ct_demo_spec(seed=11)
        case = generate_ct_demo_case(seed=experiment.seed)
        measurement = np.asarray(case["measurement"], dtype=float)
        reference = np.asarray(case["reference"], dtype=float)
        acquisition = dict(case["acquisition"])
        provenance = {
            "data_kind": "synthetic-measurements",
            "measurement_domain": "sinogram",
            "source": "Repository-local deterministic CT phantom and proxy low-dose sinogram.",
        }
        method_config = _method_config()
        input_payload = {
            "measurement_path": "synthetic://ct-demo-phantoms/sinogram",
            "reference_path": "synthetic://ct-demo-phantoms/reference",
            "provenance": provenance,
        }
        run_mode = "demo"
        proxy_for_benchmark = False
        summary = (
            "Executed a deterministic FBP baseline on a synthetic CT phantom and emitted a "
            "structured artifact bundle with explicit acquisition metadata and metrics."
        )
    elif benchmark_manifest is not None:
        experiment, dataset_entry = _ct_proxy_spec(benchmark_manifest)
        case = generate_ct_demo_case(seed=experiment.seed)
        measurement = np.asarray(case["measurement"], dtype=float)
        reference = np.asarray(case["reference"], dtype=float)
        acquisition = dict(case["acquisition"])
        provenance = {
            "data_kind": "synthetic-measurements",
            "measurement_domain": "sinogram",
            "source": (
                "Synthetic proxy sinogram generated locally because the benchmark protocol dataset "
                "was not executed directly in this smoke run."
            ),
            "proxy_for_benchmark": True,
        }
        method_config = _method_config({"proxy_generator": "deterministic-phantom"})
        input_payload = {
            "measurement_path": f"synthetic://{benchmark_manifest['name']}/ct-proxy-sinogram",
            "reference_path": f"synthetic://{benchmark_manifest['name']}/ct-proxy-reference",
            "provenance": provenance,
        }
        run_mode = "benchmark-proxy"
        proxy_for_benchmark = True
        summary = (
            f"Executed the analytic CT baseline for `{benchmark_manifest['name']}` using "
            "deterministic synthetic proxy sinograms while preserving the benchmark protocol "
            "metadata separately from executed input provenance."
        )
    elif config_path is not None:
        config = _resolve_ct_config(input_path=input_path, config_path=config_path)
        measurement, reference, acquisition, provenance = _load_ct_from_config(config)
        experiment = config.experiment
        dataset_entry = config.dataset_entry.to_dict()
        method_config = _method_config(dict(config.method_config))
        input_payload = config.input_spec.to_dict()
        input_payload["provenance"] = provenance
        run_mode = "declared-config"
        proxy_for_benchmark = bool(provenance.get("proxy_for_benchmark", False))
        summary = (
            "Loaded a declared CT experiment config, reconstructed the supplied sinogram with "
            "FBP, and emitted a provenance-heavy artifact bundle."
        )
    elif input_path is not None:
        measurement_path = Path(input_path).resolve()
        if measurement_path.suffix != ".npz":
            raise ValueError("CT .npy inputs require --config with declared geometry and provenance")
        measurement, reference, acquisition, provenance = _load_self_describing_input(measurement_path)
        _require_ct_provenance(provenance)
        experiment, dataset_entry = _ct_demo_spec(seed=11)
        method_config = _method_config()
        input_payload = {
            "measurement_path": str(measurement_path),
            "reference_path": str(measurement_path),
            "provenance": provenance,
        }
        run_mode = "self-describing-input"
        proxy_for_benchmark = bool(provenance.get("proxy_for_benchmark", False))
        summary = (
            "Loaded a self-describing CT `.npz` input and reconstructed it with the Phase 2 "
            "analytic baseline."
        )
    else:
        raise ValueError("Provide --demo, --config, or --input.")

    angles_degrees = np.asarray(acquisition.get("angles_degrees"), dtype=float)
    if angles_degrees.ndim != 1 or angles_degrees.size == 0:
        raise ValueError("CT acquisition metadata must provide a non-empty angles_degrees list")

    reconstruction = filtered_backprojection(measurement, angles_degrees)
    reconstruction = np.maximum(reconstruction, float(method_config["clip_min"]))
    metric_values = compute_metrics(reference, reconstruction, experiment.metrics)

    resolved_config = _resolved_config(
        experiment=experiment,
        dataset_entry=dataset_entry,
        input_payload=input_payload,
        acquisition={**acquisition, "angles_degrees": angles_degrees.tolist()},
        method_config=method_config,
        run_mode=run_mode,
        proxy_for_benchmark=proxy_for_benchmark,
        benchmark_manifest=benchmark_manifest,
    )
    environment_yaml = environment_snapshot(
        skill_name="ct-recon",
        run_mode=run_mode,
        extra={
            "angle_count": int(angles_degrees.size),
            "detector_count": int(measurement.shape[1]),
        },
    )
    environment_digest = sha256_text(environment_yaml)

    bundle_root = init_artifact_bundle(
        output_dir,
        title=experiment.title,
        skill_name="ct-recon",
        summary=summary,
        metrics={
            "status": "completed",
            "skill": "ct-recon",
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
                "angle_count": int(angles_degrees.size),
                "detector_count": int(measurement.shape[1]),
            },
            "metrics": metric_values,
            "environment_digest": environment_digest,
        },
        config_yaml=yaml.safe_dump(stringify_paths(resolved_config), sort_keys=False),
        report_sections=_report_sections(
            experiment=experiment,
            dataset_entry=dataset_entry,
            acquisition={**acquisition, "angles_degrees": angles_degrees.tolist()},
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
                f"Angle count: {int(angles_degrees.size)}",
                f"Detector count: {int(measurement.shape[1])}",
                f"Proxy for benchmark: {proxy_for_benchmark}",
                f"Environment digest: {environment_digest}",
            ]
        ),
        environment_yaml=environment_yaml,
    )

    np.save(bundle_root / "figures" / "measurement.npy", measurement)
    np.save(bundle_root / "figures" / "reference.npy", reference)
    np.save(bundle_root / "figures" / "reconstruction.npy", reconstruction)
    write_tsv(
        bundle_root / "tables" / "metrics.tsv",
        headers=["metric", "value"],
        rows=[[metric_name, f"{metric_value:.6f}"] for metric_name, metric_value in metric_values.items()],
    )
    finalize_bundle(bundle_root)

    return WorkflowResult(
        bundle_path=bundle_root,
        skill_name="ct-recon",
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
