from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def _load_ct_workflow():
    src_dir = ROOT / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from clawimaging.skill_workflows.ct import run_ct_reconstruction

    return run_ct_reconstruction


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Input .npy or self-describing .npz file")
    parser.add_argument("--config", help="Experiment config YAML path")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Run the deterministic CT demo")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.demo and not args.input and not args.config:
        raise SystemExit("Provide --demo, --input, or --config.")

    run_ct_reconstruction = _load_ct_workflow()
    output_dir = Path(args.output).resolve()
    reproduction_command = (
        f"python3 skills/ct-recon/ct_recon.py"
        f"{' --demo' if args.demo else ''}"
        f"{f' --input {Path(args.input).resolve()}' if args.input else ''}"
        f"{f' --config {Path(args.config).resolve()}' if args.config else ''}"
        f" --output {output_dir}"
    )
    run_ct_reconstruction(
        output_dir=output_dir,
        demo=args.demo,
        input_path=args.input,
        config_path=args.config,
        reproduction_command=reproduction_command,
    )
    print(f"Wrote CT bundle to {args.output}")


if __name__ == "__main__":
    main()
