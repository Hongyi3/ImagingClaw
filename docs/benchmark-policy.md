# Benchmark Policy

## Why benchmarks are central

Benchmarking is the backbone of ClawImaging. The project should make fair comparison easier than
unfair comparison.

## Required benchmark metadata

Every benchmark specification must declare:

- name and version
- modality and task
- dataset reference with name, version, split, and access
- forward model and geometry
- preprocessing
- calibration assumptions
- methods under comparison
- metrics
- seeds
- hardware notes
- environment notes

The machine-readable source of truth lives under `benchmarks/specs/`.

## Required baseline classes

Every benchmark track must include all three baseline classes:

1. Analytic
2. Iterative / model-based
3. Learned / unrolled

Validation should fail if any class is missing.

## Dataset coupling

- Every benchmark spec must resolve against `datasets/registry.yaml`
- Benchmark modality must match the dataset registry entry
- Benchmark access mode must match the dataset registry entry
- Reports must embed the resolved dataset-registry metadata, not just the benchmark-local reference

## Execution levels

### Smoke benchmark
Purpose:
- run in CI
- verify interface stability
- catch obvious regressions

Characteristics:
- tiny subset
- short runtime
- reduced metric set acceptable only when declared explicitly

### Release benchmark
Purpose:
- produce citable results
- compare methods on a fixed protocol
- publish immutable artifact bundles

Characteristics:
- full protocol
- complete metrics
- archived outputs
- release tag and environment digest required

## Reporting requirements

At minimum, each benchmark bundle must emit:

- aggregate benchmark summary in `metrics.json`
- resolved benchmark manifest in `resolved_config.yaml`
- exact commands in `reproducibility/commands.sh`
- analysis log in `reproducibility/analysis_log.md`
- environment snapshot in `reproducibility/environment.yml`
- checksums in `reproducibility/checksums.sha256`
- report sections for benchmark metadata, dataset provenance, methods, metrics, and reproducibility

## Fairness rules

- No undocumented preprocessing advantages
- No benchmark claim without declared seeds and split logic
- No learned method without meaningful non-learned baselines
- No benchmark without a machine-readable spec and registry-backed dataset reference
