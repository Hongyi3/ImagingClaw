import math

import numpy as np
import pytest

from clawimaging.metrics import compute_metrics


def test_compute_metrics_identity_case() -> None:
    reference = np.eye(8, dtype=float)
    metrics = compute_metrics(reference, reference, ["nmse", "nrmse", "relative-error", "psnr", "ssim"])

    assert metrics["nmse"] == 0.0
    assert metrics["nrmse"] == 0.0
    assert metrics["relative-error"] == 0.0
    assert math.isinf(metrics["psnr"])
    assert metrics["ssim"] == pytest.approx(1.0, rel=1e-6)


def test_compute_metrics_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="same shape"):
        compute_metrics(np.zeros((4, 4), dtype=float), np.zeros((4, 5), dtype=float), ["psnr"])


def test_compute_metrics_rejects_unknown_metric() -> None:
    with pytest.raises(ValueError, match="Unsupported metric"):
        compute_metrics(np.zeros((4, 4), dtype=float), np.zeros((4, 4), dtype=float), ["mae"])
