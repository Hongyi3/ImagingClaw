# Codex work packets

Use these in order. Each phase is sized so Codex can make real progress without drifting.

## Suggested workflow

1. Start Codex at repository root
2. Ask it to summarize the instruction files it loaded
3. Create a Git checkpoint
4. Hand it exactly one phase file
5. Review diff and run tests
6. Move to the next phase only after acceptance criteria are met

## Sequence

1. `PHASE-0.md` — core substrate
2. `PHASE-1.md` — benchmark and dataset registry
3. `PHASE-2.md` — CT and MRI implementation
4. `PHASE-3.md` — coherent imaging, publication, and release

## Example prompt

```text
Read AGENTS.md, PROJECT-CHARTER.md, and codex/PHASE-0.md.
Complete the phase end to end with production-minded, minimal changes.
Keep interfaces stable, run tests, regenerate the skill catalog, and summarize what remains.
```
