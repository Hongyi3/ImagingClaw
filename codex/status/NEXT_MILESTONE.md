# Next Milestone

## Current Position

Milestone 2 — CT and MRI is complete. Phase 2 — CT and MRI implementation has been accepted, and
the repository is now queued for Phase 3 — Coherent imaging, publication, and release.

## Execute Next

Codex should execute [`codex/PHASE-3.md`](/Users/hongyimac/Desktop/clawimaging_prework/codex/PHASE-3.md)
next. Milestones come from [`BLUEPRINT.md`](/Users/hongyimac/Desktop/clawimaging_prework/BLUEPRINT.md),
while phase files are Codex work packets; Codex must follow `next_phase_file` in
[`codex/status/current.yaml`](/Users/hongyimac/Desktop/clawimaging_prework/codex/status/current.yaml)
even when the milestone label and phase number do not match.

## Priority Files And Policies

- [`AGENTS.md`](/Users/hongyimac/Desktop/clawimaging_prework/AGENTS.md)
- [`PROJECT-CHARTER.md`](/Users/hongyimac/Desktop/clawimaging_prework/PROJECT-CHARTER.md)
- [`BLUEPRINT.md`](/Users/hongyimac/Desktop/clawimaging_prework/BLUEPRINT.md)
- [`docs/reproducibility-contract.md`](/Users/hongyimac/Desktop/clawimaging_prework/docs/reproducibility-contract.md)
- [`codex/PHASE-3.md`](/Users/hongyimac/Desktop/clawimaging_prework/codex/PHASE-3.md)
- [`skills/phase-retrieve/SKILL.md`](/Users/hongyimac/Desktop/clawimaging_prework/skills/phase-retrieve/SKILL.md)
- [`skills/paper-figure/SKILL.md`](/Users/hongyimac/Desktop/clawimaging_prework/skills/paper-figure/SKILL.md)
- [`skills/repro-export/SKILL.md`](/Users/hongyimac/Desktop/clawimaging_prework/skills/repro-export/SKILL.md)

## Definition Of Done

- `phase-retrieve` skill is usable in beta mode.
- Paper figure regeneration is scriptable.
- Release checklist is actionable.
- The repository is close to software-paper submission quality.

## Latest Validation

- `python3 scripts/generate_catalog.py` passed and regenerated `skills/catalog.json` with updated Phase 2 skill metadata.
- `python3 -m pytest` passed with 50 tests, including CT and MRI demos, declared config loading, benchmark dispatch, metrics, datasets, artifacts, and CLI coverage.
- `python3 -m src.clawimaging.cli list` passed and listed all six registered skills.
- `ruff check .` passed.
- `python3 -m mypy src` passed.
