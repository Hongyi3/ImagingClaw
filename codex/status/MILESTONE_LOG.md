# Milestone Log

Entries are append-only. Add new entries at the end and do not rewrite prior entries.

## 2026-03-06

- Transition: Introduced the `codex/status/` milestone-tracking system, confirmed Milestone 0 —
  Charter and structure as complete, and set Milestone 1 — Core substrate with
  `codex/PHASE-0.md` as the next executable work packet.
- Status: Ready to begin core substrate work.
- Validation: `python3 scripts/generate_catalog.py`, `python3 -m pytest`,
  `python3 -m src.clawimaging.cli list`, and `ruff check .` passed. `python3 -m mypy src`
  failed on existing typing issues and missing PyYAML stubs.
- Notes:
  - Milestone numbers follow `BLUEPRINT.md`.
  - Phase files under `codex/` are execution packets, and `next_phase_file` is authoritative.

- Transition: Completed Milestone 1 — Core substrate and designated Milestone 2 — CT and MRI as
  the next active stage, with `codex/PHASE-1.md` as the next executable work packet.
- Status: Phase 0 acceptance criteria are satisfied. Core specs reject blank required values,
  artifact bundles validate checksums and required files, and the CLI now supports `list --json`
  and `route --explain` without adding modality logic to the orchestrator.
- Validation: `python3 scripts/generate_catalog.py`, `python3 -m pytest`,
  `python3 -m src.clawimaging.cli list`, `ruff check .`, and `python3 -m mypy src` all passed.
- Notes:
  - Validation used `python3` because `python` is unavailable on PATH in this environment.
  - The next packet remains `codex/PHASE-1.md` even though the next milestone label is
    Milestone 2 — CT and MRI.

## 2026-03-07

- Transition: Accepted Phase 1 — Benchmarks and datasets within Milestone 2 — CT and MRI, and
  advanced the next executable work packet from `codex/PHASE-1.md` to `codex/PHASE-2.md`.
- Status: Benchmark specs validate against the dataset registry, benchmark-run emits resolved
  manifests through the artifact bundle, and the repository is ready for CT and MRI baseline
  implementation.
- Validation: `python3 scripts/generate_catalog.py`, `python3 -m pytest`,
  `python3 -m src.clawimaging.cli list`, `ruff check .`, and `python3 -m mypy src` all passed.
- Notes:
  - Validation used `python3` because `python` is unavailable on PATH in this environment.
  - `skills/catalog.json` was regenerated deterministically with no content changes.

- Transition: Completed Phase 2 — CT and MRI and advanced the next executable work packet from
  `codex/PHASE-2.md` to `codex/PHASE-3.md`, designating Milestone 3 — Coherent imaging,
  publication, and release as the active stage.
- Status: Deterministic CT and MRI smoke baselines now emit structured artifact bundles, declared
  experiment configs resolve against the dataset registry, and benchmark-run dispatches both
  analytic workflows into nested child bundles while explicitly marking synthetic proxy execution.
- Validation: `python3 scripts/generate_catalog.py`, `python3 -m pytest`,
  `python3 -m src.clawimaging.cli list`, `ruff check .`, and `python3 -m mypy src` all passed.
- Notes:
  - Validation used `python3` because `python` is unavailable on PATH in this environment.
  - `python3 -m pytest` passed with 50 tests, including CT/MRI demo, config, and benchmark
    dispatch coverage.
