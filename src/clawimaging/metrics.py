from __future__ import annotations

from collections.abc import Sequence
from typing import Callable

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


MetricFunction = Callable[[np.ndarray, np.ndarray], float]


def _prepare_array(array: np.ndarray) -> np.ndarray:
    prepared = np.asarray(array)
    if np.iscomplexobj(prepared):
        prepared = np.abs(prepared)
    return prepared.astype(float, copy=False)


def _validate_image_pair(reference: np.ndarray, estimate: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    reference_array = _prepare_array(reference)
    estimate_array = _prepare_array(estimate)
    if reference_array.shape != estimate_array.shape:
        raise ValueError("Reference and estimate must have the same shape")
    if reference_array.ndim != 2:
        raise ValueError("Metrics require 2D image inputs")
    return reference_array, estimate_array


def nmse(reference: np.ndarray, estimate: np.ndarray) -> float:
    reference_array, estimate_array = _validate_image_pair(reference, estimate)
    denominator = float(np.sum(reference_array ** 2))
    if denominator == 0.0:
        raise ValueError("NMSE is undefined for an all-zero reference image")
    numerator = float(np.sum((estimate_array - reference_array) ** 2))
    return numerator / denominator


def nrmse(reference: np.ndarray, estimate: np.ndarray) -> float:
    return float(np.sqrt(nmse(reference, estimate)))


def relative_error(reference: np.ndarray, estimate: np.ndarray) -> float:
    reference_array, estimate_array = _validate_image_pair(reference, estimate)
    denominator = float(np.linalg.norm(reference_array))
    if denominator == 0.0:
        raise ValueError("Relative error is undefined for an all-zero reference image")
    return float(np.linalg.norm(estimate_array - reference_array) / denominator)


def psnr(reference: np.ndarray, estimate: np.ndarray) -> float:
    reference_array, estimate_array = _validate_image_pair(reference, estimate)
    mse = float(np.mean((estimate_array - reference_array) ** 2))
    if mse == 0.0:
        return float("inf")
    reference_min = float(np.min(reference_array))
    reference_max = float(np.max(reference_array))
    data_range = reference_max - reference_min
    if data_range == 0.0:
        data_range = 1.0
    return 20.0 * float(np.log10(data_range)) - 10.0 * float(np.log10(mse))


def ssim(reference: np.ndarray, estimate: np.ndarray) -> float:
    reference_array, estimate_array = _validate_image_pair(reference, estimate)
    min_dimension = min(reference_array.shape)
    window_size = 7 if min_dimension >= 7 else max(1, min_dimension)
    if window_size % 2 == 0:
        window_size -= 1
    pad = window_size // 2

    reference_padded = np.pad(reference_array, pad, mode="reflect")
    estimate_padded = np.pad(estimate_array, pad, mode="reflect")

    reference_windows = sliding_window_view(reference_padded, (window_size, window_size))
    estimate_windows = sliding_window_view(estimate_padded, (window_size, window_size))

    mean_reference = np.mean(reference_windows, axis=(-1, -2))
    mean_estimate = np.mean(estimate_windows, axis=(-1, -2))
    var_reference = np.var(reference_windows, axis=(-1, -2))
    var_estimate = np.var(estimate_windows, axis=(-1, -2))
    covariance = np.mean(
        (reference_windows - mean_reference[..., None, None])
        * (estimate_windows - mean_estimate[..., None, None]),
        axis=(-1, -2),
    )

    reference_min = float(np.min(reference_array))
    reference_max = float(np.max(reference_array))
    data_range = reference_max - reference_min
    if data_range == 0.0:
        data_range = 1.0
    c1 = (0.01 * data_range) ** 2
    c2 = (0.03 * data_range) ** 2
    numerator = (2.0 * mean_reference * mean_estimate + c1) * (2.0 * covariance + c2)
    denominator = (
        (mean_reference ** 2 + mean_estimate ** 2 + c1)
        * (var_reference + var_estimate + c2)
    )
    return float(np.mean(numerator / denominator))


METRICS: dict[str, MetricFunction] = {
    "nmse": nmse,
    "nrmse": nrmse,
    "relative-error": relative_error,
    "psnr": psnr,
    "ssim": ssim,
}


def compute_metrics(
    reference: np.ndarray,
    estimate: np.ndarray,
    metric_names: Sequence[str],
) -> dict[str, float]:
    results: dict[str, float] = {}
    for metric_name in metric_names:
        normalized_name = metric_name.strip().lower()
        if normalized_name not in METRICS:
            raise ValueError(f"Unsupported metric requested: {metric_name}")
        results[normalized_name] = METRICS[normalized_name](reference, estimate)
    return results
