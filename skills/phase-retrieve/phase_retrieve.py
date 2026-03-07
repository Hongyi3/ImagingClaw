from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def _load_run_scaffold_skill():
    src_dir = ROOT / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from clawimaging.scaffold_skill import run_scaffold_skill

    return run_scaffold_skill


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Input file path")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run scaffold demo")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.demo and not args.input:
        raise SystemExit("Provide --demo or --input.")
    run_scaffold_skill = _load_run_scaffold_skill()
    run_scaffold_skill(
        skill_name="phase-retrieve",
        title="Phase Retrieval Demo",
        output_dir=args.output,
        summary="Scaffold coherent-imaging bundle demonstrating the report and reproducibility contract.",
        input_path=args.input,
    )
    print(f"Wrote scaffold bundle to {args.output}")


if __name__ == "__main__":
    main()
