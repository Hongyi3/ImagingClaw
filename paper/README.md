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
- `python3 paper/scripts/build_package.py --package software --output <package-bundle>`
- `python3 paper/scripts/build_package.py --package benchmark --demo --output <package-bundle>`

## Package modes

- `software` copies the release manifest, synchronized root metadata, catalog snapshot, and core
  repo docs into an artifact bundle suitable for software-paper support.
- `benchmark` packages a benchmark-run bundle together with regenerated manuscript assets and a
  repro-export audit bundle. Use `--demo` to build it from the repo's supported smoke benchmark,
  or `--source-bundle <benchmark-bundle-or-child-bundle>` to package an existing benchmark run.
