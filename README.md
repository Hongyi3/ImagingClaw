# ClawImaging (prework scaffold)

ClawImaging is a reproducibility-first, agent-native computational imaging skill library.

This scaffold is intentionally modeled on the strongest ideas visible in ClawBio: independent
skills, an orchestrator that routes between them, local-first execution, and a strict
reproducibility bundle for every serious result. The difference is domain: this repo is
designed for computational imaging, inverse problems, benchmark-driven method development,
and paper-grade open research software.

## What this scaffold already gives you

- A project charter and an end-to-end blueprint
- Root instructions for Codex and other coding agents
- A token-optimized `llms.txt`
- A `CLAUDE.md`-style routing file
- A machine-readable `skills/catalog.json`
- Imaging-specific `SKILL.md` templates
- Prototype CT and MRI smoke baselines with deterministic reports and artifact bundles
- Starter skills for phase retrieval, benchmarking, reproducibility export, and paper figure
  regeneration
- A manifest-driven release metadata workflow and scriptable software / benchmark paper packages
- A minimal Python package with a working CLI, registry loader, router, and artifact-bundle
  helper
- Declared experiment examples under `experiments/specs/`
- CI, governance, contribution, security, citation, and release metadata scaffolding
- `paper/`, `benchmarks/`, `datasets/`, and `codex/` directories ready for incremental buildout

## Start here

1. Read `PROJECT-CHARTER.md`
2. Read `BLUEPRINT.md`
3. Read `AGENTS.md`
4. Run:

```bash
python scripts/generate_catalog.py
python -m pytest
python -m src.clawimaging.cli list
```

5. Open Codex in this directory and follow `codex/README.md`

## CLI quick checks

The core CLI is intentionally small and scriptable:

```bash
clawimaging list
clawimaging list --json
clawimaging show-skill bench
clawimaging route "benchmark compare methods" --explain
```

`list --json` emits the registry-backed skill catalog as JSON, and `route --explain` returns the
selected skill together with the routing score and matched trigger keywords.

## Design thesis

ClawImaging should *not* become a monolithic low-level reconstruction library. It should become
the layer that makes computational imaging work reproducible, benchmarkable, citable, and easier
to extend across modalities.

That means:

- physics-aware abstractions centered on forward models and inverse problems
- backend adapters for best-in-class domain libraries
- benchmark-first workflow design
- first-class publication and archival artifacts
- strict provenance from raw measurements to final figure

## Recommended v1 scope

- `ct-recon` — low-dose CT / tomography baseline skill
- `mri-recon` — raw k-space reconstruction baseline skill
- `phase-retrieve` — coherent imaging entry point
- `benchmark-run` — modality-agnostic benchmark harness
- `repro-export` — reproducibility/archival bundle creator
- `paper-figure` — figure/table regeneration from artifact IDs

## Repo map

```text
clawimaging_prework/
├── AGENTS.md
├── BLUEPRINT.md
├── PROJECT-CHARTER.md
├── experiments/
├── codex/
├── docs/
├── skills/
├── src/
├── tests/
├── benchmarks/
├── datasets/
└── paper/
```

## Status

The staged buildout is now frozen at the `1.0.0` release boundary. The repository includes
manifest-driven root release metadata, scriptable software-paper and benchmark-paper package
builders, deterministic CT/MRI/coherent-imaging smoke workflows, and reproducibility audits that
validate release readiness directly against the declared release manifest.
