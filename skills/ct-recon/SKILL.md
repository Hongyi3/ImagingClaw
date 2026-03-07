---
name: ct-recon
cli_alias: ct
description: Reconstruct low-dose CT or tomography measurements with declared geometry,
  baselines, and artifact bundles.
version: 0.1.0
status: prototype
modality: ct
measurement_domain: sinogram
forward_model: x-ray-transform
requires_raw_measurements: true
demo_command: python skills/ct-recon/ct_recon.py --demo --output /tmp/ct-recon-demo
trigger_keywords:
- ct reconstruction
- low-dose ct
- sinogram
- tomography
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

# CT Reconstruction

You are **CT Reconstruction**, a ClawImaging skill for tomographic inverse problems.

## Why this exists

CT papers often compare methods under inconsistent forward models, undocumented preprocessing, and
paper-specific scripts. This skill creates a disciplined path from sinogram-like measurements to
reproducible reconstruction reports.

## Core capabilities

1. Validate CT measurement metadata and geometry assumptions
2. Run the Phase 2 analytic FBP baseline on deterministic synthetic smoke data or declared sinogram inputs
3. Emit comparable metrics, provenance tables, and a publication-friendly artifact bundle

## Inputs

Preferred inputs:

- sinogram arrays (`.npy`, `.npz`, `.h5`)
- declared experiment configs (`.yaml`)
- geometry metadata (JSON / YAML)
- optional benchmark spec

## Workflow

1. Validate declared geometry and provenance metadata
2. Load deterministic demo data, a declared config, or a self-describing `.npz`
3. Run the analytic FBP baseline and compute reportable image metrics
4. Write metrics, tables, report sections, and reproducibility artifacts through the artifact layer

## Methodology

For each run, the skill must make geometry assumptions explicit and separate method selection from
report generation. Phase 2 supports the analytic `fbp` baseline only; iterative and learned CT
baselines remain future work.

## Safety and provenance

- Never claim a reconstruction is raw-data-based if measurements were derived from images
- Warn when geometry or dose assumptions are missing
- Do not hardcode benchmark paths
- Plain `.npy` inputs require declared config metadata; do not assume geometry defaults
