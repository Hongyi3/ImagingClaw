# Reproducibility Contract

ClawImaging treats reproducibility as a first-class output.

## Minimum artifact bundle

```text
bundle/
├── report.md
├── metrics.json
├── resolved_config.yaml
├── figures/
├── tables/
├── reproducibility/
│   ├── commands.sh
│   ├── analysis_log.md
│   ├── environment.yml
│   └── checksums.sha256
├── CITATION.cff
├── codemeta.json
└── ro-crate-metadata.json
```

## Requirements

### report.md
Human-readable narrative of what ran, with assumptions and warnings.

### metrics.json
Machine-readable result summary.

### resolved_config.yaml
The exact configuration actually used, after defaults are resolved.

### commands.sh
The precise commands needed to reproduce the run.

### analysis_log.md
Chronological notes, warnings, and detected assumptions.

### environment snapshot
At least one environment capture format.

### checksums.sha256
Integrity hashes for inputs and generated outputs.

### citation and archive metadata
Sufficient metadata for citation, discovery, and archival packaging.

## Stretch goals

- HTML / PDF rendering
- container recipe
- SBOM
- benchmark summary manifest
- paper figure mapping file
