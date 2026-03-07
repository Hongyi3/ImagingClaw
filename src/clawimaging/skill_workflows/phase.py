from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from ..artifacts import init_artifact_bundle, sha256_text
from ..datasets import get_dataset_entry
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


DEFAULT_PHASE_METHOD = "gerchberg-saxton"
DEMO_DATASET_NAME = "synthetic-phase-objects"
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


def _grid(size: int) -> tuple[np.ndarray, np.ndarray]:
    axis = np.linspace(-1.0, 1.0, size)
    x, y = np.meshgrid(axis, axis, indexing="xy")
    return np.asarray(x, dtype=float), np.asarray(y, dtype=float)


def build_support_mask(size: int = 64) -> np.ndarray:
    x, y = _grid(size)
    radial = np.sqrt(x ** 2 + y ** 2)
    support = radial <= 0.82
    support &= np.abs(x) <= 0.9
    support &= np.abs(y) <= 0.9
    return support.astype(float)


def build_phase_map(size: int = 64) -> np.ndarray:
    x, y = _grid(size)
    phase = (
        0.52 * np.exp(-((x + 0.32) ** 2 + (y - 0.18) ** 2) / 0.09)
        - 0.44 * np.exp(-((x - 0.24) ** 2 + (y + 0.12) ** 2) / 0.07)
        + 0.18 * np.sin(np.pi * x) * np.cos(1.5 * np.pi * y)
    )
    return np.asarray(np.clip(phase, -0.9, 0.9), dtype=float)


