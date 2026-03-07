from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def _load_workflows():
    src_dir = ROOT / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from clawimaging.skill_workflows.phase import run_phase_retrieval
    from clawimaging.skill_workflows.repro import run_repro_export

    return run_phase_retrieval, run_repro_export


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Source artifact bundle path")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run the repro-export demo")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.demo and not args.input:
        raise SystemExit("Provide --demo or --input.")

    run_phase_retrieval, run_repro_export = _load_workflows()
    output_dir = Path(args.output).resolve()
    source_bundle: Path
    if args.demo:
        temp_root = Path(tempfile.mkdtemp(prefix="clawimaging-repro-"))
        source_bundle = temp_root / "phase-source"
        run_phase_retrieval(
            output_dir=source_bundle,
            demo=True,
            reproduction_command=(
                "python3 skills/phase-retrieve/phase_retrieve.py"
                f" --demo --output {source_bundle}"
            ),
        )
    else:
        source_bundle = Path(args.input).resolve()

    reproduction_command = (
        f"python3 skills/repro-export/repro_export.py"
        f"{' --demo' if args.demo else ''}"
        f"{f' --input {source_bundle}' if not args.demo else ''}"
        f" --output {output_dir}"
    )
    run_repro_export(
        output_dir=output_dir,
        source_bundle=source_bundle,
        repo_root=ROOT,
        reproduction_command=reproduction_command,
    )
    print(f"Wrote repro export bundle to {args.output}")


if __name__ == "__main__":
    main()
