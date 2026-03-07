# Project Charter

## Working name

ClawImaging

## Mission

Build the most reproducible, benchmarkable, and publication-ready open-source skill library for
computational imaging, centered on forward models, inverse problems, and research-grade artifact
generation.

## Problem statement

Computational imaging research is technically rich but operationally fragmented. Labs often rely on
a patchwork of modality-specific toolkits, private scripts, ad hoc dataset preprocessing, and
paper-specific evaluation code. As a result, strong ideas are difficult to reproduce, compare, and
extend.

ClawImaging exists to solve that operational problem.

## Who this is for

- Researchers building new inverse methods
- Reviewers and collaborators who need rerunnable experiments
- Students entering CT, MRI, coherent imaging, or microscopy
- Labs that want benchmark and paper pipelines without inventing them from scratch
- AI coding agents that need explicit project structure and methodology contracts

## Core claim

Every reported result should be one experiment specification and one command away from reproduction.

## Principles

1. Local-first by default
2. Raw-measurement aware
3. Reproducibility is part of the output, not a later add-on
4. One skill, one job, composable through an orchestrator
5. Benchmark-first rather than leaderboard-first
6. Publication artifacts and software artifacts should point to each other
7. Domain libraries should be wrapped, not rewritten without reason

## First public release scope

### Stable tracks
- CT / tomography
- MRI reconstruction

### Research-beta track
- Phase retrieval / coherent imaging

### Cross-cutting infrastructure
- Experiment specification
- Dataset registry
- Benchmark registry
- Artifact bundle export
- Paper figure regeneration
- Agent-facing project metadata

## Non-goals for v1

- A universal GUI
- Support for every imaging modality
- Clinical deployment
- Replacing all domain-specific backends
- Chasing SOTA on every task before the benchmark substrate is trusted

## Definition of done for v1.0

- End-to-end CT benchmark from declared dataset spec to immutable artifact bundle
- End-to-end MRI benchmark with explicit dataset-access policy handling
- Working phase retrieval skill in research-beta mode
- Continuous smoke benchmarks in CI
- Release-time full benchmark workflow
- Complete user and contributor docs
- Citation metadata, DOI wiring, and archive-ready outputs
- Paper directory that can regenerate all manuscript figures and tables

## Success metrics

- External contributors can add a skill without reverse-engineering the repo
- Reviewers can rerun at least one flagship figure from released artifacts
- Benchmark specs are stable enough to compare multiple methods fairly
- A software paper can be submitted without a structural rewrite
