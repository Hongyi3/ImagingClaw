from pathlib import Path

import numpy as np
import pytest
import yaml

from clawimaging.experiments import load_experiment_config


def test_load_experiment_config_repo_examples() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    ct_config = load_experiment_config(repo_root / "experiments" / "specs" / "ct_fbp_example.yaml")
    mri_config = load_experiment_config(repo_root / "experiments" / "specs" / "mri_zero_fill_example.yaml")

    assert ct_config.dataset_entry.data_kind == "synthetic-measurements"
    assert ct_config.experiment.dataset.name == "ct-demo-phantoms"
    assert mri_config.dataset_entry.measurement_domain == "k-space"
    assert mri_config.experiment.method == "rss-zero-fill"


def test_load_experiment_config_rejects_dataset_modality_mismatch(tmp_path: Path) -> None:
    measurement_path = tmp_path / "measurement.npy"
    reference_path = tmp_path / "reference.npy"
    np.save(measurement_path, np.zeros((4, 4), dtype=float))
    np.save(reference_path, np.zeros((4, 4), dtype=float))

    config_path = tmp_path / "broken.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "experiment": {
                    "experiment_id": "broken",
                    "title": "Broken config",
                    "modality": "mri",
                    "task": "synthetic",
                    "dataset": {
                        "name": "ct-demo-phantoms",
                        "version": "0.1",
                        "split": "synthetic",
                        "access": "open",
                    },
                    "forward_model": {
                        "operator": "fourier-encoding",
                        "geometry": "cartesian",
                        "noise_model": "acquisition-native",
                    },
                    "method": "rss-zero-fill",
                    "metrics": ["nmse"],
                    "seed": 5,
                },
                "input": {
                    "measurement_path": str(measurement_path),
                    "reference_path": str(reference_path),
                    "provenance": {
                        "data_kind": "synthetic-measurements",
                        "measurement_domain": "k-space",
                        "source": "unit test",
                    },
                },
                "acquisition": {"sampling_mask": [[1.0, 1.0], [1.0, 1.0]]},
                "method_config": {"coil_combination": "rss"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="modality does not match"):
        load_experiment_config(config_path)
