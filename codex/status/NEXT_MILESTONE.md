# Next Milestone

## Current Position

Milestone 3 — Coherent imaging, publication, and release is complete. Phase 3 has been accepted,
and the repository is now designated for Milestone 5 — v1.0 follow-through.

## Execute Next

No further Codex phase file is currently defined. Before requesting more milestone execution,
define a new work packet for Milestone 5 and point
[`codex/status/current.yaml`](/Users/hongyimac/Desktop/clawimaging_prework/codex/status/current.yaml)
at it.

## Priority Files And Policies

- [`AGENTS.md`](/Users/hongyimac/Desktop/clawimaging_prework/AGENTS.md)
- [`PROJECT-CHARTER.md`](/Users/hongyimac/Desktop/clawimaging_prework/PROJECT-CHARTER.md)
- [`BLUEPRINT.md`](/Users/hongyimac/Desktop/clawimaging_prework/BLUEPRINT.md)
- [`docs/release-checklist.md`](/Users/hongyimac/Desktop/clawimaging_prework/docs/release-checklist.md)
- [`paper/README.md`](/Users/hongyimac/Desktop/clawimaging_prework/paper/README.md)
- [`skills/phase-retrieve/SKILL.md`](/Users/hongyimac/Desktop/clawimaging_prework/skills/phase-retrieve/SKILL.md)
- [`skills/paper-figure/SKILL.md`](/Users/hongyimac/Desktop/clawimaging_prework/skills/paper-figure/SKILL.md)
- [`skills/repro-export/SKILL.md`](/Users/hongyimac/Desktop/clawimaging_prework/skills/repro-export/SKILL.md)

## Definition Of Done

- Freeze a v1.0 release plan.
- Prepare archive and DOI wiring for release.
- Prepare the software-paper package.
- Prepare the benchmark-paper package.

## Latest Validation

- `python3 scripts/generate_catalog.py` passed and regenerated `skills/catalog.json` with updated Phase 3 skill metadata.
- `python3 -m pytest` passed with 61 tests, including coherent-imaging workflows, paper regeneration, release auditing, and prior CT/MRI coverage.
- `python3 -m src.clawimaging.cli list` passed and listed all six registered skills.
- `ruff check .` passed.
- `python3 -m mypy src` passed.
- `python3 scripts/check_release_readiness.py` completed with warnings because `CITATION.cff`, `codemeta.json`, and `.zenodo.json` still contain placeholder public-release metadata.
