from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Mapping
from urllib import error, parse, request
from uuid import uuid4

from app_config import setting
from curriculum import DEFAULT_SETTINGS, normalized_settings


DATA_DIR = Path(os.environ.get("MATHWEB_DATA_DIR", "data/private"))
SESSIONS_PATH = DATA_DIR / "session_history.json"
SETTINGS_PATH = DATA_DIR / "learning_settings.json"


class StorageError(RuntimeError):
    """학습 기록 저장소 오류."""


def storage_mode() -> str:
    return "supabase" if setting("SUPABASE_URL") and setting("SUPABASE_SERVICE_ROLE_KEY") else "local"


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(f"저장 파일을 읽지 못했습니다: {path.name}") from exc


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(path)
    except OSError as exc:
        raise StorageError(f"저장 파일을 쓰지 못했습니다: {path.name}") from exc


def _supabase_request(method: str, table: str, *, query: str = "", payload=None):
    base_url = setting("SUPABASE_URL").rstrip("/")
    key = setting("SUPABASE_SERVICE_ROLE_KEY")
    url = f"{base_url}/rest/v1/{table}{query}"
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation,resolution=merge-duplicates",
    }
    try:
        req = request.Request(url, data=body, headers=headers, method=method)
        with request.urlopen(req, timeout=12) as response:
            raw = response.read().decode("utf-8")
    except (error.URLError, TimeoutError) as exc:
        raise StorageError("온라인 학습 기록 저장소에 연결하지 못했습니다.") from exc
    return json.loads(raw) if raw else None


def list_sessions() -> list[dict]:
    if storage_mode() == "supabase":
        rows = _supabase_request(
            "GET", "math_sessions", query="?select=*&order=completed_at.asc"
        )
        return list(rows or [])
    return list(_read_json(SESSIONS_PATH, []))


def save_session(session: Mapping[str, object]) -> dict:
    record = dict(session)
    record.setdefault("id", uuid4().hex)
    if storage_mode() == "supabase":
        rows = _supabase_request("POST", "math_sessions", payload=record)
        return dict((rows or [record])[0])
    sessions = list_sessions()
    sessions.append(record)
    _write_json(SESSIONS_PATH, sessions)
    return record


def update_session(session_id: str, changes: Mapping[str, object]) -> None:
    if storage_mode() == "supabase":
        encoded = parse.quote(session_id, safe="")
        _supabase_request(
            "PATCH", "math_sessions", query=f"?id=eq.{encoded}", payload=dict(changes)
        )
        return
    sessions = list_sessions()
    for session in sessions:
        if session.get("id") == session_id:
            session.update(changes)
            _write_json(SESSIONS_PATH, sessions)
            return
    raise StorageError("수정할 학습 기록을 찾지 못했습니다.")


def load_settings() -> dict:
    if storage_mode() == "supabase":
        rows = _supabase_request(
            "GET", "math_settings", query="?id=eq.family&select=settings"
        )
        if rows:
            return normalized_settings(rows[0].get("settings", {}))
        return dict(DEFAULT_SETTINGS)
    return normalized_settings(_read_json(SETTINGS_PATH, DEFAULT_SETTINGS))


def save_settings(settings: Mapping[str, object]) -> dict:
    config = normalized_settings(settings)
    if storage_mode() == "supabase":
        _supabase_request(
            "POST",
            "math_settings",
            payload={
                "id": "family",
                "settings": config,
                "updated_at": datetime.now().astimezone().isoformat(),
            },
        )
    else:
        _write_json(SETTINGS_PATH, config)
    return config
