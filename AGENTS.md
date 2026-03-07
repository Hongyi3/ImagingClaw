# AGENTS.md

## Repository purpose

This repository is a reproducibility-first computational imaging project scaffold. It is designed
for coding agents and human contributors to extend systematically.

## Read these first

In this order:

1. `PROJECT-CHARTER.md`
2. `BLUEPRINT.md`
3. `docs/architecture.md`
4. `docs/benchmark-policy.md`
5. `docs/dataset-policy.md`
6. `docs/reproducibility-contract.md`
7. the relevant `SKILL.md` for the area you are touching

If you are editing under `paper/`, also read `paper/AGENTS.override.md`.
If you are editing under `skills/`, also read `skills/AGENTS.override.md`.

## Working rules

1. After loading the root policy docs and before substantive work, read
   `codex/status/current.yaml` and `codex/status/NEXT_MILESTONE.md`.

2. Unless the user explicitly overrides it, execute only the `next_milestone` and
   `next_phase_file` named in the status files. The status files choose the active work packet;
   policy docs and phase files define how the work must be done.

3. When a milestone is materially advanced or completed, update `codex/status/current.yaml`,
   rewrite `codex/status/NEXT_MILESTONE.md`, and append to `codex/status/MILESTONE_LOG.md` in
   the same change.

4. After completing any user-requested change that modifies repo-tracked files, Codex must create
   a task-scoped commit and push the current branch to GitHub before reporting completion. Push
   only the changes for the current task. If unrelated local changes would be included, or if the
   push fails, stop and report the blocker instead of claiming the task is finished.

5. Preserve the architecture:
   - orchestrator routes
   - skills own domain workflows
   - adapters wrap external backends
   - bundle helpers own artifact creation

6. Never put modality-specific physics in the orchestrator.

7. Treat `SKILL.md` as the methodology contract. If implementation changes capability, input,
   output, routing, or safety behavior, update `SKILL.md` in the same change.

8. Prefer adapter wrappers over re-implementing complex domain libraries.

9. Keep the CLI stable unless a task explicitly changes it.

10. Benchmark work must encode:
   - dataset version
   - preprocessing
   - forward model
   - calibration assumptions
   - metrics
   - seeds
   - hardware
   - environment digest

11. Raw-measurement provenance is mandatory. Do not silently treat processed images as raw data.

12. All serious outputs should flow through the artifact-bundle utilities.

## Commands to run after meaningful changes

```bash
python scripts/generate_catalog.py
python -m pytest
```

If you changed Python modules under `src/`, also run:

```bash
python -m src.clawimaging.cli list
```

If the environment has the tools installed, also run:

```bash
ruff check .
mypy src
```

## Contribution style

- Small, focused changes
- Clear docstrings
- Type hints where practical
- No dead config files
- No hidden assumptions about filesystem layout
- No hardcoded absolute paths

## Scientific quality bar

- Cite datasets and methods in docs when adding real integrations
- Keep baseline comparisons honest
- Prefer explicit metadata over implicit defaults
- No benchmark claims without reproducible specs and outputs

## File conventions

- Root policy docs stay concise and stable
- `docs/` holds detailed policy and design notes
- `skills/<name>/SKILL.md` is mandatory
- `skills/catalog.json` must be regenerated after `SKILL.md` frontmatter changes
- `paper/` must remain script-driven

## When uncertain

Choose the more reproducible, more explicit, and more benchmarkable design.
