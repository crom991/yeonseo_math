from __future__ import annotations

import html
import random
import time

import streamlit as st

from arithmetic import (
    LEVELS,
    Problem,
    SessionSummary,
    choose_next_level,
    make_problem,
    summarize_session,
)


SESSION_SECONDS = 10 * 60


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
    .block-container {
        max-width: 560px;
        padding: 1rem 1rem 3rem;
    }
    .hero {
        padding: 1.2rem 0 .4rem;
        text-align: center;
    }
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
        margin: .8rem 0 1rem;
        padding: 2rem 1rem;
        text-align: center;
    }
    .level-label { color: #64748b; font-size: .9rem; font-weight: 700; }
    .problem {
        color: #172554;
        font-size: clamp(3rem, 16vw, 5rem);
        font-weight: 800;
        letter-spacing: .04em;
        line-height: 1.25;
        margin-top: .5rem;
    }
    .feedback {
        border-radius: 16px;
        margin: .5rem 0 1rem;
        padding: .8rem 1rem;
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
    .metric-big { color: #172554; font-size: 2rem; font-weight: 800; }
    div[data-testid="stNumberInput"] input {
        font-size: 2rem;
        text-align: center;
        min-height: 64px;
        border-radius: 16px;
    }
    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stButton"] button {
        min-height: 54px;
        border-radius: 14px;
        font-size: 1.05rem;
        font-weight: 800;
        width: 100%;
    }
    @media (max-width: 480px) {
        .block-container { padding-top: .35rem; }
        .question-card { padding: 1.5rem .7rem; }
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
        "question_number": 1,
        "current_problem": None,
        "started_at": None,
        "problem_started_at": None,
        "finished_at": None,
        "last_feedback": None,
        "recent_signatures": [],
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
    now = time.time()
    st.session_state.screen = "quiz"
    st.session_state.records = []
    st.session_state.current_level = 2
    st.session_state.question_number = 1
    st.session_state.started_at = now
    st.session_state.finished_at = None
    st.session_state.last_feedback = None
    st.session_state.recent_signatures = []
    st.session_state.current_problem = new_problem(2)


def finish_session() -> None:
    if st.session_state.finished_at is None:
        st.session_state.finished_at = time.time()
    st.session_state.screen = "result"


def remaining_seconds() -> int:
    if st.session_state.started_at is None:
        return SESSION_SECONDS
    return max(0, SESSION_SECONDS - int(time.time() - st.session_state.started_at))


def submit_answer(answer_text: str) -> None:
    cleaned = answer_text.strip().replace(",", "")
    if not cleaned or (cleaned.startswith("-") and not cleaned[1:].isdigit()) or (
        not cleaned.startswith("-") and not cleaned.isdigit()
    ):
        st.session_state.last_feedback = {
            "kind": "input",
            "message": "숫자로 답을 적어 주세요.",
        }
        return

    problem: Problem = st.session_state.current_problem
    answer = int(cleaned)
    is_correct = answer == problem.answer
    elapsed = max(0.1, time.time() - st.session_state.problem_started_at)
    st.session_state.records.append(
        {
            "level": problem.level,
            "expression": problem.expression,
            "answer": problem.answer,
            "user_answer": answer,
            "correct": is_correct,
            "seconds": elapsed,
        }
    )

    if is_correct:
        st.session_state.last_feedback = {
            "kind": "good",
            "message": random.choice(["정답이에요! 잘했어요 🌟", "좋아요, 정확해요! 👏", "멋져요! 다음 문제도 천천히 해봐요 😊"]),
        }
    else:
        safe_expression = html.escape(problem.expression)
        st.session_state.last_feedback = {
            "kind": "try",
            "message": f"괜찮아요. {safe_expression}의 답은 {problem.answer}예요. 다음 문제는 천천히 해봐요.",
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
    left, right = st.columns([2, 1])
    with left:
        st.progress(progress, text=f"오늘 연습 {int(progress * 100)}%")
    with right:
        st.markdown(f"**남은 시간 {minutes}:{seconds:02d}**")
    if remaining <= 0:
        finish_session()
        st.rerun()


def render_intro() -> None:
    render_header("한 문제씩 차근차근, 정확하게 풀어 봐요.")
    st.markdown(
        """
        <div class="summary-card">
          <div class="metric-big">⏱️ 10분</div>
          <p>두 자리 수 덧셈부터 시작해요. 답에 따라 문제가 조금 쉬워지거나 어려워져요.</p>
          <p>빨리 푸는 것보다 <strong>정확하게 푸는 것</strong>이 더 중요해요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("연습 시작", type="primary", use_container_width=True):
        start_session()
        st.rerun()


def render_feedback() -> None:
    feedback = st.session_state.last_feedback
    if not feedback:
        return
    css_class = "good" if feedback["kind"] == "good" else "try"
    st.markdown(
        f'<div class="feedback {css_class}">{feedback["message"]}</div>',
        unsafe_allow_html=True,
    )


def render_quiz() -> None:
    if remaining_seconds() <= 0:
        finish_session()
        st.rerun()

    render_timer()
    render_feedback()
    problem: Problem = st.session_state.current_problem
    st.markdown(
        f"""
        <div class="question-card">
          <div class="level-label">{st.session_state.question_number}번째 문제 · {html.escape(LEVELS[problem.level].name)}</div>
          <div class="problem">{html.escape(problem.expression)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    key = f"answer_{st.session_state.question_number}"
    with st.form(key=f"form_{key}", clear_on_submit=True):
        answer_value = st.number_input(
            "답",
            key=key,
            value=None,
            step=1,
            format="%d",
            placeholder="답을 숫자로 적어 주세요",
        )
        submitted = st.form_submit_button("정답 확인", type="primary")
    if submitted:
        submit_answer("" if answer_value is None else str(answer_value))
        st.rerun()

    with st.expander("오늘은 여기까지 할래요"):
        st.caption("10분 전에도 그만할 수 있어요. 푼 문제까지 결과에 담겨요.")
        if st.button("연습 마치기", use_container_width=True):
            finish_session()
            st.rerun()


def render_result() -> None:
    records = st.session_state.records
    elapsed = 0
    if st.session_state.started_at is not None:
        end = st.session_state.finished_at or time.time()
        elapsed = min(SESSION_SECONDS, int(end - st.session_state.started_at))
    summary: SessionSummary = summarize_session(records, elapsed)

    render_header("오늘 연습을 마쳤어요. 끝까지 해낸 것이 가장 멋져요!")
    cols = st.columns(3)
    cols[0].metric("푼 문제", f"{summary.attempted}개")
    cols[1].metric("맞힌 문제", f"{summary.correct}개")
    cols[2].metric("정확도", f"{summary.accuracy:.0f}%")

    minutes, seconds = divmod(summary.elapsed_seconds, 60)
    st.markdown(
        f"""
        <div class="summary-card">
          <div class="metric-big">걸린 시간 {minutes}분 {seconds}초</div>
          <p>{html.escape(summary.message)}</p>
          <p><strong>다음 시작 단계:</strong> {html.escape(LEVELS[summary.recommended_level].name)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    wrong = [record for record in records if not record["correct"]]
    if wrong:
        with st.expander("틀린 문제 다시 보기"):
            for record in wrong[-5:]:
                st.write(
                    f"{record['expression']} = {record['answer']} "
                    f"(적은 답: {record['user_answer']})"
                )
    else:
        st.success("오늘 푼 문제를 모두 맞혔어요! 🌟")

    if st.button("새로 10분 연습", type="primary", use_container_width=True):
        start_session()
        st.rerun()


initialize_state()

if st.session_state.screen == "intro":
    render_intro()
elif st.session_state.screen == "quiz":
    render_quiz()
else:
    render_result()
