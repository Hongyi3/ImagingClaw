# Contributing to ClawImaging

We welcome contributions in computational imaging, inverse problems, benchmarking, datasets,
reproducibility tooling, and documentation.

## Before you start

Read:

- `PROJECT-CHARTER.md`
- `AGENTS.md`
- `docs/architecture.md`
- `docs/benchmark-policy.md`
- `docs/dataset-policy.md`

## How to contribute a new skill

### 1. Copy the template

```bash
mkdir -p skills/your-skill-name
cp templates/SKILL-TEMPLATE.md skills/your-skill-name/SKILL.md
```

### 2. Define the skill

Edit `SKILL.md` and complete:

- YAML frontmatter
- capability summary
- inputs
- workflow
- methodology
- output structure
- safety and provenance notes

### 3. Add implementation code

Suggested layout:

```text
skills/your-skill-name/
├── SKILL.md
├── your_skill.py
├── tests/
└── examples/
```

### 4. Regenerate the catalog

```bash
python scripts/generate_catalog.py
```

### 5. Run tests

```bash
python -m pytest
```

### 6. Submit a focused change

Preferred branch names:

- `feat/<skill-name>`
- `fix/<area>`
- `docs/<area>`

## Skill guidelines

1. One skill, one job
2. Local-first by default
3. Benchmark-compatible output whenever applicable
4. All serious runs emit artifact bundles
5. Document data lineage and preprocessing assumptions
6. Keep routing keywords specific and useful
7. Avoid hardcoded paths or machine-specific assumptions

## Benchmark contribution guidelines

A benchmark contribution is not complete unless it defines:

- dataset and version
- access policy
- splits
- forward model
- metrics
- seeds
- baseline classes
- hardware reporting expectations

## Paper contribution guidelines

Anything under `paper/` must be script-generated. Do not commit manually edited figures or
hand-copied tables.
