# Release Checklist

## Before any public release

- [ ] `python3 scripts/check_release_readiness.py` reviewed and warnings resolved
- [ ] Root license finalized
- [ ] `CITATION.cff` updated with real authors
- [ ] `.zenodo.json` updated
- [ ] `codemeta.json` updated
- [ ] docs build clean
- [ ] tests pass
- [ ] catalog regenerated
- [ ] benchmark specs validated
- [ ] artifact bundle contract tested
- [ ] security review of CLI and file writing paths completed

## Before v1.0

- [ ] one stable CT benchmark track
- [ ] one stable MRI benchmark track
- [ ] one coherent imaging beta track
- [ ] release benchmark workflow documented
- [ ] paper figure regeneration path working
- [ ] DOI workflow configured

## Machine-checkable audit

Run:

```bash
python3 scripts/check_release_readiness.py
```

The script validates benchmark and dataset specs and audits `CITATION.cff`, `codemeta.json`, and
`.zenodo.json` for parseability, placeholders, and cross-file mismatches. Manual release items
remain manual checklist steps.
