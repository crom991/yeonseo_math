from __future__ import annotations

import hmac

import pandas as pd
import streamlit as st

from app_config import setting
from arithmetic import DOMAIN_LABELS, DOMAIN_ORDER, LEVELS, levels_for_domain
from curriculum import domain_is_mastered, normalized_settings, unlocked_domains
from notifications import FEELING_LABELS
from storage import (
    StorageError,
    list_sessions,
    load_settings,
    save_settings,
    storage_mode,
)


st.set_page_config(
    page_title="부모용 학습 기록",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def authenticate_parent() -> bool:
    expected_pin = setting("PARENT_PIN")
    if not expected_pin:
        st.error(
            "부모 페이지가 아직 잠겨 있습니다. Streamlit Secrets에 `PARENT_PIN`을 "
            "등록하면 날짜별 기록과 설정을 볼 수 있습니다."
        )
        return False
    if st.session_state.get("parent_authenticated"):
        return True
    st.title("🔒 부모 확인")
    st.caption("학습 기록과 난이도 설정은 부모만 볼 수 있어요.")
    entered = st.text_input("부모 PIN", type="password", max_chars=20)
    if st.button("확인", type="primary", width="stretch"):
        if hmac.compare_digest(entered, expected_pin):
            st.session_state.parent_authenticated = True
            st.rerun()
        else:
            st.error("PIN이 맞지 않습니다.")
    st.page_link("app.py", label="학습 화면으로 돌아가기", icon="✏️")
    return False


def history_frame(sessions: list[dict]) -> pd.DataFrame:
    rows = []
    for session in reversed(sessions):
        elapsed = int(session.get("elapsed_seconds", 0))
        rows.append(
            {
                "날짜": session.get("local_date", "-"),
                "영역": DOMAIN_LABELS.get(str(session.get("domain")), "-"),
                "단계": LEVELS.get(int(session.get("final_level", 2)), LEVELS[2]).name,
                "문제": int(session.get("attempted", 0)),
                "정답": int(session.get("correct", 0)),
                "정확도(%)": float(session.get("accuracy", 0)),
                "시간(분)": round(elapsed / 60, 1),
                "아이 느낌": FEELING_LABELS.get(str(session.get("feeling", "")), "선택하지 않음"),
                "전송": "완료" if session.get("telegram_sent_at") else "미전송",
            }
        )
    return pd.DataFrame(rows)


def render_summary(sessions: list[dict]) -> None:
    st.subheader("날짜별 학습 기록")
    if not sessions:
        st.info("아직 저장된 학습 기록이 없습니다.")
        return
    total_attempted = sum(int(session.get("attempted", 0)) for session in sessions)
    total_correct = sum(int(session.get("correct", 0)) for session in sessions)
    average_accuracy = total_correct / total_attempted * 100 if total_attempted else 0
    cols = st.columns(4)
    cols[0].metric("학습한 날", f"{len({s.get('local_date') for s in sessions})}일")
    cols[1].metric("총 학습", f"{len(sessions)}회")
    cols[2].metric("총 문제", f"{total_attempted}개")
    cols[3].metric("전체 정확도", f"{average_accuracy:.0f}%")

    frame = history_frame(sessions)
    st.dataframe(
        frame,
        hide_index=True,
        width="stretch",
        column_config={
            "정확도(%)": st.column_config.NumberColumn(format="%.0f%%"),
            "시간(분)": st.column_config.NumberColumn(format="%.1f"),
        },
    )

    chart = frame.iloc[::-1].copy()
    if len(chart) >= 2:
        chart.index = range(len(chart))
        st.line_chart(chart, y="정확도(%)", x_label="학습 순서", y_label="정확도")


def render_settings(sessions: list[dict]) -> None:
    st.subheader("학습 영역과 난이도 설정")
    current = normalized_settings(load_settings())
    mode_label = "자동 성장" if current["mode"] == "automatic" else "부모 지정"
    mode = st.radio(
        "운영 방식",
        ["자동 성장", "부모 지정"],
        index=0 if mode_label == "자동 성장" else 1,
        horizontal=True,
    )
    enabled_labels = st.multiselect(
        "자동 성장에 포함할 영역",
        options=[DOMAIN_LABELS[domain] for domain in DOMAIN_ORDER],
        default=[DOMAIN_LABELS[domain] for domain in current["enabled_domains"]],
        help="선택한 순서가 아니라 덧셈→뺄셈→곱셈→나눗셈→소수→분수 순서로 열립니다.",
    )
    enabled_domains = [
        domain for domain in DOMAIN_ORDER if DOMAIN_LABELS[domain] in enabled_labels
    ] or ["addition"]
    focus_domain = st.selectbox(
        "부모가 지정할 영역",
        options=enabled_domains,
        index=(
            enabled_domains.index(current["focus_domain"])
            if current["focus_domain"] in enabled_domains
            else 0
        ),
        format_func=lambda domain: DOMAIN_LABELS[domain],
        disabled=mode != "부모 지정",
    )
    level_options = levels_for_domain(focus_domain)
    forced_level = st.selectbox(
        "시작 단계",
        options=level_options,
        index=(
            level_options.index(current["forced_level"])
            if current["forced_level"] in level_options
            else 0
        ),
        format_func=lambda level: f"{level}단계 · {LEVELS[level].name}",
        disabled=mode != "부모 지정",
    )
    submitted = st.button("설정 저장", type="primary")
    if submitted:
        save_settings(
            {
                "mode": "automatic" if mode == "자동 성장" else "focus",
                "enabled_domains": enabled_domains,
                "focus_domain": focus_domain,
                "forced_level": forced_level,
            }
        )
        st.success("다음 10분 학습부터 새 설정을 적용합니다.")
        st.rerun()

    unlocked = unlocked_domains(sessions, current)
    st.markdown(
        "**현재 자동으로 열린 영역:** "
        + ", ".join(DOMAIN_LABELS[domain] for domain in unlocked)
    )
    st.caption(
        "한 영역에서 최근 두 번 모두 5문제 이상 풀고 정확도 80% 이상이며 "
        "‘어려웠어요’가 아니면 다음 영역이 열립니다. 부모 지정은 이 규칙보다 우선합니다."
    )
    for domain in current["enabled_domains"]:
        status = "기준 충족" if domain_is_mastered(domain, sessions) else "연습 중"
        st.write(f"- {DOMAIN_LABELS[domain]}: {status}")


if authenticate_parent():
    top_left, top_right = st.columns([4, 1])
    with top_left:
        st.title("📊 부모용 학습 기록")
        st.caption("날짜별 결과를 보고 다음 학습 영역과 단계를 조절할 수 있습니다.")
    with top_right:
        if st.button("로그아웃", width="stretch"):
            st.session_state.parent_authenticated = False
            st.rerun()

    try:
        all_sessions = list_sessions()
        render_summary(all_sessions)
        st.divider()
        render_settings(all_sessions)
    except StorageError as exc:
        st.error(str(exc))

    if storage_mode() == "local":
        st.warning(
            "현재는 서버 로컬 파일에 기록합니다. Streamlit Cloud 재시작 후에도 보존하려면 "
            "운영 배포에서 Supabase Secrets를 연결해야 합니다."
        )
    else:
        st.success("온라인 학습 기록 저장소에 연결되어 있습니다.")

    st.page_link("app.py", label="학습 화면으로 돌아가기", icon="✏️")
