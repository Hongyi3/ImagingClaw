# Phase 1 — Benchmarks and datasets

## Goal

Create the benchmark and dataset substrate that the skills can build on.

## Required work

- implement a benchmark-spec loader
- implement a dataset-registry loader
- add validation for required benchmark fields
- connect benchmark metadata into artifact bundles
- add tests for spec validation

## Acceptance criteria

- benchmark specs in `benchmarks/specs/` validate
- dataset registry in `datasets/registry.yaml` validates
- benchmark runs can emit a resolved benchmark manifest
- docs are updated if schema changes
