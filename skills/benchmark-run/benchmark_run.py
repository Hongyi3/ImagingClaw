from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]


def _load_workflow():
    src_dir = ROOT / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from clawimaging.skill_workflows.benchmark import default_benchmark_spec_path, run_benchmark

    return default_benchmark_spec_path, run_benchmark


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Benchmark spec YAML path")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the default CT benchmark spec and dispatch the supported smoke baseline",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.demo and not args.input:
        raise SystemExit("Provide --demo or --input.")

    default_benchmark_spec_path, run_benchmark = _load_workflow()
    spec_path = default_benchmark_spec_path(ROOT) if args.demo else Path(args.input).resolve()
    reproduction_command = (
        f"python3 skills/benchmark-run/benchmark_run.py"
        f"{' --demo' if args.demo else ''}"
        f"{f' --input {spec_path}' if not args.demo else ''}"
        f" --output {Path(args.output).resolve()}"
    )
    try:
        run_benchmark(
            output_dir=args.output,
            spec_path=spec_path,
            reproduction_command=reproduction_command,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Wrote benchmark bundle to {args.output}")


if __name__ == "__main__":
    main()
