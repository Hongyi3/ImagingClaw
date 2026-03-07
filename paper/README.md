# Paper directory

This directory should eventually hold the manuscript source, figure-generation scripts, and
provenance notes linking manuscript assets to benchmark artifact IDs.

## Rules

- figures and tables must be script-generated
- no manual binary edits as the source of truth
- manuscript claims should map to benchmark specs and released artifacts

## Current entrypoint

- `python3 paper/scripts/regenerate_assets.py --input <bundle> --output <paper-bundle>`
- `python3 paper/scripts/regenerate_assets.py --demo --output <paper-bundle>`
