# Codex Playbook

This repository is deliberately prepared for Codex-assisted development.

## What Codex should read first

1. `AGENTS.md`
2. `PROJECT-CHARTER.md`
3. `BLUEPRINT.md`
4. the relevant phase file under `codex/`

## Best operating pattern

1. Start Codex in the repository root
2. Ask it to summarize the instruction sources it loaded
3. Create a Git checkpoint
4. Give it one phase file at a time
5. Require tests and catalog regeneration before it finishes

## Good first prompts

- Summarize the loaded instructions and tell me the first milestone to implement.
- Complete `codex/PHASE-0.md` end to end and keep changes minimal but production-minded.
- Implement the benchmark specification loader described in `docs/benchmark-policy.md`.
- Turn the CT scaffold into a real baseline pipeline without breaking the artifact-bundle contract.

## Review rule

Treat Codex like a fast collaborator, not an oracle. Require:
- file-by-file diffs
- explicit assumptions
- tests
- updated docs
