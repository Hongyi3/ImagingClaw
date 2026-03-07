# skills/AGENTS.override.md

When editing inside `skills/`:

1. Read the target skill's `SKILL.md` before changing code.
2. Keep the skill CLI stable unless the task explicitly changes it.
3. If you change routing keywords, regenerate `skills/catalog.json`.
4. Reports must continue to flow through the artifact-bundle helpers.
5. Do not make a skill silently depend on hidden local files or private paths.
