# Publication Strategy

## Paper sequence

### Paper 1 — software paper
Goal:
- establish the platform
- emphasize design, need, and research application
- document reproducibility philosophy and architecture

Likely targets:
- JOSS
- JORS

### Paper 2 — benchmark / methodology paper
Goal:
- define fair benchmark protocols
- compare strong baselines
- publish reproducible benchmark artifacts

Likely targets:
- IEEE Transactions on Computational Imaging
- SIAM Journal on Imaging Sciences

## Internal rules for publication readiness

- figures must be script-generated
- tables must come from versioned artifacts
- claims must map to benchmark specs
- code, docs, and manuscript should reference the same release
- release metadata should be synchronized from one manifest, not edited independently

## What reviewers should be able to do

- inspect the benchmark spec
- download or request the dataset using documented instructions
- rerun at least one flagship result
- trace every paper figure to an artifact ID

## Packaging entrypoints

Use these scriptable bundle builders for release-facing paper support:

```bash
python3 paper/scripts/build_package.py --package software --output /tmp/clawimaging-software-package
python3 paper/scripts/build_package.py --package benchmark --demo --output /tmp/clawimaging-benchmark-package
```

The software package captures release metadata and core documentation. The benchmark package
captures a resolved benchmark bundle, regenerated manuscript assets, dataset references, and a
reproducibility audit bundle.
