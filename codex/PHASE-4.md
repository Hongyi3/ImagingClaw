# Phase 4 — v1.0 release freeze

## Goal

Freeze the repository for a truthful `1.0.0` release with manifest-driven metadata and
scriptable paper-support packages.

## Required work

- define a release manifest under `release/`
- synchronize root release metadata from the manifest
- validate release readiness against the manifest and `pyproject.toml`
- add software-paper and benchmark-paper package assembly scripts
- update milestone status files and release-facing docs

## Acceptance criteria

- `release/v1.0.yaml` is the source of truth for root release metadata
- `python3 scripts/check_release_readiness.py` passes
- `python3 paper/scripts/build_package.py --package software --output <dir>` works
- `python3 paper/scripts/build_package.py --package benchmark --demo --output <dir>` works
- status files mark Milestone 5 — v1.0 as complete
