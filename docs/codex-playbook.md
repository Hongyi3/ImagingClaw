# Codex Playbook

This repository is deliberately prepared for Codex-assisted development.

## What Codex should read first

1. `AGENTS.md`
2. `PROJECT-CHARTER.md`
3. `BLUEPRINT.md`
4. `codex/status/current.yaml`
5. `codex/status/NEXT_MILESTONE.md`
6. the `next_phase_file` named in `codex/status/current.yaml`

## Best operating pattern

1. Start Codex in the repository root
2. Ask it to summarize the instruction sources it loaded
3. Create a Git checkpoint
4. Read `codex/status/current.yaml` and `codex/status/NEXT_MILESTONE.md`
5. Give it exactly the `next_phase_file` named there
6. Require tests and catalog regeneration before it finishes
7. Require a task-scoped commit and push before it finishes any change that modifies
   repo-tracked files
8. Require the status files to be updated when the milestone advances

## Good first prompts

- Summarize the loaded instructions, the current milestone state in `codex/status/current.yaml`, the work packet selected by `next_phase_file`, and the requirement to commit and push completed repo-tracked changes.
- Read `AGENTS.md`, `PROJECT-CHARTER.md`, `BLUEPRINT.md`, `codex/status/current.yaml`, and `codex/status/NEXT_MILESTONE.md`. Complete the `next_phase_file` end to end with minimal, production-minded changes.
- Read the Codex status files first, then implement the benchmark specification loader described in `docs/benchmark-policy.md` only if it is the active next milestone.
- Read the Codex status files first, then turn the selected CT or MRI work packet into a real baseline pipeline without breaking the artifact-bundle contract.

## Review rule

Treat Codex like a fast collaborator, not an oracle. Require:
- file-by-file diffs
- explicit assumptions
- tests
- updated docs
