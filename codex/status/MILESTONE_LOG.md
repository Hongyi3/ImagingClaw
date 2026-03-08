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

- Transition: Completed Phase 3 — Coherent imaging, publication, and release, and designated
  Milestone 5 — v1.0 as the next milestone with no further Codex work packet defined yet.
- Status: `phase-retrieve` now runs a beta Gerchberg-Saxton workflow with direct coherent-imaging
  benchmark dispatch, `paper-figure` regenerates manuscript assets from validated bundles,
  `repro-export` emits audit bundles without mutating source runs, and release readiness now has a
  machine-checkable audit script.
- Validation: `python3 scripts/generate_catalog.py`, `python3 -m pytest`,
  `python3 -m src.clawimaging.cli list`, `ruff check .`, and `python3 -m mypy src` all passed.
- Notes:
  - Validation used `python3` because `python` is unavailable on PATH in this environment.
  - `python3 -m pytest` passed with 61 tests, including coherent-imaging, paper, and release audit
    coverage.
  - `python3 scripts/check_release_readiness.py` completed with warnings because root release
    metadata files still contain placeholder values.
  - Milestone 5 currently has no `codex/PHASE-*.md` work packet; define one before further
    milestone execution.

## 2026-03-08

- Transition: Added `codex/PHASE-4.md`, completed Milestone 5 — v1.0, and advanced the repository
  to post-v1.0 planning with no further Codex work packet defined yet.
- Status: Root release metadata is now synchronized from `release/v1.0.yaml`, release readiness
  passes cleanly against both the manifest and `pyproject.toml`, and software-paper plus
  benchmark-paper support packages are scriptable artifact bundles layered on the existing
  benchmark, paper, and repro-export workflows.
- Validation: `python3 scripts/sync_release_metadata.py`, `python3 scripts/generate_catalog.py`,
  `python3 -m pytest`, `python3 -m src.clawimaging.cli list`, `ruff check .`,
  `python3 -m mypy src`, and `python3 scripts/check_release_readiness.py` all passed.
- Notes:
  - Validation used `python3` because `python` is unavailable on PATH in this environment.
  - `python3 -m pytest` passed with 66 tests, including release-manifest validation,
    publication-package assembly, release auditing, coherent-imaging workflows, and prior CT/MRI
    coverage.
  - `python3 scripts/check_release_readiness.py` passed with zero errors and zero warnings.
  - The root release manifest truthfully records the DOI state as pending until public archive
    registration occurs.
  - Post-v1.0 planning currently has no `codex/PHASE-*.md` work packet; define one before further
    milestone execution.
