# Release Checklist

## Before any public release

- [ ] `python3 scripts/sync_release_metadata.py` run after editing `release/v1.0.yaml`
- [ ] `python3 scripts/check_release_readiness.py` passes cleanly
- [ ] Root license finalized
- [ ] `release/v1.0.yaml` updated with current release identity
- [ ] `CITATION.cff` synchronized from `release/v1.0.yaml`
- [ ] `.zenodo.json` synchronized from `release/v1.0.yaml`
- [ ] `codemeta.json` synchronized from `release/v1.0.yaml`
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
- [ ] software-paper support package scriptable
- [ ] benchmark-paper support package scriptable
- [ ] DOI workflow state recorded truthfully in `release/v1.0.yaml`

## Machine-checkable audit

Run:

```bash
python3 scripts/sync_release_metadata.py
python3 scripts/check_release_readiness.py
```

The release sync script renders root metadata from `release/v1.0.yaml`. The readiness audit then
validates benchmark specs, dataset specs, the release manifest, and the synchronized
`CITATION.cff`, `codemeta.json`, and `.zenodo.json` files for parseability and exact manifest
consistency. Manual release items remain manual checklist steps.
