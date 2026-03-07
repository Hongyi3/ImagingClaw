# Codex work packets

Use these in order. Each phase is sized so Codex can make real progress without drifting. The
status files under `codex/status/` decide which packet is active, and `next_phase_file` is the
authoritative execution target even when milestone numbering and phase numbering do not match.

## Status files

- `status/current.yaml` is the machine-readable source of truth for the active stage, next
  milestone, acceptance state, blockers, and latest validation results.
- `status/NEXT_MILESTONE.md` is the human-readable handoff for the next packet of work.
- `status/MILESTONE_LOG.md` is the append-only history of milestone transitions and major
  validation outcomes.

## Suggested workflow

1. Start Codex at repository root
2. Ask it to summarize the instruction and status files it loaded
3. Create a Git checkpoint
4. Read `codex/status/current.yaml` and `codex/status/NEXT_MILESTONE.md`
5. Hand it exactly the phase file named by `next_phase_file`
6. Review diff and run tests
7. Create a task-scoped commit and push the current branch to GitHub before finishing any change
   that modifies repo-tracked files
8. Update the status files when the milestone advances
9. Move to the next phase only after acceptance criteria are met

## Sequence

This is the reference order of work packets. Execute the packet selected by `next_phase_file`,
not whichever phase number appears to match the milestone number.

1. `PHASE-0.md` — core substrate
2. `PHASE-1.md` — benchmark and dataset registry
3. `PHASE-2.md` — CT and MRI implementation
4. `PHASE-3.md` — coherent imaging, publication, and release

## Example prompt

```text
Read AGENTS.md, PROJECT-CHARTER.md, BLUEPRINT.md, codex/status/current.yaml, and
codex/status/NEXT_MILESTONE.md. Execute only the next_phase_file named there.
Complete that work packet end to end with production-minded, minimal changes.
Keep interfaces stable, run tests, regenerate the skill catalog, update the status files if the
milestone advances, commit and push completed repo-tracked changes, and summarize what remains.
```
