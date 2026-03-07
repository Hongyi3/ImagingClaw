from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any, TextIO

from .orchestrator import explain_route, route_query
from .registry import get_skill, list_skills


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="clawimaging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available skills")
    list_parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit the skill catalog as JSON.",
    )

    show = subparsers.add_parser("show-skill", help="Show one skill by name or alias")
    show.add_argument("name")

    route = subparsers.add_parser("route", help="Route a natural-language query to a skill")
    route.add_argument("query")
    route.add_argument(
        "--explain",
        action="store_true",
        help="Include route score and matched keywords in the output.",
    )

    return parser


def _write_json(payload: Any, *, stream: TextIO) -> None:
    print(json.dumps(payload, indent=2), file=stream)


def run(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    if args.command == "list":
        skills = list_skills()
        if args.as_json:
            _write_json(skills, stream=stdout)
            return 0
        for skill_record in skills:
            alias = f" ({skill_record['cli_alias']})" if skill_record.get("cli_alias") else ""
            print(
                f"- {skill_record['name']}{alias}: {skill_record['description']}",
                file=stdout,
            )
        return 0

    if args.command == "show-skill":
        selected_skill = get_skill(args.name)
        if selected_skill is None:
            print(f"Skill not found: {args.name}", file=stderr)
            return 1
        _write_json(selected_skill, stream=stdout)
        return 0

    if args.command == "route":
        skills = list_skills()
        if args.explain:
            match = explain_route(args.query, skills)
            if match is None:
                _write_json(
                    {"skill": None, "score": 0, "matched_keywords": []},
                    stream=stdout,
                )
                return 0
            _write_json(
                {
                    "skill": match.skill,
                    "score": match.score,
                    "matched_keywords": match.matched_keywords,
                },
                stream=stdout,
            )
            return 0
        selected_skill = route_query(args.query, skills)
        if selected_skill is None:
            print("No matching skill found.", file=stdout)
            return 0
        _write_json(selected_skill, stream=stdout)
        return 0

    print("Unknown command.", file=stderr)
    return 1


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
