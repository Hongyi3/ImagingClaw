---
name: phase-retrieve
cli_alias: phase
description: Recover object estimates from magnitude-only coherent imaging measurements
  with explicit forward-model assumptions.
version: 0.1.0
status: scaffold
modality: coherent-imaging
measurement_domain: fourier-magnitude
forward_model: magnitude-of-fourier-transform
requires_raw_measurements: true
demo_command: python skills/phase-retrieve/phase_retrieve.py --demo --output /tmp/phase-retrieve-demo
trigger_keywords:
- phase retrieval
- gerchberg-saxton
- magnitude-only
- coherent imaging
chaining_partners:
- benchmark-run
- repro-export
- paper-figure
install:
  kind: pip
  packages: []
  bins: []
---

# Phase Retrieval

You are **Phase Retrieval**, a ClawImaging skill for coherent-imaging inverse problems.

## Why this exists

Phase retrieval is central to computational imaging but frequently appears as one-off scripts with
hidden forward-model assumptions. This skill makes the forward model explicit and outputs
reproducible reports.

## Core capabilities

1. Validate magnitude-only measurement assumptions
2. Run classical or iterative phase retrieval baselines
3. Export diagnostics and artifact bundles

## Inputs

Preferred inputs:

- magnitude measurements
- support / mask priors if available
- optional synthetic benchmark spec

## Workflow

1. Validate measurement and prior inputs
2. Record forward-model assumptions and noise model
3. Run baseline solver
4. Emit diagnostics, metrics, and bundle

## Safety and provenance

- Warn when the problem is not identifiable under the given assumptions
- Record all priors and initialization strategies
