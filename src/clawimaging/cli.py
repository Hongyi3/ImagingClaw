from __future__ import annotations

import argparse
import json

from .orchestrator import route_query
from .registry import get_skill, list_skills


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="clawimaging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available skills")

    show = subparsers.add_parser("show-skill", help="Show one skill by name or alias")
    show.add_argument("name")

    route = subparsers.add_parser("route", help="Route a natural-language query to a skill")
    route.add_argument("query")

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "list":
        for skill in list_skills():
            alias = f" ({skill['cli_alias']})" if skill.get("cli_alias") else ""
            print(f"- {skill['name']}{alias}: {skill['description']}")
        return

    if args.command == "show-skill":
        skill = get_skill(args.name)
        if skill is None:
            raise SystemExit(f"Skill not found: {args.name}")
        print(json.dumps(skill, indent=2))
        return

    if args.command == "route":
        skill = route_query(args.query, list_skills())
        if skill is None:
            print("No matching skill found.")
        else:
            print(json.dumps(skill, indent=2))
        return


if __name__ == "__main__":
    main()
