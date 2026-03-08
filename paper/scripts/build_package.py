from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]


def _load_builders():
    src_dir = ROOT / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from clawimaging.publication import build_benchmark_package, build_software_package

    return build_benchmark_package, build_software_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--package",
        required=True,
        choices=("software", "benchmark"),
        help="Publication package type to build.",
    )
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Build the benchmark package from the default smoke benchmark")
    parser.add_argument(
        "--source-bundle",
        help="Benchmark-run bundle or child run bundle to use as the benchmark package source.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.package == "software" and (args.demo or args.source_bundle):
        raise SystemExit("The software package does not accept --demo or --source-bundle.")
    if args.package == "benchmark" and not args.demo and not args.source_bundle:
        raise SystemExit("The benchmark package requires --demo or --source-bundle.")
    if args.package == "benchmark" and args.demo and args.source_bundle:
        raise SystemExit("Use exactly one of --demo or --source-bundle for the benchmark package.")

    build_benchmark_package, build_software_package = _load_builders()
    output_dir = Path(args.output).resolve()
    reproduction_command = (
        f"python3 paper/scripts/build_package.py --package {args.package}"
        f"{' --demo' if args.demo else ''}"
        f"{f' --source-bundle {Path(args.source_bundle).resolve()}' if args.source_bundle else ''}"
        f" --output {output_dir}"
    )
    if args.package == "software":
        build_software_package(output_dir, repo_root=ROOT, reproduction_command=reproduction_command)
    else:
        build_benchmark_package(
            output_dir,
            repo_root=ROOT,
            source_bundle=args.source_bundle,
            demo=args.demo,
            reproduction_command=reproduction_command,
        )
    print(f"Wrote {args.package} package bundle to {args.output}")


if __name__ == "__main__":
    main()
