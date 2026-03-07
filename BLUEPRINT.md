# ClawImaging Blueprint

## 1. Positioning

The right move is **not** to build another reconstruction library from scratch. The right move is
to build a reproducibility-first operating layer for computational imaging, inspired by ClawBio’s
architecture and retargeted to inverse problems.

ClawImaging should preserve these ClawBio ideas:

- independent skills with explicit methodology contracts in `SKILL.md`
- an orchestrator that routes requests and composes workflows
- local-first execution
- strict artifact bundles containing reports, commands, environments, and checksums
- agent-facing project files that let coding agents understand the repo quickly

## 2. Academic thesis

The project’s strongest academic claim should be simple and durable:

> Every computational-imaging result should be reproducible from a single experiment spec and a
> single command, with raw-data provenance, benchmark context, and publication artifacts preserved.

That is stronger than “we have another reconstruction package.” It makes the project useful to
researchers, reviewers, and other labs.

## 3. What to build

### Core package
A Python package that owns:

- experiment specifications
- dataset registry
- benchmark registry
- orchestrator and routing logic
- artifact bundle generation
- report assembly
- light wrappers around external backends

### Skills
Each skill is a thin, sharp unit of work with a CLI and a `SKILL.md` contract.

Recommended first-wave skills:

1. `ct-recon`
2. `mri-recon`
3. `phase-retrieve`
4. `benchmark-run`
5. `repro-export`
6. `paper-figure`

### Adapters
Keep backend-specific logic in adapters so the core stays clean.

Recommended initial adapter targets:

- DeepInverse
- ODL
- SCICO
- ASTRA
- BART
- SigPy
- CIL
- Pyxu
- PtyPy
- Ptychography 4.0

## 4. Scope strategy

### Stable v1 tracks
- CT / tomography
- MRI reconstruction

### Research-beta v1 track
- Phase retrieval / coherent imaging

### Why this scope works
It balances openness, scientific importance, and modality diversity:

- CT gives you a clean public benchmark story
- MRI gives you community visibility and raw-measurement relevance
- Coherent imaging makes the project feel genuinely computational-imaging-native

## 5. Architecture

```text
User / agent request
        │
        ▼
Orchestrator (routing + planning + bundle assembly)
        │
        ├── Skill: ct-recon
        ├── Skill: mri-recon
        ├── Skill: phase-retrieve
        ├── Skill: benchmark-run
        ├── Skill: repro-export
        └── Skill: paper-figure
        │
        ▼
Output layer
- report.md / html / pdf
- figures/
- tables/
- metrics.json
- resolved_config.yaml
- commands.sh
- environment lock
- checksums.sha256
- analysis_log.md
- citation + archive metadata
```

### Key abstractions

- `Measurement`
- `ForwardModel`
- `Geometry`
- `NoiseModel`
- `Calibration`
- `DatasetRef`
- `ExperimentSpec`
- `BenchmarkSpec`
- `MetricSuite`
- `ArtifactBundle`

### Rule
Never bury modality-specific physics in the orchestrator. The orchestrator routes; the skill owns
domain logic; the adapter owns backend interop.

## 6. Benchmark-first doctrine

Benchmarks are not a side feature. They are the center of gravity.

Every benchmark must declare:

- dataset version and access mode
- train / validation / test split logic
- forward operator and geometry
- calibration assumptions
- preprocessing steps
- reconstruction method and hyperparameters
- metrics
- random seeds
- hardware information
- software environment digest

### Required baseline tiers

For each benchmark track, include:

1. analytic / closed-form baseline where meaningful
2. iterative / model-based baseline
3. learned or unrolled baseline

This prevents the project from becoming a pure deep-learning showcase with weak comparisons.

### Benchmark execution levels

#### CI smoke level
- tiny subset
- fast runtime
- catches interface and numerical regressions

#### release level
- full benchmark set
- archived outputs
- immutable summary tables and metrics

## 7. Dataset policy

Data handling is a scientific issue, not just an engineering issue.

