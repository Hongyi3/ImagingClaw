.PHONY: install-dev test lint typecheck catalog demo-ct demo-mri demo-phase

install-dev:
	python -m pip install -e .[dev]

test:
	python -m pytest

lint:
	ruff check .

typecheck:
	mypy src

catalog:
	python scripts/generate_catalog.py

demo-ct:
	python skills/ct-recon/ct_recon.py --demo --output /tmp/clawimaging-ct-demo

demo-mri:
	python skills/mri-recon/mri_recon.py --demo --output /tmp/clawimaging-mri-demo

demo-phase:
	python skills/phase-retrieve/phase_retrieve.py --demo --output /tmp/clawimaging-phase-demo
