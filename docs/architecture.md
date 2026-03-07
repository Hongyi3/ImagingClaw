# Architecture

## Overview

ClawImaging is organized as a small core package plus explicit skills.

```text
natural-language request / CLI request
                │
                ▼
         Orchestrator / router
                │
       ┌────────┼────────┬────────────┬────────────┐
       ▼        ▼        ▼            ▼            ▼
   ct-recon  mri-recon  phase-    benchmark-   repro-export
                        retrieve      run
                │
                ▼
         Artifact bundle layer
                │
                ▼
 report.md / metrics.json / figures / tables / commands / env / checksums
```

## Layering

### Core layer
Owns:

- experiment data models
- skill registry loading
- routing
- artifact creation
- report assembly helpers

### Skill layer
Owns:

- domain-specific input validation
- forward-model and inverse-method choices
- metrics and diagnostics
- modality-specific report sections

### Adapter layer
Owns:

- integration with external libraries
- lazy imports
- backend-specific configuration translation

## Anti-patterns

Do not:

- place modality logic in the orchestrator
- place benchmark policy in skill scripts
- bypass the artifact layer for serious runs
- couple public interfaces tightly to one external backend
