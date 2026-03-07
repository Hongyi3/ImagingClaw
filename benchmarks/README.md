# Benchmarks

Benchmark specifications live under `benchmarks/specs/`.

Each spec must pin:

- dataset name, version, split, and access
- task and modality
- forward model and geometry
- preprocessing
- calibration assumptions
- methods
- metrics
- seeds
- hardware notes
- environment notes

The phase-1 benchmark runner validates these specs against `datasets/registry.yaml` and emits a
resolved benchmark manifest in the artifact bundle.

Phase 2 extends this by dispatching the supported analytic CT or MRI baseline into a nested child
bundle while explicitly marking synthetic proxy execution when upstream benchmark measurements are
not present locally.
