# Phase 2 — CT and MRI

## Goal

Replace CT and MRI stubs with real baseline workflows while preserving the artifact-bundle contract.

## Required work

- implement one meaningful CT baseline
- implement one meaningful MRI baseline
- support declared config loading
- ensure reports contain method, data, metrics, and provenance sections
- keep skill CLIs stable

## Acceptance criteria

- `ct-recon` demo produces a realistic structured report
- `mri-recon` demo produces a realistic structured report
- benchmark runner can call both
- tests cover main execution paths
- `SKILL.md` files remain accurate
