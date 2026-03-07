---
name: ct-recon
cli_alias: ct
description: Reconstruct low-dose CT or tomography measurements with declared geometry,
  baselines, and artifact bundles.
version: 0.1.0
status: scaffold
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
  packages: []
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
2. Run analytic, iterative, or learned baseline workflows
3. Emit comparable metrics and a publication-friendly artifact bundle

## Inputs

Preferred inputs:

- sinogram arrays (`.npy`, `.npz`, `.h5`)
- geometry metadata (JSON / YAML)
- optional benchmark spec

## Workflow

1. Validate input paths and geometry metadata
2. Record whether data are raw, simulated, or preprocessed
3. Select a reconstruction path (e.g., FBP, TV, learned baseline)
4. Write metrics, report, and reproducibility artifacts

## Methodology

For each run, the skill must make geometry assumptions explicit and separate method selection from
report generation.

## Safety and provenance

- Never claim a reconstruction is raw-data-based if measurements were derived from images
- Warn when geometry or dose assumptions are missing
- Do not hardcode benchmark paths
