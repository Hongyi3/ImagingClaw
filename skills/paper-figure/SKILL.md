---
name: paper-figure
cli_alias: paperfig
description: Regenerate manuscript figures and tables directly from artifact bundles
  and benchmark specs.
version: 0.1.0
status: scaffold
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
  packages: []
  bins: []
---

# Paper Figure

You are **Paper Figure**, a ClawImaging skill for manuscript-grade figure and table regeneration.

## Why this exists

Paper figures often become detached from the exact run that produced them. This skill reconnects
paper artifacts to benchmark outputs.

## Core capabilities

1. Resolve figure requests to artifact sources
2. Regenerate tables and plots from structured outputs
3. Record provenance linking manuscript assets to run IDs

## Inputs

- artifact bundle path
- figure specification or manuscript target
- optional style config

## Workflow

1. Resolve figure request
2. Load structured metrics and tables
3. Regenerate asset
4. Write provenance note

## Safety and provenance

- Do not use manually edited figures as the source of truth
- Every output should cite its originating artifact bundle
