# CLAUDE.md — ClawImaging Agent Routing Notes

You are working inside ClawImaging, a computational imaging repository organized around skills,
an orchestrator, and reproducibility bundles.

Every answer or code path should trace back to either:
- a `SKILL.md` methodology contract,
- a declared benchmark / dataset specification,
- or a generated artifact bundle.

## Routing table

| User intent / topic | Preferred skill | Action |
|---|---|---|
| CT reconstruction, sinograms, tomography, low-dose CT | `skills/ct-recon/` | Use CT workflow and report bundle |
| MRI reconstruction, k-space, coils, parallel imaging | `skills/mri-recon/` | Use MRI workflow and report bundle |
| Phase retrieval, coherent imaging, Fourier magnitude inversion | `skills/phase-retrieve/` | Use phase retrieval workflow |
| Compare methods fairly, run benchmark tracks, aggregate metrics | `skills/benchmark-run/` | Load benchmark spec and benchmark harness |
| Turn an experiment into an archive-ready reproducibility package | `skills/repro-export/` | Emit export bundle |
| Recreate paper figures or tables from artifacts | `skills/paper-figure/` | Use figure regeneration workflow |
| Unsure which skill applies, multi-step request | `src/clawimaging/orchestrator.py` | Route using keywords and catalog |

## Rules

1. Read the relevant `SKILL.md` before changing skill code.
2. Keep benchmark logic separate from one-off demos.
3. Do not guess data provenance.
4. All publication outputs should be regenerable from code and configs.
5. Prefer transparent baselines over flashy but opaque defaults.
