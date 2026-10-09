from __future__ import annotations


PROFILES = {
    "yeonseo": {"id": "yeonseo", "name": "연서", "emoji": "🌷"},
    "haeun": {"id": "haeun", "name": "하은", "emoji": "🌼"},
}
DEFAULT_PROFILE_ID = "yeonseo"


def normalize_profile_id(value: object) -> str | None:
    profile_id = str(value or "").strip().lower()
    return profile_id if profile_id in PROFILES else None


def profile_name(profile_id: object) -> str:
    normalized = normalize_profile_id(profile_id) or DEFAULT_PROFILE_ID
    return str(PROFILES[normalized]["name"])
