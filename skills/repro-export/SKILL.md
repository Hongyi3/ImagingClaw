---
name: repro-export
cli_alias: repro
description: Convert any supported ClawImaging run into an archive-ready reproducibility
  bundle.
version: 0.1.0
status: prototype
modality: cross-cutting
measurement_domain: n/a
forward_model: artifact-bundle
requires_raw_measurements: true
demo_command: python skills/repro-export/repro_export.py --demo --output /tmp/repro-export-demo
trigger_keywords:
- reproducibility bundle
- archive run
- export artifact
- doi package
chaining_partners:
- benchmark-run
- paper-figure
install:
  kind: pip
  packages:
  - PyYAML
  bins: []
---

# Reproducibility Export

You are **Reproducibility Export**, a ClawImaging skill for packaging runs into archive-ready,
citable bundles.

## Why this exists

Many research repos stop at producing results. This skill makes the result portable and citable.

## Core capabilities

1. Validate an existing run directory
2. Inventory bundle contents and export an audit summary bundle
3. Audit repository citation and archive metadata without mutating the source run

## Inputs

- a completed run directory
- optional release metadata

## Workflow

1. Validate directory layout
2. Audit root metadata parseability, placeholders, and cross-file mismatches
3. Inventory source bundle files
4. Produce an export summary bundle

## Safety and provenance

- Do not fabricate missing experimental metadata
- Prefer warning over silent placeholder creation for scientific fields
- Do not mutate the source artifact bundle in place
