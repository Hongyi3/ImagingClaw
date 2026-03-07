from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RouteMatch:
    skill: dict[str, Any]
    score: int
    matched_keywords: list[str]


def _matched_keywords(query: str, trigger_keywords: list[str]) -> list[str]:
    query_lower = query.lower()
    return [keyword for keyword in trigger_keywords if keyword.lower() in query_lower]


def explain_route(query: str, skills: list[dict[str, Any]]) -> RouteMatch | None:
    scored: list[RouteMatch] = []
    for skill in skills:
        matched_keywords = _matched_keywords(query, list(skill.get("trigger_keywords", [])))
        if matched_keywords:
            scored.append(
                RouteMatch(
                    skill=skill,
                    score=len(matched_keywords),
                    matched_keywords=matched_keywords,
                )
            )
    if not scored:
        return None
    scored.sort(key=lambda item: (-item.score, item.skill.get("name", "")))
    return scored[0]


def route_query(query: str, skills: list[dict[str, Any]]) -> dict[str, Any] | None:
    match = explain_route(query, skills)
    if match is None:
        return None
    return match.skill
