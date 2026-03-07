# Dataset Policy

## Core rule

The repository must always make it clear whether a method is operating on:

- raw measurements
- partially processed measurements
- reconstructed images
- synthetic measurements

This classification is stored as `data_kind` in the dataset registry and must never be implicit.

## Mandatory dataset registry fields

Each entry in `datasets/registry.yaml` must declare:

- canonical name
- version
- modality
- measurement domain
- data kind
- access mode
- source citation or URL
- redistribution policy
- license / terms
- labels / annotations
- known preprocessing assumptions
- dataset card path
- notes

## Data lineage rules

- Every benchmark spec must point to a registry entry by dataset name and version
- Every benchmark run must record dataset version and split
- All preprocessing must be declared
- If processed images are transformed back into a measurement domain, the report must say so
  explicitly
- Synthetic data must remain labeled synthetic all the way through the artifact bundle

## Controlled-access datasets

Datasets governed by data-use agreements can be supported, but the repo must not pretend they are
frictionless public resources. Their wrappers and cards should document:

- how access is requested
- what cannot be redistributed
- publication obligations
- whether only derived metrics can be shared

## Dataset documentation

Every registry entry must point to a dataset-specific card under `datasets/cards/` or another
explicit documentation path. The card should be concise but citable enough to keep the registry
truthful.

## Practical v1 guidance

### CT
Use LoDoPaB-CT as the flagship open benchmark track.

### MRI
Support fastMRI, but treat it as an access-controlled benchmark track.

### Coherent imaging
Start with a small public or synthetic starter dataset that makes the coherent-imaging workflow
explicit while clearly marking synthetic provenance.
