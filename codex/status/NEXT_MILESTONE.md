# Next Milestone

## Current Position

Milestone 5 — v1.0 is complete. Phase 4 has been accepted, and the repository is now in
post-v1.0 planning with no active Codex work packet.

## Execute Next

No further Codex phase file is currently defined. Before requesting more milestone execution,
define a new post-v1.0 work packet and point
[`codex/status/current.yaml`](/Users/hongyimac/Desktop/clawimaging_prework/codex/status/current.yaml)
at it.

## Priority Files And Policies

- [`AGENTS.md`](/Users/hongyimac/Desktop/clawimaging_prework/AGENTS.md)
- [`PROJECT-CHARTER.md`](/Users/hongyimac/Desktop/clawimaging_prework/PROJECT-CHARTER.md)
- [`BLUEPRINT.md`](/Users/hongyimac/Desktop/clawimaging_prework/BLUEPRINT.md)
- [`release/v1.0.yaml`](/Users/hongyimac/Desktop/clawimaging_prework/release/v1.0.yaml)
- [`docs/release-checklist.md`](/Users/hongyimac/Desktop/clawimaging_prework/docs/release-checklist.md)
- [`docs/publication-strategy.md`](/Users/hongyimac/Desktop/clawimaging_prework/docs/publication-strategy.md)
- [`paper/README.md`](/Users/hongyimac/Desktop/clawimaging_prework/paper/README.md)
- [`skills/repro-export/SKILL.md`](/Users/hongyimac/Desktop/clawimaging_prework/skills/repro-export/SKILL.md)
- [`GOVERNANCE.md`](/Users/hongyimac/Desktop/clawimaging_prework/GOVERNANCE.md)

## Definition Of Done

- Define the next post-v1.0 milestone explicitly.
- Add a new `codex/PHASE-*.md` work packet with acceptance criteria.
- Point `codex/status/current.yaml` at that packet.
- Keep release metadata and publication-package workflows as the standing baseline.

## Latest Validation

- `python3 scripts/sync_release_metadata.py` passed and synchronized `CITATION.cff`, `codemeta.json`, and `.zenodo.json` from `release/v1.0.yaml`.
- `python3 scripts/generate_catalog.py` passed and regenerated `skills/catalog.json` with updated release-audit methodology text.
- `python3 -m pytest` passed with 66 tests, including release-manifest validation, publication-package assembly, release auditing, coherent-imaging workflows, and prior CT/MRI coverage.
- `python3 -m src.clawimaging.cli list` passed and listed all six registered skills.
- `ruff check .` passed.
- `python3 -m mypy src` passed.
- `python3 scripts/check_release_readiness.py` passed with zero errors and zero warnings.
