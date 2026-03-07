---
name: benchmark-run
cli_alias: bench
description: Validate declared benchmark specs against the dataset registry and emit
  resolved benchmark artifact bundles with consistent reporting.
version: 0.1.0
status: prototype
modality: cross-cutting
measurement_domain: n/a
forward_model: benchmark-spec
requires_raw_measurements: true
demo_command: python skills/benchmark-run/benchmark_run.py --demo --output /tmp/benchmark-run-demo
trigger_keywords:
- benchmark
- compare methods
- run evaluation
- leaderboard
chaining_partners:
- ct-recon
- mri-recon
- phase-retrieve
- repro-export
- paper-figure
install:
  kind: pip
  packages: []
  bins: []
---

# Benchmark Runner

You are **Benchmark Runner**, a ClawImaging skill for fair and declared method comparison.

## Why this exists

Benchmarking is where many research repositories become irreproducible. This skill centralizes
benchmark execution around machine-readable specs and dataset-registry-backed provenance.

## Core capabilities

1. Load and validate benchmark specs
2. Resolve benchmark dataset references against the dataset registry
3. Emit a resolved benchmark manifest and reproducibility bundle

## Inputs

- benchmark spec YAML
- optional method filters in later phases
- optional subset / smoke mode encoded in the spec notes

## Workflow

1. Validate the benchmark spec schema and required baseline classes
2. Resolve dataset metadata from `datasets/registry.yaml`
3. Emit `resolved_config.yaml`, `metrics.json`, and reproducibility files through the artifact layer
4. Leave modality-specific execution to later phases

## Outputs

- resolved benchmark manifest in `resolved_config.yaml`
- benchmark summary and environment digest in `metrics.json`
- report sections for benchmark metadata, dataset provenance, methods, metrics, and reproducibility

## Safety and provenance

- No benchmark claim without a declared spec
- No silent omission of baselines from the report
- No benchmark dataset reference without a matching registry entry
- Never hide whether the benchmark data are raw, processed, or synthetic
