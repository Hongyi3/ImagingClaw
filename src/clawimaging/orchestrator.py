from __future__ import annotations

from typing import Any


def _score_query(query: str, trigger_keywords: list[str]) -> int:
    query_lower = query.lower()
    return sum(1 for keyword in trigger_keywords if keyword.lower() in query_lower)


def route_query(query: str, skills: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored: list[tuple[int, dict[str, Any]]] = []
    for skill in skills:
        score = _score_query(query, list(skill.get("trigger_keywords", [])))
        if score > 0:
            scored.append((score, skill))
    if not scored:
        return None
    scored.sort(key=lambda item: (-item[0], item[1].get("name", "")))
    return scored[0][1]