### Mandatory rules
- Record whether inputs are raw measurements, partially processed measurements, or images
- Record every preprocessing step
- Record access restrictions and redistribution limits
- Attach a dataset card or datasheet
- Refuse silent conversion of processed images back into measurement space without explicit warning

### Recommended initial dataset tracks
- LoDoPaB-CT for CT
- fastMRI for MRI
- a small public phase retrieval / ptychography starter dataset for coherent imaging

## 8. Reproducibility contract

Every accepted run should emit a self-describing artifact bundle:

```text
artifact_bundle/
├── report.md
├── metrics.json
├── resolved_config.yaml
├── figures/
├── tables/
├── reproducibility/
│   ├── commands.sh
│   ├── environment.yml
│   ├── analysis_log.md
│   └── checksums.sha256
├── CITATION.cff
├── codemeta.json
└── ro-crate-metadata.json
```

Optional but strongly recommended:

- container recipe
- SBOM
- frozen benchmark manifest
- paper figure mapping file

## 9. Licensing strategy

Recommended approach:

- permissive root license for core repo (BSD-3-Clause recommended here)
- optional extras for backend integrations
- isolate GPL-sensitive integrations if they threaten the core distribution strategy
- document dataset terms separately from code licenses

## 10. Governance

Adopt lightweight formal governance from the beginning.

### Roles
- Steering group
- Core maintainers
- Triage / docs maintainers
- Modality maintainers

### Proposal process
Use CIPs — Computational Imaging Proposals — for major changes in:
- modality scope
- benchmark protocols
- dataset policy
- artifact format
- release process

### Decision rule
Consensus first, explicit vote only when needed.

## 11. Publication strategy

### Paper 1
Software paper once the core is stable enough for review.

Best initial targets:
- JOSS
- JORS

### Paper 2
Benchmark / methodology paper once benchmark tracks are stable and trusted.

Best likely targets:
- IEEE Transactions on Computational Imaging
- SIAM Journal on Imaging Sciences

### Internal rule
No manuscript figure should exist without a script and artifact reference.

## 12. Milestones

### Milestone 0 — Charter and structure
- finalize mission
- finalize scope
- freeze naming and repo conventions
- lock the artifact-bundle contract

### Milestone 1 — Core substrate
- implement specs, registry, and bundle machinery
- create CLI
- generate machine-readable skill catalog
- add tests, linting, CI

### Milestone 2 — CT and MRI
- build usable `ct-recon` and `mri-recon`
- add one benchmark spec per track
- ship demo runs

### Milestone 3 — Optical identity
- add `phase-retrieve`
- add public coherent-imaging benchmark starter
- extend report logic for optical diagnostics

### Milestone 4 — Professionalization
- docs site
- governance
- citation metadata
- DOI integration
- release automation
- paper reproducibility flow

### Milestone 5 — v1.0
- freeze release
- archive
- prepare software paper
- prepare benchmark paper

## 13. Codex execution model

This scaffold is intentionally prepared so Codex can work in clear phases.

### Codex should:
- read `AGENTS.md`
- read the relevant `SKILL.md` before editing any skill
- execute one work packet at a time from `codex/`
- keep interfaces stable unless a work packet explicitly changes them
- run tests and regenerate the catalog before finishing a phase

### Codex should not:
- invent new modality abstractions casually
- sneak modality-specific logic into the orchestrator
- bypass raw-data provenance rules
- manually edit paper figures
- collapse the repo into notebooks

## 14. Risks and mitigations

### Risk: scope explosion
Mitigation: stable v1 tracks are CT + MRI; coherent imaging stays beta.

### Risk: licensing confusion
Mitigation: keep adapters thin and document license boundaries early.

### Risk: benchmark invalidity
Mitigation: benchmark specs must encode data lineage, preprocessing, and baselines.

### Risk: agent drift
Mitigation: use root and nested `AGENTS.md` / overrides plus milestone work packets.

## 15. The shortest useful summary

ClawImaging should become the repo that makes computational imaging experiments easy to rerun,
easy to compare, easy to cite, and hard to fake.
