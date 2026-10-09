from __future__ import annotations

import json
from typing import Mapping
from urllib import error, parse, request

from app_config import setting
from arithmetic import DOMAIN_LABELS, LEVELS
from profiles import profile_name


class TelegramNotificationError(RuntimeError):
    """텔레그램 학습 결과 전송 실패."""


FEELING_LABELS = {
    "easy": "쉬웠어요",
    "normal": "딱 좋았어요",
    "hard": "어려웠어요",
    "": "선택하지 않음",
}
APP_URL = "https://yeonseo-math.exambreaker-dev.workers.dev/"


def telegram_is_configured() -> bool:
    return bool(setting("TELEGRAM_BOT_TOKEN") and setting("TELEGRAM_CHAT_ID"))


def build_result_message(session: Mapping[str, object]) -> str:
    elapsed = int(session.get("elapsed_seconds", 0))
    minutes, seconds = divmod(elapsed, 60)
    final_level = int(session.get("final_level", session.get("recommended_level", 2)))
    feeling = FEELING_LABELS.get(str(session.get("feeling", "")), "선택하지 않음")
    return "\n".join(
        [
            "🧮 오늘의 연산 10분 학습 결과",
            f"👧 학습자: {profile_name(session.get('profile_id'))}",
            f"📅 날짜: {session.get('local_date', '-')}",
            f"📚 영역: {DOMAIN_LABELS.get(str(session.get('domain')), '-')}",
            f"✏️ 단계: {LEVELS[final_level].name}",
            f"✅ 정답: {session.get('correct', 0)}/{session.get('attempted', 0)}개",
            f"🎯 정확도: {float(session.get('accuracy', 0)):.0f}%",
            f"⏱ 학습 시간: {minutes}분 {seconds}초",
            f"🙂 오늘 느낌: {feeling}",
            f"➡️ 다음 권장: {LEVELS[int(session.get('recommended_level', final_level))].name}",
            "",
            f"🔗 연산 웹페이지: {APP_URL}",
        ]
    )


def send_telegram_message(message: str, *, timeout: float = 15.0) -> None:
    token = setting("TELEGRAM_BOT_TOKEN")
    chat_id = setting("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise TelegramNotificationError(
            "Telegram 설정이 필요합니다. Streamlit Secrets에 "
            "TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID를 등록해 주세요."
        )
    payload = parse.urlencode({"chat_id": chat_id, "text": message}).encode()
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        with request.urlopen(endpoint, data=payload, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise TelegramNotificationError("Telegram 메시지 전송에 실패했습니다.") from exc
    if not body.get("ok"):
        raise TelegramNotificationError("Telegram API가 전송을 거부했습니다.")
