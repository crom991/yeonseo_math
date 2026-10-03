from __future__ import annotations

from collections import Counter
from typing import Mapping, Sequence

from arithmetic import DOMAIN_ORDER, first_level_for_domain, levels_for_domain


DEFAULT_SETTINGS = {
    "mode": "automatic",
    "enabled_domains": list(DOMAIN_ORDER),
    "focus_domain": "addition",
    "forced_level": 2,
}

DOMAIN_INITIAL_LEVEL = {
    "addition": 2,
    "subtraction": 5,
    "multiplication": 8,
    "division": 11,
    "decimal": 14,
    "fraction": 16,
}


def normalized_settings(settings: Mapping[str, object] | None) -> dict:
    result = dict(DEFAULT_SETTINGS)
    if settings:
        result.update(settings)
    enabled = [domain for domain in DOMAIN_ORDER if domain in result["enabled_domains"]]
    result["enabled_domains"] = enabled or ["addition"]
    if result["focus_domain"] not in result["enabled_domains"]:
        result["focus_domain"] = result["enabled_domains"][0]
    forced_level = int(result.get("forced_level", first_level_for_domain(result["focus_domain"])))
    if forced_level not in levels_for_domain(result["focus_domain"]):
        forced_level = first_level_for_domain(result["focus_domain"])
    result["forced_level"] = forced_level
    result["mode"] = "focus" if result.get("mode") == "focus" else "automatic"
    return result


def domain_is_mastered(domain: str, sessions: Sequence[Mapping[str, object]]) -> bool:
    domain_sessions = [session for session in sessions if session.get("domain") == domain]
    if len(domain_sessions) < 2:
        return False
    recent = domain_sessions[-2:]
    return all(
        float(session.get("accuracy", 0)) >= 80
        and session.get("feeling") != "hard"
        and int(session.get("attempted", 0)) >= 5
        for session in recent
    )


def unlocked_domains(
    sessions: Sequence[Mapping[str, object]], settings: Mapping[str, object] | None
) -> list[str]:
    selected = normalized_settings(settings)["enabled_domains"]
    unlocked: list[str] = []
    for domain in selected:
        if not unlocked:
            unlocked.append(domain)
            continue
        previous = unlocked[-1]
        if domain_is_mastered(previous, sessions):
            unlocked.append(domain)
        else:
            break
    return unlocked


def choose_start_level(
    sessions: Sequence[Mapping[str, object]], settings: Mapping[str, object] | None
) -> int:
    config = normalized_settings(settings)
    if config["mode"] == "focus":
        return int(config["forced_level"])

    domains = unlocked_domains(sessions, config)
    counts = Counter(str(session.get("domain", "")) for session in sessions)
    chosen_domain = min(domains, key=lambda domain: (counts[domain], domains.index(domain)))
    domain_sessions = [session for session in sessions if session.get("domain") == chosen_domain]
    if not domain_sessions:
        return DOMAIN_INITIAL_LEVEL.get(chosen_domain, first_level_for_domain(chosen_domain))
    recommendation = int(domain_sessions[-1].get("recommended_level", first_level_for_domain(chosen_domain)))
    return recommendation if recommendation in levels_for_domain(chosen_domain) else first_level_for_domain(chosen_domain)
