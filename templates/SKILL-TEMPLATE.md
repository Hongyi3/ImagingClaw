---
name: your-skill-name
cli_alias: your-alias
description: One-line description of the skill and its modality.
version: 0.1.0
status: scaffold
modality: imaging-modality
measurement_domain: measurements
forward_model: operator-name
requires_raw_measurements: true
demo_command: python skills/your-skill-name/your_skill.py --demo --output /tmp/your-skill-demo
trigger_keywords:
  - keyword one
  - keyword two
chaining_partners:
  - benchmark-run
  - repro-export
install:
  kind: pip
  packages: []
  bins: []
---

# Skill Name

You are **Skill Name**, a specialized ClawImaging skill for [domain].

## Why this exists

Describe the research or engineering pain point this skill addresses.

## Core capabilities

1. Capability one
2. Capability two
3. Capability three

## Inputs

Describe accepted file types, metadata, and assumptions.

## Workflow

1. Validate inputs and required metadata
2. Resolve forward-model and calibration assumptions
3. Run the method / baseline
4. Emit an artifact bundle with metrics and report

## Methodology

Document the method clearly enough that a coding agent could follow the workflow even if the
implementation is incomplete.

## Output structure

```text
output/
├── report.md
├── metrics.json
├── figures/
├── tables/
└── reproducibility/
```

## Safety and provenance

- Do not hide preprocessing assumptions
- Record whether inputs are raw or processed
- Warn when required metadata are missing
- Route serious outputs through artifact bundles
