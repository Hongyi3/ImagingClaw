from __future__ import annotations

import json
from pathlib import Path

import yaml


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md missing YAML frontmatter.")
    _, rest = text.split("---\n", 1)
    yaml_text, _body = rest.split("\n---\n", 1)
    return yaml.safe_load(yaml_text) or {}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    skills_dir = repo_root / "skills"
    payload = {"project": "ClawImaging", "skills": []}

    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        frontmatter = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        script_name = f"{skill_dir.name.replace('-', '_')}.py"
        has_script = (skill_dir / script_name).exists()
        entry = {
            "name": frontmatter.get("name", skill_dir.name),
            "cli_alias": frontmatter.get("cli_alias"),
            "description": frontmatter.get("description", ""),
            "version": frontmatter.get("version", "0.1.0"),
            "status": frontmatter.get("status", "scaffold"),
            "modality": frontmatter.get("modality"),
            "measurement_domain": frontmatter.get("measurement_domain"),
            "forward_model": frontmatter.get("forward_model"),
            "has_script": has_script,
            "has_tests": (skill_dir / "tests").exists(),
            "has_demo": has_script,
            "demo_command": frontmatter.get("demo_command"),
            "dependencies": frontmatter.get("install", {}).get("packages", []),
            "tags": [],
            "trigger_keywords": frontmatter.get("trigger_keywords", []),
            "chaining_partners": frontmatter.get("chaining_partners", []),
        }
        payload["skills"].append(entry)

    out_path = skills_dir / "catalog.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
