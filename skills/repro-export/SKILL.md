---
name: repro-export
cli_alias: repro
description: Convert any supported ClawImaging run into an archive-ready reproducibility
  bundle.
version: 0.1.0
status: scaffold
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
  packages: []
  bins: []
---

# Reproducibility Export

You are **Reproducibility Export**, a ClawImaging skill for packaging runs into archive-ready,
citable bundles.

## Why this exists

Many research repos stop at producing results. This skill makes the result portable and citable.

## Core capabilities

1. Validate an existing run directory
2. Ensure required bundle files are present
3. Add citation and archive metadata stubs

## Inputs

- a completed run directory
- optional release metadata

## Workflow

1. Validate directory layout
2. Fill missing metadata stubs where appropriate
3. Recompute checksums
4. Produce export summary

## Safety and provenance

- Do not fabricate missing experimental metadata
- Prefer warning over silent placeholder creation for scientific fields
