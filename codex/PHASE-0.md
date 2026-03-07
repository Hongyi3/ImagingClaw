# Phase 0 — Core substrate

## Goal

Turn the scaffold into a reliable internal foundation.

## Required work

- strengthen `src/clawimaging/specs.py`
- expand `src/clawimaging/artifacts.py`
- make the CLI slightly more usable
- improve tests
- keep docs synchronized with implementation

## Acceptance criteria

- `python -m pytest` passes
- `python scripts/generate_catalog.py` updates `skills/catalog.json` deterministically
- CLI can list skills and route simple queries
- artifact bundle creation is tested and stable
- no modality-specific logic in the orchestrator
