from __future__ import annotations

from datetime import datetime
import html
import random
import time
from zoneinfo import ZoneInfo

import streamlit as st

from arithmetic import (
    DOMAIN_LABELS,
    LEVELS,
    Problem,
    SessionSummary,
    adjust_level_for_feeling,
    choose_next_level,
    is_correct_answer,
    make_problem,
    parse_answer,
    summarize_session,
)
from curriculum import choose_start_level
from notifications import (
    FEELING_LABELS,
    TelegramNotificationError,
    build_result_message,
    send_telegram_message,
    telegram_is_configured,
)
from storage import (
    StorageError,
    list_sessions,
    load_settings,
    save_session,
    storage_mode,
    update_session,
)


SESSION_SECONDS = 10 * 60
KST = ZoneInfo("Asia/Seoul")


st.set_page_config(
    page_title="오늘의 연산 10분",
    page_icon="✏️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #fffaf0 0%, #f0f9ff 100%);
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 560px; padding: .65rem 1rem 2rem; }
    .hero { padding: 1.2rem 0 .4rem; text-align: center; }
    .hero h1 {
        color: #183153;
        font-size: clamp(1.8rem, 8vw, 2.6rem);
        margin-bottom: .35rem;
    }
    .hero p { color: #52657a; font-size: 1rem; }
    .question-card {
        background: white;
        border: 1px solid #dbeafe;
        border-radius: 24px;
        box-shadow: 0 12px 32px rgba(30, 64, 175, .08);
        margin: .45rem 0 .7rem;
        padding: 1.25rem .75rem;
        text-align: center;
    }
    .level-label { color: #64748b; font-size: .9rem; font-weight: 700; }
    .problem {
        color: #172554;
        font-size: clamp(2.7rem, 14vw, 5rem);
        font-weight: 800;
        letter-spacing: .02em;
        line-height: 1.25;
        margin-top: .3rem;
    }
    .feedback {
        border-radius: 16px;
        margin: .35rem 0 .55rem;
        padding: .65rem 1rem;
        text-align: center;
        font-weight: 700;
    }
    .feedback.good { background: #dcfce7; color: #166534; }
    .feedback.try { background: #ffedd5; color: #9a3412; }
    .summary-card {
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 28px rgba(15, 23, 42, .08);
        padding: 1.2rem;
        margin: .8rem 0;
    }
    .metric-big { color: #172554; font-size: 1.8rem; font-weight: 800; }
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input {
        font-size: 2rem;
        text-align: center;
        min-height: 64px;
        border-radius: 16px;
    }
    [data-testid="stNumberInputContainer"] {
        min-height: 64px;
    }
    div[data-testid="stNumberInput"] input::placeholder,
    div[data-testid="stTextInput"] input::placeholder {
        font-size: 1.25rem;
    }
    [data-testid="stNumberInputStepDown"],
    [data-testid="stNumberInputStepUp"],
    [data-testid="InputInstructions"] {
        display: none !important;
    }
    div[data-testid="stForm"] {
        background: transparent;
        border: 0;
        padding: 0;
    }
    div[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        align-items: flex-end;
        flex-wrap: nowrap;
        gap: .55rem;
    }
    div[data-testid="stForm"] [data-testid="stColumn"] {
        min-width: 0 !important;
    }
    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button {
        min-height: 64px;
        padding-left: .7rem;
        padding-right: .7rem;
        white-space: nowrap;
    }
    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stButton"] button,
    div[data-testid="stPageLink"] a {
        min-height: 54px;
        border-radius: 14px;
        font-size: 1.05rem;
        font-weight: 800;
        width: 100%;
    }
    @media (max-width: 480px) {
        .block-container { padding: .2rem .75rem 1.5rem; }
        .question-card { padding: 1rem .55rem; }
        .problem { font-size: clamp(2.5rem, 13vw, 4rem); }
        div[data-testid="stNumberInput"] input::placeholder,
        div[data-testid="stTextInput"] input::placeholder { font-size: 1.1rem; }
        div[data-testid="stFormSubmitButton"] button { font-size: .95rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_state() -> None:
    defaults = {
        "screen": "intro",
        "records": [],
        "current_level": 2,
        "start_level": 2,
        "question_number": 1,
        "current_problem": None,
        "started_at": None,
        "problem_started_at": None,
        "finished_at": None,
        "last_feedback": None,
        "recent_signatures": [],
        "result_record": None,
        "result_storage_error": None,
        "saved_feeling": "",
        "telegram_sent": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def new_problem(level: int) -> Problem:
    recent = set(st.session_state.recent_signatures[-12:])
    problem = make_problem(level, random.Random(), exclude=recent)
    st.session_state.recent_signatures.append(problem.signature)
    st.session_state.problem_started_at = time.time()
    return problem


def start_session() -> None:
    try:
        start_level = choose_start_level(list_sessions(), load_settings())
    except StorageError:
        start_level = 2
    now = time.time()
    st.session_state.screen = "quiz"
    st.session_state.records = []
    st.session_state.current_level = start_level
    st.session_state.start_level = start_level
    st.session_state.question_number = 1
    st.session_state.started_at = now
    st.session_state.finished_at = None
    st.session_state.last_feedback = None
    st.session_state.recent_signatures = []
    st.session_state.result_record = None
    st.session_state.result_storage_error = None
    st.session_state.saved_feeling = ""
    st.session_state.telegram_sent = False
    st.session_state.current_problem = new_problem(start_level)


def finish_session() -> None:
    if st.session_state.finished_at is None:
        st.session_state.finished_at = time.time()
    st.session_state.screen = "result"


def remaining_seconds() -> int:
    if st.session_state.started_at is None:
        return SESSION_SECONDS
    return max(0, SESSION_SECONDS - int(time.time() - st.session_state.started_at))


def submit_answer(answer_text: str) -> None:
    problem: Problem = st.session_state.current_problem
    if parse_answer(answer_text) is None:
        st.session_state.last_feedback = {
            "kind": "input",
            "message": "답을 숫자로 적어 주세요. 분수는 3/4처럼 적어요.",
        }
        return

    is_correct = is_correct_answer(problem, answer_text)
    elapsed = max(0.1, time.time() - st.session_state.problem_started_at)
    st.session_state.records.append(
        {
            "level": problem.level,
            "expression": problem.expression,
            "answer": problem.answer_text,
            "user_answer": answer_text.strip(),
            "correct": is_correct,
            "seconds": round(elapsed, 2),
        }
    )

    if is_correct:
        st.session_state.last_feedback = {
            "kind": "good",
            "message": random.choice(
                [
                    "정답이에요! 잘했어요 🌟",
                    "좋아요, 정확해요! 👏",
                    "멋져요! 다음 문제도 천천히 해봐요 😊",
                ]
            ),
        }
    else:
        safe_expression = html.escape(problem.expression.replace(" = ?", ""))
        st.session_state.last_feedback = {
            "kind": "try",
            "message": f"괜찮아요. {safe_expression}의 답은 {problem.answer_text}예요. 다음 문제는 천천히 해봐요.",
        }

    st.session_state.current_level = choose_next_level(
        st.session_state.current_level, st.session_state.records
    )
    st.session_state.question_number += 1
    st.session_state.current_problem = new_problem(st.session_state.current_level)


def render_header(subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><h1>오늘의 연산 10분</h1><p>{html.escape(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )


@st.fragment(run_every="1s")
def render_timer() -> None:
    remaining = remaining_seconds()
    minutes, seconds = divmod(remaining, 60)
    progress = 1 - remaining / SESSION_SECONDS
    st.progress(
        progress,
        text=f"오늘 연습 {int(progress * 100)}% · 남은 시간 {minutes}:{seconds:02d}",
    )
    if remaining <= 0:
        finish_session()
        st.rerun()


def next_study_label() -> str:
    try:
        level = choose_start_level(list_sessions(), load_settings())
        return f"오늘은 {DOMAIN_LABELS[LEVELS[level].domain]} · {LEVELS[level].name}부터 시작해요."
    except StorageError:
        return "오늘은 두 자리 수 덧셈부터 시작해요."


def render_intro() -> None:
    render_header("한 문제씩 차근차근, 정확하게 풀어 봐요.")
    st.markdown(
        f"""
        <div class="summary-card">
          <div class="metric-big">⏱️ 10분</div>
          <p>{next_study_label()}</p>
          <p>최근 결과와 오늘 느낌을 보고 다음 영역과 단계를 자동으로 정해요.</p>
          <p>빨리 푸는 것보다 <strong>정확하게 푸는 것</strong>이 더 중요해요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("연습 시작", type="primary", width="stretch"):
        start_session()
        st.rerun()
    st.page_link(
        "pages/1_부모_학습기록.py",
        label="부모용 학습 기록과 설정",
        icon="👨‍👩‍👧",
        width="stretch",
    )


def render_feedback() -> None:
    feedback = st.session_state.last_feedback
    if not feedback:
        return
    css_class = "good" if feedback["kind"] == "good" else "try"
    st.markdown(
        f'<div class="feedback {css_class}">{feedback["message"]}</div>',
        unsafe_allow_html=True,
    )


def render_answer_input(problem: Problem, key: str):
    if problem.answer_kind == "fraction":
        return st.text_input(
            "답",
            key=key,
            placeholder="예: 3/4",
            autocomplete="off",
            label_visibility="collapsed",
        )
    if problem.answer_kind == "decimal":
        value = st.number_input(
            "답",
            key=key,
            value=None,
            step=0.1,
            format="%.1f",
            placeholder="예: 4.2",
            label_visibility="collapsed",
        )
    else:
        value = st.number_input(
            "답",
            key=key,
            value=None,
            step=1,
            format="%d",
            placeholder="답을 숫자로 적어 보세요",
            label_visibility="collapsed",
        )
    return "" if value is None else str(value)


def render_quiz() -> None:
    if remaining_seconds() <= 0:
        finish_session()
        st.rerun()

    render_timer()
    render_feedback()
    problem: Problem = st.session_state.current_problem
    level_info = LEVELS[problem.level]
    st.markdown(
        f"""
        <div class="question-card">
          <div class="level-label">{st.session_state.question_number}번째 문제 · {html.escape(DOMAIN_LABELS[level_info.domain])} · {html.escape(level_info.name)}</div>
          <div class="problem">{html.escape(problem.expression)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    key = f"answer_{st.session_state.question_number}"
    with st.form(key=f"form_{key}", clear_on_submit=True):
        answer_column, submit_column = st.columns([3.1, 1.25], gap="small")
        with answer_column:
            answer_text = render_answer_input(problem, key)
        with submit_column:
            submitted = st.form_submit_button(
                "정답 확인",
                type="primary",
                width="stretch",
            )
    if submitted:
        submit_answer(answer_text)
        st.rerun()

    with st.expander("오늘은 여기까지 할래요"):
        st.caption("10분 전에도 그만할 수 있어요. 푼 문제까지 결과에 담겨요.")
        if st.button("연습 마치기", width="stretch"):
            finish_session()
            st.rerun()


def elapsed_seconds() -> int:
    if st.session_state.started_at is None:
        return 0
    end = st.session_state.finished_at or time.time()
    return min(SESSION_SECONDS, int(end - st.session_state.started_at))


def ensure_result_saved(summary: SessionSummary) -> dict | None:
    if st.session_state.result_record is not None:
        return st.session_state.result_record
    completed_at = datetime.now(KST)
    final_level = (
        int(st.session_state.records[-1]["level"])
        if st.session_state.records
        else st.session_state.start_level
    )
    record = {
        "completed_at": completed_at.isoformat(),
        "local_date": completed_at.date().isoformat(),
        "domain": summary.domain,
        "start_level": st.session_state.start_level,
        "final_level": final_level,
        "recommended_level": summary.recommended_level,
        "attempted": summary.attempted,
        "correct": summary.correct,
        "accuracy": round(summary.accuracy, 1),
        "elapsed_seconds": summary.elapsed_seconds,
        "feeling": "",
        "telegram_sent_at": None,
        "records": list(st.session_state.records),
    }
    try:
        saved = save_session(record)
    except StorageError as exc:
        st.session_state.result_storage_error = str(exc)
        return None
    st.session_state.result_record = saved
    return saved


def save_feeling(feeling: str, summary: SessionSummary) -> None:
    record = st.session_state.result_record
    if not record:
        return
    if feeling == "normal":
        recommended = summary.recommended_level
    else:
        recommended = adjust_level_for_feeling(
            int(record["final_level"]), feeling, summary.accuracy
        )
    try:
        update_session(record["id"], {"feeling": feeling, "recommended_level": recommended})
    except StorageError as exc:
        st.error(str(exc))
        return
    record.update({"feeling": feeling, "recommended_level": recommended})
    st.session_state.saved_feeling = feeling
    st.success("오늘 느낀 난이도를 저장했어요.")


def send_result_to_parent() -> None:
    record = st.session_state.result_record
    if not record:
        st.error("저장된 학습 결과가 없어 보낼 수 없습니다.")
        return
    try:
        send_telegram_message(build_result_message(record))
        sent_at = datetime.now(KST).isoformat()
        update_session(record["id"], {"telegram_sent_at": sent_at})
    except (TelegramNotificationError, StorageError) as exc:
        st.error(str(exc))
        return
    record["telegram_sent_at"] = sent_at
    st.session_state.telegram_sent = True
    st.success("아빠에게 오늘 학습 결과를 보냈어요! 📩")


def render_result() -> None:
    records = st.session_state.records
    summary: SessionSummary = summarize_session(records, elapsed_seconds())
    saved = ensure_result_saved(summary)

    render_header("오늘 연습을 마쳤어요. 끝까지 해낸 것이 가장 멋져요!")
    cols = st.columns(3)
    cols[0].metric("푼 문제", f"{summary.attempted}개")
    cols[1].metric("맞힌 문제", f"{summary.correct}개")
    cols[2].metric("정확도", f"{summary.accuracy:.0f}%")

    minutes, seconds = divmod(summary.elapsed_seconds, 60)
    recommendation = int(saved["recommended_level"]) if saved else summary.recommended_level
    st.markdown(
        f"""
        <div class="summary-card">
          <div class="metric-big">걸린 시간 {minutes}분 {seconds}초</div>
          <p>{html.escape(summary.message)}</p>
          <p><strong>오늘 영역:</strong> {html.escape(DOMAIN_LABELS[summary.domain])}</p>
          <p><strong>다음 권장 단계:</strong> {html.escape(LEVELS[recommendation].name)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("오늘 문제는 어땠나요?")
    label_to_code = {
        "😊 쉬웠어요": "easy",
        "🙂 딱 좋았어요": "normal",
        "😥 어려웠어요": "hard",
    }
    saved_code = st.session_state.saved_feeling or (saved or {}).get("feeling", "")
    labels = list(label_to_code)
    index = next(
        (position for position, label in enumerate(labels) if label_to_code[label] == saved_code),
        None,
    )
    feeling_label = st.radio(
        "체감 난이도",
        labels,
        index=index,
        horizontal=True,
        label_visibility="collapsed",
    )
    if st.button(
        "오늘 느낌 저장",
        disabled=feeling_label is None or saved is None,
        width="stretch",
    ):
        save_feeling(label_to_code[feeling_label], summary)
        st.rerun()

    wrong = [record for record in records if not record["correct"]]
    if wrong:
        with st.expander("틀린 문제 다시 보기"):
            for record in wrong[-5:]:
                st.write(
                    f"{record['expression'].replace(' = ?', '')} = {record['answer']} "
                    f"(적은 답: {record['user_answer']})"
                )
    else:
        st.success("오늘 푼 문제를 모두 맞혔어요! 🌟")

    if st.session_state.result_storage_error:
        st.warning(st.session_state.result_storage_error)
    elif storage_mode() == "local":
        st.caption("현재 기록은 이 서버에 저장됩니다. 운영 배포에서는 온라인 저장소를 연결할 예정이에요.")

    if st.button("새로 10분 연습", type="primary", width="stretch"):
        start_session()
        st.rerun()

    configured = telegram_is_configured()
    already_sent = st.session_state.telegram_sent or bool((saved or {}).get("telegram_sent_at"))
    if st.button(
        "아빠에게 학습 결과 보내기",
        icon=":material/send:",
        disabled=not configured or saved is None or already_sent,
        width="stretch",
    ):
        send_result_to_parent()
        st.rerun()
    if already_sent:
        st.caption("오늘 결과를 이미 보냈어요.")
    elif not configured:
        st.caption(
            "전송을 켜려면 Streamlit Secrets에 기존 `TELEGRAM_BOT_TOKEN`과 "
            "`TELEGRAM_CHAT_ID`를 등록해 주세요."
        )

    st.page_link(
        "pages/1_부모_학습기록.py",
        label="부모용 날짜별 학습 기록 보기",
        icon="📊",
        width="stretch",
    )


initialize_state()

if st.session_state.screen == "intro":
    render_intro()
elif st.session_state.screen == "quiz":
    render_quiz()
else:
    render_result()
