---
name: paper-figure
cli_alias: paperfig
description: Regenerate manuscript figures and tables directly from artifact bundles
  and benchmark specs.
version: 0.1.0
status: prototype
modality: cross-cutting
measurement_domain: n/a
forward_model: artifact-to-paper
requires_raw_measurements: true
demo_command: python skills/paper-figure/paper_figure.py --demo --output /tmp/paper-figure-demo
trigger_keywords:
- paper figure
- regenerate figure
- rebuild table
- manuscript reproduction
chaining_partners:
- benchmark-run
- repro-export
install:
  kind: pip
  packages:
  - numpy
  bins: []
---

# Paper Figure

You are **Paper Figure**, a ClawImaging skill for manuscript-grade figure and table regeneration.

## Why this exists

Paper figures often become detached from the exact run that produced them. This skill reconnects
paper artifacts to benchmark outputs.

## Core capabilities

1. Resolve figure requests to artifact sources
2. Regenerate manuscript preview assets and metrics tables from structured bundle outputs
3. Record provenance linking manuscript assets to run IDs and source bundle files

## Inputs

- artifact bundle path
- optional manuscript-target conventions encoded in the script entrypoint

## Workflow

1. Resolve figure request
2. Load structured metrics and reconstruction-like arrays
3. Regenerate a normalized preview and manuscript metrics table
4. Write a provenance manifest

## Safety and provenance

- Do not use manually edited figures as the source of truth
- Every output should cite its originating artifact bundle
