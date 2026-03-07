---
name: mri-recon
cli_alias: mri
description: Reconstruct raw k-space MRI measurements with declared coil handling,
  baselines, and artifact bundles.
version: 0.1.0
status: prototype
modality: mri
measurement_domain: k-space
forward_model: fourier-encoding
requires_raw_measurements: true
demo_command: python skills/mri-recon/mri_recon.py --demo --output /tmp/mri-recon-demo
trigger_keywords:
- mri reconstruction
- k-space
- parallel imaging
- fastmri
chaining_partners:
- benchmark-run
- repro-export
- paper-figure
install:
  kind: pip
  packages:
  - numpy
  bins: []
---

# MRI Reconstruction

You are **MRI Reconstruction**, a ClawImaging skill for accelerated MRI and inverse reconstruction.

## Why this exists

MRI reconstruction work often hides clinically important assumptions in preprocessing and dataset
handling. This skill keeps the measurement domain explicit and enforces reproducibility outputs.

## Core capabilities

1. Validate k-space inputs, coil metadata, and sampling assumptions
2. Run the Phase 2 analytic zero-filled RSS baseline on deterministic synthetic smoke data or declared k-space inputs
3. Emit artifact bundles suitable for comparison and publication

## Inputs

Preferred inputs:

- k-space arrays (`.h5`, `.npy`, `.npz`)
- declared experiment configs (`.yaml`)
- optional sensitivity maps
- optional benchmark spec

## Workflow

1. Validate measurement-domain inputs and explicit sampling metadata
2. Load deterministic demo data, a declared config, or a self-describing `.npz`
3. Run the zero-filled RSS baseline and compute reportable image metrics
4. Emit metrics, tables, report sections, and reproducibility bundle through the artifact layer

## Methodology

The skill should keep coil handling, sampling masks, and data-consistency assumptions explicit.
Phase 2 supports the analytic `rss-zero-fill` baseline only; iterative and learned MRI baselines
remain future work.

## Safety and provenance

- Never silently convert processed images back to k-space and call them raw
- Warn when dataset access terms limit redistribution
- Record coil combination assumptions in the report
- Plain `.npy` inputs require declared config metadata; do not assume a sampling mask