def generate_phase_demo_case(
    *,
    seed: int,
    size: int = 64,
    noise_std: float = 0.0,
) -> dict[str, Any]:
    support = build_support_mask(size=size)
    reference_phase = build_phase_map(size=size) * support
    reference_object = support * np.exp(1j * reference_phase)
    measurement = np.abs(_fft2c(reference_object))
    if noise_std > 0.0:
        rng = np.random.default_rng(seed)
        measurement = np.clip(
            measurement + rng.normal(loc=0.0, scale=noise_std, size=measurement.shape),
            a_min=0.0,
            a_max=None,
        )
    return {
        "measurement": measurement.astype(float),
        "reference_phase": reference_phase.astype(float),
        "support": support.astype(float),
        "acquisition": {
            "support_fraction": float(np.mean(support)),
            "centered_fft": True,
            "object_type": "pure-phase",
            "noise_std": float(noise_std),
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


def _load_self_describing_input(
    path: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    payload = _load_npz_payload(path)
    required = {"measurement", "reference_phase", "support", "provenance_json"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(
            f"Self-describing phase input {path} missing required fields: {', '.join(missing)}"
        )
    provenance = json.loads(str(payload["provenance_json"].item()))
    return (
        np.asarray(payload["measurement"], dtype=float),
        np.asarray(payload["reference_phase"], dtype=float),
        np.asarray(payload["support"], dtype=float),
        provenance,
    )


def _require_phase_provenance(provenance: dict[str, Any]) -> None:
    required_fields = ("data_kind", "measurement_domain", "source")
    missing = [
        field_name
        for field_name in required_fields
        if not str(provenance.get(field_name, "")).strip()
    ]
    if missing:
        raise ValueError("Phase provenance missing required fields: " + ", ".join(missing))


def _resolve_support(config: ExperimentRunConfig) -> np.ndarray:
    if "support_path" in config.acquisition:
        support_path = resolve_support_path(
            str(config.acquisition["support_path"]),
            base_dir=config.source_path.parent,
        )
        return _array_from_npy(support_path).astype(float)
    if "support" in config.acquisition:
        return np.asarray(config.acquisition["support"], dtype=float)
    raise ValueError("Phase acquisition metadata must declare support_path or support")


def _resolve_phase_config(
    *,
    input_path: str | Path | None,
    config_path: str | Path,
) -> ExperimentRunConfig:
    config = load_experiment_config(config_path)
    if input_path is not None:
        config = config.override_measurement_path(input_path)
    return config


def _validate_phase_config(config: ExperimentRunConfig) -> None:
    if config.experiment.modality != "coherent-imaging":
        raise ValueError("Phase workflow requires experiment.modality to be 'coherent-imaging'")
    if config.experiment.method.lower() != DEFAULT_PHASE_METHOD:
        raise ValueError(
            f"Phase workflow supports only the `{DEFAULT_PHASE_METHOD}` baseline"
        )
    _require_phase_provenance(config.input_spec.provenance)
    _ = _resolve_support(config)


def _load_phase_from_config(
    config: ExperimentRunConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any], dict[str, Any]]:
    _validate_phase_config(config)
    measurement_path = config.input_spec.measurement_path
    if measurement_path.suffix == ".npy":
        if config.input_spec.reference_path is None:
            raise ValueError("Phase config runs require input.reference_path for metrics")
        support = _resolve_support(config)
        return (
            _array_from_npy(measurement_path).astype(float),
            _array_from_npy(config.input_spec.reference_path).astype(float),
            support,
            dict(config.acquisition),
            dict(config.input_spec.provenance),
        )
    if measurement_path.suffix == ".npz":
        measurement, reference_phase, support, provenance = _load_self_describing_input(
            measurement_path
        )
        if config.input_spec.reference_path is not None:
            reference_phase = _array_from_npy(config.input_spec.reference_path).astype(float)
        acquisition = dict(config.acquisition)
        if "support_path" in acquisition:
            support = _resolve_support(config)
        return (
            measurement,
            reference_phase,
            support,
            acquisition,
            {**provenance, **dict(config.input_spec.provenance)},
        )
    raise ValueError("Phase input must be a .npy or .npz file")


def _phase_experiment(
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
    noise_model: str,
) -> tuple[ExperimentSpec, dict[str, Any]]:
    dataset_entry = get_dataset_entry(dataset_name, dataset_version)
    experiment = ExperimentSpec(
        experiment_id=experiment_id,
        title=title,
        modality="coherent-imaging",
        task=task,
        dataset=DatasetRef(
            name=dataset_name,
            version=dataset_version,
            split=split,
            access=access,
        ),
        forward_model=ForwardModelSpec(
            operator="magnitude-of-fourier-transform",
            geometry="planar",
            noise_model=noise_model,
        ),
        method=DEFAULT_PHASE_METHOD,
        metrics=metrics,
        seed=seed,
        hardware={"reference_device": "cpu"},
        notes=notes,
    )
    experiment.validate_against_dataset(dataset_entry)
    return experiment, dataset_entry.to_dict()


def _phase_demo_spec(*, seed: int) -> tuple[ExperimentSpec, dict[str, Any]]:
    return _phase_experiment(
        experiment_id="phase-demo-gerchberg-saxton",
        title="Synthetic coherent-imaging Gerchberg-Saxton smoke run",
        dataset_name=DEMO_DATASET_NAME,
        dataset_version=DEMO_DATASET_VERSION,
        split="synthetic-smoke",
        access="open",
        task="fourier-phase-retrieval",
        metrics=["relative-error", "psnr", "ssim"],
        seed=seed,
        notes=["Repository-local synthetic phase retrieval demo."],
        noise_model="noiseless-synthetic",
    )


def _phase_benchmark_spec(
    benchmark_manifest: dict[str, Any],
) -> tuple[ExperimentSpec, dict[str, Any]]:
    dataset = dict(benchmark_manifest["dataset"])
    return _phase_experiment(
        experiment_id=f"{benchmark_manifest['name']}-gerchberg-saxton",
        title=f"Gerchberg-Saxton baseline for {benchmark_manifest['name']}",
        dataset_name=str(dataset["name"]),
        dataset_version=str(dataset["version"]),
        split=str(dataset["split"]),
        access=str(dataset["access"]),
        task=str(benchmark_manifest["task"]),
        metrics=[str(metric) for metric in benchmark_manifest["metrics"]],
        seed=int(benchmark_manifest["seeds"]["eval"]),
        notes=[
            "Benchmark protocol resolved against the registry.",
            "Executed directly against the repository-local synthetic coherent-imaging benchmark.",
        ],
        noise_model=str(benchmark_manifest["forward_model"]["noise_model"]),
    )


def _method_config(method_config: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "iterations": 48,
        "initialization": "random-phase",
        "enforce_unit_amplitude": True,
    }
    if method_config:
        payload.update(method_config)
    payload["iterations"] = int(payload["iterations"])
    if payload["iterations"] <= 0:
        raise ValueError("Phase retrieval iterations must be positive")
    payload["initialization"] = str(payload["initialization"]).strip().lower()
    if payload["initialization"] != "random-phase":
        raise ValueError("Phase workflow supports only random-phase initialization")
    payload["enforce_unit_amplitude"] = bool(payload["enforce_unit_amplitude"])
    return payload


def _validate_shapes(
    *,
    measurement: np.ndarray,
    reference_phase: np.ndarray,
    support: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    measurement_array = np.asarray(measurement, dtype=float)
    reference_array = np.asarray(reference_phase, dtype=float)
    support_array = np.asarray(support, dtype=float)
    if measurement_array.shape != reference_array.shape or measurement_array.shape != support_array.shape:
        raise ValueError("Phase measurement, reference phase, and support must share the same shape")
    if measurement_array.ndim != 2:
        raise ValueError("Phase workflow requires 2D arrays")
    return measurement_array, reference_array, support_array


def reconstruct_gerchberg_saxton(
    measurement: np.ndarray,
    support: np.ndarray,
    *,
    iterations: int,
    seed: int,
    enforce_unit_amplitude: bool,
) -> tuple[np.ndarray, dict[str, float]]:
    rng = np.random.default_rng(seed)
    support_mask = support > 0.5
    estimate = np.where(
        support_mask,
        np.exp(1j * rng.uniform(-np.pi, np.pi, size=measurement.shape)),
        0.0,
    ).astype(np.complex128)

    for _ in range(iterations):
        spectrum = _fft2c(estimate)
        spectrum = measurement * np.exp(1j * np.angle(spectrum))
        estimate = _ifft2c(spectrum)
        estimate = np.where(support_mask, estimate, 0.0)
        if enforce_unit_amplitude:
            estimate = np.where(
                support_mask,
                np.exp(1j * np.angle(estimate)),
                0.0,
            )

    measurement_norm = float(np.linalg.norm(measurement))
    if measurement_norm == 0.0:
        measurement_norm = 1e-12
    measurement_residual = float(
        np.linalg.norm(np.abs(_fft2c(estimate)) - measurement) / measurement_norm
    )
    return estimate, {
        "measurement_residual": measurement_residual,
        "support_fraction": float(np.mean(support_mask)),
    }


def _align_global_phase(
    reference_phase: np.ndarray,
    estimate: np.ndarray,
    support: np.ndarray,
) -> np.ndarray:
    reference_object = support * np.exp(1j * reference_phase)
    mask = support > 0.5
    correlation = np.vdot(reference_object[mask], estimate[mask])
    if correlation == 0.0:
        return estimate
    return np.asarray(
        estimate * np.exp(-1j * float(np.angle(correlation))),
        dtype=np.complex128,
    )


def _report_sections(
    *,
    experiment: ExperimentSpec,
    dataset_entry: dict[str, Any],
    acquisition: dict[str, Any],
    provenance: dict[str, Any],
    method_config: dict[str, Any],
    metric_values: dict[str, float],
    diagnostics: dict[str, float],
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
            "Forward Model Assumptions",
            "\n".join(
                [
                    f"- Operator: `{experiment.forward_model.operator}`",
                    f"- Geometry: `{experiment.forward_model.geometry}`",
                    f"- Noise model: `{experiment.forward_model.noise_model}`",
                    f"- Centered FFT: `{acquisition.get('centered_fft', True)}`",
                    f"- Object model: `{acquisition.get('object_type', 'pure-phase')}`",
                ]
            ),
        ),
        (
            "Priors",
            "\n".join(
                [
                    f"- Binary support supplied: `{True}`",
                    f"- Support fraction: {diagnostics['support_fraction']:.4f}",
                    f"- Enforce unit amplitude: `{method_config['enforce_unit_amplitude']}`",
                    f"- Initialization: `{method_config['initialization']}`",
                    f"- Notes:\n{notes_block}",
                ]
            ),
        ),
        (
            "Optical Diagnostics",
            "\n".join(
                [
                    f"- Gerchberg-Saxton iterations: {method_config['iterations']}",
                    f"- Measurement residual: {diagnostics['measurement_residual']:.6f}",
                    f"- Support energy leakage: {diagnostics['support_leakage']:.6f}",
                ]
            ),
        ),
        (
            "Metrics",
            format_bullets(
                [f"{metric_name}: {metric_value:.6f}" for metric_name, metric_value in metric_values.items()]
            ),
        ),
        (
            "Reproducibility Notes",
            "\n".join(
                [
                    f"- Environment digest: `{environment_digest}`",
                    f"- Dataset card: `{dataset_entry['card']}`",
                    "- Global phase was aligned before phase-domain metric evaluation.",
                ]
            ),
        ),
    ]


def run_phase_retrieval(
    output_dir: str | Path,
    *,
    demo: bool = False,
    input_path: str | Path | None = None,
    config_path: str | Path | None = None,
    benchmark_manifest: dict[str, Any] | None = None,
    reproduction_command: str,
) -> WorkflowResult:
    run_mode = "demo" if demo else "declared-config"
    proxy_for_benchmark = False

    if benchmark_manifest is not None:
        run_mode = "benchmark"
        experiment, dataset_entry = _phase_benchmark_spec(benchmark_manifest)
        noise_std = 0.01 if experiment.forward_model.noise_model == "gaussian" else 0.0
        demo_case = generate_phase_demo_case(seed=experiment.seed, noise_std=noise_std)
        measurement = np.asarray(demo_case["measurement"], dtype=float)
        reference_phase = np.asarray(demo_case["reference_phase"], dtype=float)
        support = np.asarray(demo_case["support"], dtype=float)
        acquisition = {
            **dict(demo_case["acquisition"]),
            "benchmark_name": benchmark_manifest["name"],
        }
        provenance = {
            "data_kind": "synthetic-measurements",
            "measurement_domain": "fourier-magnitude",
            "source": "Repository-local synthetic coherent-imaging benchmark data.",
        }
        method_config = _method_config()
    elif demo:
        experiment, dataset_entry = _phase_demo_spec(seed=37)
        demo_case = generate_phase_demo_case(seed=experiment.seed)
        measurement = np.asarray(demo_case["measurement"], dtype=float)
        reference_phase = np.asarray(demo_case["reference_phase"], dtype=float)
        support = np.asarray(demo_case["support"], dtype=float)
        acquisition = dict(demo_case["acquisition"])
        provenance = {
            "data_kind": "synthetic-measurements",
            "measurement_domain": "fourier-magnitude",
            "source": "Repository-local synthetic coherent-imaging smoke data.",
        }
        method_config = _method_config()
    elif config_path is not None:
        config = _resolve_phase_config(input_path=input_path, config_path=config_path)
        measurement, reference_phase, support, acquisition, provenance = _load_phase_from_config(
            config
        )
        experiment = config.experiment
        dataset_entry = config.dataset_entry.to_dict()
        method_config = _method_config(config.method_config)
    elif input_path is not None:
        measurement_path = Path(input_path).resolve()
        if measurement_path.suffix != ".npz":
            raise ValueError(
                "Phase .npy inputs require --config with declared support and provenance metadata"
            )
        measurement, reference_phase, support, provenance = _load_self_describing_input(
            measurement_path
        )
        _require_phase_provenance(provenance)
        experiment, dataset_entry = _phase_demo_spec(seed=23)
        acquisition = {
            "support_fraction": float(np.mean(support > 0.5)),
            "centered_fft": True,
            "object_type": "pure-phase",
        }
        method_config = _method_config()
        run_mode = "self-describing-input"
    else:
        raise ValueError("Provide --demo, --config, or --input.")

    measurement, reference_phase, support = _validate_shapes(
        measurement=measurement,
        reference_phase=reference_phase,
        support=support,
    )
    _require_phase_provenance(provenance)

    reconstruction, base_diagnostics = reconstruct_gerchberg_saxton(
        measurement,
        support,
        iterations=int(method_config["iterations"]),
        seed=int(experiment.seed),
        enforce_unit_amplitude=bool(method_config["enforce_unit_amplitude"]),
    )
    aligned_reconstruction = _align_global_phase(reference_phase, reconstruction, support)
    support_mask = support > 0.5
    reconstructed_phase = np.where(support_mask, np.angle(aligned_reconstruction), 0.0)
    masked_reference = np.where(support_mask, reference_phase, 0.0)
    masked_reconstruction = np.where(support_mask, reconstructed_phase, 0.0)
    reconstruction_norm = float(np.linalg.norm(aligned_reconstruction))
    if reconstruction_norm == 0.0:
        reconstruction_norm = 1e-12
    support_leakage = float(
        np.linalg.norm(aligned_reconstruction[~support_mask]) / reconstruction_norm
    )
    diagnostics = {
        **base_diagnostics,
        "support_leakage": support_leakage,
    }
    metric_values = compute_metrics(masked_reference, masked_reconstruction, experiment.metrics)

    environment_yaml = environment_snapshot(
        skill_name="phase-retrieve",
        run_mode=run_mode,
        extra={
            "dataset": f"{experiment.dataset.name}@{experiment.dataset.version}",
            "method": experiment.method,
            "iterations": method_config["iterations"],
            "measurement_domain": provenance["measurement_domain"],
        },
    )
    environment_digest = sha256_text(environment_yaml)
    summary = (
        "Recovered a pure-phase object estimate from magnitude-only Fourier measurements using "
        "a deterministic Gerchberg-Saxton baseline with explicit support and forward-model "
        "assumptions."
    )
    resolved_config = {
        "experiment": experiment.to_dict(),
        "dataset_registry_entry": dataset_entry,
        "input": {
            "measurement_path": str(input_path) if input_path is not None else None,
            "provenance": provenance,
        },
        "acquisition": {
            **acquisition,
            "support": support.astype(float),
        },
        "method_config": method_config,
        "metrics": metric_values,
        "optical_diagnostics": diagnostics,
        "environment_digest": environment_digest,
    }
    if config_path is not None:
        resolved_config["config_path"] = str(Path(config_path).resolve())
    if benchmark_manifest is not None:
        resolved_config["benchmark_manifest"] = benchmark_manifest

    bundle_root = Path(output_dir).resolve()
    init_artifact_bundle(
        bundle_root,
        title=experiment.title,
        skill_name="phase-retrieve",
        summary=summary,
        metrics={
            "status": "completed",
            "skill": "phase-retrieve",
            "run_mode": run_mode,
            "metrics": metric_values,
            "optical_diagnostics": diagnostics,
            "environment_digest": environment_digest,
            "proxy_for_benchmark": proxy_for_benchmark,
        },
        config_yaml=yaml.safe_dump(stringify_paths(resolved_config), sort_keys=False),
        report_sections=_report_sections(
            experiment=experiment,
            dataset_entry=dataset_entry,
            acquisition=acquisition,
            provenance=provenance,
            method_config=method_config,
            metric_values=metric_values,
            diagnostics=diagnostics,
            environment_digest=environment_digest,
            proxy_for_benchmark=proxy_for_benchmark,
            run_mode=run_mode,
        ),
        commands=render_commands(reproduction_command),
        analysis_log=render_analysis_log(
            [
                f"Run mode: {run_mode}",
                f"Dataset protocol: {experiment.dataset.name}@{experiment.dataset.version}",
                f"Support fraction: {diagnostics['support_fraction']:.4f}",
                f"Gerchberg-Saxton iterations: {method_config['iterations']}",
                f"Proxy for benchmark: {proxy_for_benchmark}",
                f"Environment digest: {environment_digest}",
            ]
        ),
        environment_yaml=environment_yaml,
    )

    np.save(bundle_root / "figures" / "measurement_magnitude.npy", measurement)
    np.save(bundle_root / "figures" / "support.npy", support.astype(float))
    np.save(bundle_root / "figures" / "reference_phase.npy", masked_reference)
    np.save(bundle_root / "figures" / "reconstruction_phase.npy", masked_reconstruction)
    write_tsv(
        bundle_root / "tables" / "metrics.tsv",
        headers=["metric", "value"],
        rows=[[metric_name, f"{metric_value:.6f}"] for metric_name, metric_value in metric_values.items()],
    )
    write_tsv(
        bundle_root / "tables" / "optical_diagnostics.tsv",
        headers=["diagnostic", "value"],
        rows=[
            [diagnostic_name, f"{diagnostic_value:.6f}"]
            for diagnostic_name, diagnostic_value in diagnostics.items()
        ],
    )
    finalize_bundle(bundle_root)

    return WorkflowResult(
        bundle_path=bundle_root,
        skill_name="phase-retrieve",
        method_name=experiment.method,
        title=experiment.title,
        summary=summary,
        metrics={
            "metrics": metric_values,
            "optical_diagnostics": diagnostics,
            "environment_digest": environment_digest,
            "proxy_for_benchmark": proxy_for_benchmark,
        },
        resolved_config=resolved_config,
        proxy_for_benchmark=proxy_for_benchmark,
    )
