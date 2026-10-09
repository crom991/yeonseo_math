import {
  DOMAIN_LABELS,
  LEVELS,
  chooseNextLevel,
  isCorrectAnswer,
  makeProblem,
  parseAnswer,
  summarizeSession,
} from "./learning.js";
import { PROFILES, normalizeProfileId } from "./profiles.js";

const SESSION_SECONDS = 10 * 60;
const app = document.querySelector("#app");
const encouragements = [
  "정답이에요! 잘했어요 🌟",
  "좋아요, 정확해요! 👏",
  "멋져요! 다음 문제도 천천히 해봐요 😊",
];

const state = {
  profileId: null,
  bootstrap: null,
  screen: "loading",
  records: [],
  currentLevel: 2,
  startLevel: 2,
  questionNumber: 1,
  currentProblem: null,
  startedAt: null,
  problemStartedAt: null,
  finishedAt: null,
  feedback: null,
  recentSignatures: [],
  result: null,
  editToken: "",
  timer: null,
  saving: false,
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "content-type": "application/json", ...(options.headers || {}) },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "서버 요청에 실패했습니다.");
  return data;
}

function hero(subtitle) {
  const profile = PROFILES[state.profileId];
  return `<header class="hero"><h1>오늘의 연산 10분</h1>${profile ? `<div class="profile-badge">${profile.emoji} ${profile.name}</div>` : ""}<p>${escapeHtml(subtitle)}</p></header>`;
}

function newProblem() {
  const current = makeProblem(state.currentLevel, Math.random, state.recentSignatures.slice(-12));
  state.recentSignatures.push(current.signature);
  state.currentProblem = current;
  state.problemStartedAt = Date.now();
}

async function loadBootstrap() {
  if (!state.profileId) throw new Error("학습자를 먼저 선택해 주세요.");
  state.bootstrap = await api(`/api/bootstrap?profile=${encodeURIComponent(state.profileId)}`);
}

function renderProfileSelection(message = "") {
  state.screen = "profile";
  state.profileId = null;
  state.bootstrap = null;
  clearInterval(state.timer);
  const buttons = Object.values(PROFILES).map((profile) => `
    <button class="profile-card" data-profile="${profile.id}" type="button">
      <span class="profile-emoji" aria-hidden="true">${profile.emoji}</span>
      <strong>${profile.name}</strong>
      <span>내 학습 시작하기</span>
    </button>`).join("");
  app.innerHTML = `
    ${hero("오늘 공부할 친구를 골라 주세요.")}
    ${message ? `<div class="feedback error">${escapeHtml(message)}</div>` : ""}
    <section class="summary-card profile-selection">
      <h2>누가 공부하나요?</h2>
      <p class="caption">로그인 없이 이름만 고르면 기록과 난이도가 각자 따로 저장돼요.</p>
      <div class="profile-grid">${buttons}</div>
    </section>
    <a class="button secondary" href="/parent">👨‍👩‍👧‍👧 부모용 학습 기록과 설정</a>`;
  document.querySelectorAll("[data-profile]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.profileId = normalizeProfileId(button.dataset.profile);
      app.innerHTML = `<div class="loading-card">${PROFILES[state.profileId].name}의 학습 화면을 준비하고 있어요…</div>`;
      try { await loadBootstrap(); renderIntro(); } catch (error) { renderProfileSelection(error.message); }
    });
  });
}

function renderIntro(message = "") {
  state.screen = "intro";
  clearInterval(state.timer);
  app.innerHTML = `
    ${hero("한 문제씩 차근차근, 정확하게 풀어 봐요.")}
    ${message ? `<div class="feedback error">${escapeHtml(message)}</div>` : ""}
    <section class="summary-card">
      <div class="metric-big">⏱️ 10분</div>
      <p>${escapeHtml(state.bootstrap.nextStudyLabel)}</p>
      <p>최근 결과와 오늘 느낌을 보고 다음 영역과 단계를 자동으로 정해요.</p>
      <p>빨리 푸는 것보다 <strong>정확하게 푸는 것</strong>이 더 중요해요.</p>
    </section>
    <div class="stack">
      <button id="start-button" class="button primary" type="button">연습 시작</button>
      <button id="switch-profile" class="button secondary" type="button">다른 아이로 바꾸기</button>
      <a class="button secondary" href="/parent">👨‍👩‍👧‍👧 부모용 학습 기록과 설정</a>
    </div>`;
  document.querySelector("#start-button").addEventListener("click", startSession);
  document.querySelector("#switch-profile").addEventListener("click", () => renderProfileSelection());
}

function startSession() {
  const now = Date.now();
  state.screen = "quiz";
  state.records = [];
  state.currentLevel = Number(state.bootstrap.nextLevel || 2);
  state.startLevel = state.currentLevel;
  state.questionNumber = 1;
  state.startedAt = now;
  state.finishedAt = null;
  state.feedback = null;
  state.recentSignatures = [];
  state.result = null;
  state.editToken = "";
  newProblem();
  renderQuiz();
  clearInterval(state.timer);
  state.timer = setInterval(updateTimer, 1000);
}

function remainingSeconds() {
  if (!state.startedAt) return SESSION_SECONDS;
  return Math.max(0, SESSION_SECONDS - Math.floor((Date.now() - state.startedAt) / 1000));
}

function updateTimer() {
  if (state.screen !== "quiz") return;
  const remaining = remainingSeconds();
  const minutes = Math.floor(remaining / 60);
  const seconds = remaining % 60;
  const percent = Math.floor((1 - remaining / SESSION_SECONDS) * 100);
  const text = document.querySelector("#timer-text");
  const progress = document.querySelector("#timer-progress");
  if (text) text.textContent = `오늘 연습 ${percent}% · 남은 시간 ${minutes}:${String(seconds).padStart(2, "0")}`;
  if (progress) progress.value = percent;
  if (remaining <= 0) finishSession();
}

function renderQuiz() {
  const current = state.currentProblem;
  const level = LEVELS[current.level];
  const placeholder = current.answerKind === "fraction" ? "예: 3/4" : current.answerKind === "decimal" ? "예: 4.2" : "답을 적어 보세요";
  app.innerHTML = `
    ${hero("한 문제씩 차근차근, 정확하게 풀어 봐요.")}
    <div class="timer-row"><span id="timer-text"></span></div>
    <progress id="timer-progress" class="progress" max="100" value="0" aria-label="학습 진행률"></progress>
    ${state.feedback ? `<div class="feedback ${state.feedback.kind}">${escapeHtml(state.feedback.message)}</div>` : ""}
    <section class="question-card">
      <div class="level-label">${state.questionNumber}번째 문제 · ${escapeHtml(DOMAIN_LABELS[level.domain])} · ${escapeHtml(level.name)}</div>
      <div class="problem">${escapeHtml(current.expression)}</div>
    </section>
    <form id="answer-form" class="answer-form">
      <label class="field" style="margin:0"><span class="caption" hidden>답</span>
        <input id="answer-input" name="answer" inputmode="${current.answerKind === "integer" ? "numeric" : "decimal"}" autocomplete="off" placeholder="${placeholder}" aria-label="답" required>
      </label>
      <button class="button primary" type="submit">정답 확인</button>
    </form>
    <details class="finish-box">
      <summary>오늘은 여기까지 할래요</summary>
      <div class="stack">
        <span class="caption">10분 전에도 그만할 수 있어요. 푼 문제까지 결과에 담겨요.</span>
        <button id="finish-button" class="button secondary" type="button">연습 마치기</button>
      </div>
    </details>`;
  updateTimer();
  const input = document.querySelector("#answer-input");
  document.querySelector("#answer-form").addEventListener("submit", submitAnswer);
  document.querySelector("#finish-button").addEventListener("click", finishSession);
  input.focus({ preventScroll: true });
}

function submitAnswer(event) {
  event.preventDefault();
  const input = document.querySelector("#answer-input");
  const value = input.value.trim();
  if (!parseAnswer(value)) {
    state.feedback = { kind: "try", message: "답을 숫자로 적어 주세요. 분수는 3/4처럼 적어요." };
    renderQuiz();
    return;
  }
  const correct = isCorrectAnswer(state.currentProblem, value);
  state.records.push({
    level: state.currentProblem.level,
    expression: state.currentProblem.expression,
    answer: state.currentProblem.answerText,
    userAnswer: value,
    correct,
    seconds: Math.max(.1, (Date.now() - state.problemStartedAt) / 1000),
  });
  state.feedback = correct
    ? { kind: "good", message: encouragements[Math.floor(Math.random() * encouragements.length)] }
    : { kind: "try", message: `괜찮아요. ${state.currentProblem.signature}의 답은 ${state.currentProblem.answerText}예요. 다음 문제는 천천히 해봐요.` };
  state.currentLevel = chooseNextLevel(state.currentLevel, state.records);
  state.questionNumber += 1;
  newProblem();
  renderQuiz();
}

function elapsedSeconds() {
  if (!state.startedAt) return 0;
  return Math.min(SESSION_SECONDS, Math.floor(((state.finishedAt || Date.now()) - state.startedAt) / 1000));
}

async function finishSession() {
  if (state.screen !== "quiz" || state.saving) return;
  state.saving = true;
  state.finishedAt = Date.now();
  state.screen = "result";
  clearInterval(state.timer);
  const summary = summarizeSession(state.records, elapsedSeconds());
  renderSavingResult(summary);
  try {
    const data = await api("/api/sessions", {
      method: "POST",
      body: JSON.stringify({ profileId: state.profileId, startLevel: state.startLevel, elapsedSeconds: summary.elapsedSeconds, records: state.records }),
    });
    state.result = data.session;
    state.editToken = data.editToken;
    renderResult(summary);
  } catch (error) {
    state.result = null;
    renderResult(summary, error.message);
  } finally {
    state.saving = false;
  }
}

function renderSavingResult(summary) {
  app.innerHTML = `${hero("오늘 연습을 마쳤어요. 끝까지 해낸 것이 가장 멋져요!")}<div class="loading-card" style="margin-top:1rem">결과를 안전하게 저장하고 있어요…</div>`;
}

function resultMetrics(summary) {
  return `<div class="result-metrics">
    <div class="result-metric"><div class="result-metric-label">푼 문제</div><div class="result-metric-value">${summary.attempted}개</div></div>
    <div class="result-metric"><div class="result-metric-label">맞힌 문제</div><div class="result-metric-value">${summary.correct}개</div></div>
    <div class="result-metric"><div class="result-metric-label">정확도</div><div class="result-metric-value">${Math.round(summary.accuracy)}%</div></div>
  </div>`;
}

function renderResult(summary, storageError = "", statusMessage = "") {
  const saved = state.result;
  const recommendation = Number(saved?.recommendedLevel || summary.recommendedLevel);
  const minutes = Math.floor(summary.elapsedSeconds / 60);
  const seconds = summary.elapsedSeconds % 60;
  const wrong = state.records.filter((record) => !record.correct).slice(-5);
  const feeling = saved?.feeling || "";
  const alreadySent = Boolean(saved?.telegramSentAt);
  app.innerHTML = `
    ${hero("오늘 연습을 마쳤어요. 끝까지 해낸 것이 가장 멋져요!")}
    ${resultMetrics(summary)}
    <section class="summary-card">
      <div class="metric-big">걸린 시간 ${minutes}분 ${seconds}초</div>
      <p>${escapeHtml(summary.message)}</p>
      <p><strong>오늘 영역:</strong> ${escapeHtml(DOMAIN_LABELS[summary.domain])}</p>
      <p><strong>다음 권장 단계:</strong> ${escapeHtml(LEVELS[recommendation].name)}</p>
    </section>
    ${storageError ? `<div class="feedback error">${escapeHtml(storageError)} 기록 저장을 다시 확인해 주세요.</div>` : ""}
    ${statusMessage ? `<div class="feedback success">${escapeHtml(statusMessage)}</div>` : ""}
    <h2 class="section-title">오늘 문제는 어땠나요?</h2>
    <div class="feeling-grid" role="group" aria-label="오늘 체감 난이도">
      <button class="feeling-button ${feeling === "easy" ? "selected" : ""}" data-feeling="easy" type="button">😊 쉬웠어요</button>
      <button class="feeling-button ${feeling === "normal" ? "selected" : ""}" data-feeling="normal" type="button">🙂 딱 좋았어요</button>
      <button class="feeling-button ${feeling === "hard" ? "selected" : ""}" data-feeling="hard" type="button">😥 어려웠어요</button>
    </div>
    <p class="caption">${feeling ? "오늘 느낌이 저장되었어요." : "하나를 누르면 오늘 느낌이 자동으로 저장돼요."}</p>
    <h2 class="section-title">${wrong.length ? "틀린 문제 다시 보기" : "오늘 문제"}</h2>
    ${wrong.length ? `<ul class="wrong-list">${wrong.map((record) => `<li>${escapeHtml(record.expression.replace(" = ?", ""))} = ${escapeHtml(record.answer)} <span class="caption">(적은 답: ${escapeHtml(record.userAnswer)})</span></li>`).join("")}</ul>` : `<div class="feedback good">오늘 푼 문제를 모두 맞혔어요! 🌟</div>`}
    <div class="spacer"></div>
    <div class="stack">
      <button id="restart-button" class="button primary" type="button">새로 10분 연습</button>
      <button id="switch-profile" class="button secondary" type="button">다른 아이로 바꾸기</button>
      <button id="telegram-button" class="button secondary" type="button" ${!saved || !state.bootstrap.telegramConfigured || alreadySent ? "disabled" : ""}>📩 아빠에게 학습 결과 보내기</button>
      <p class="caption">${alreadySent ? "오늘 결과를 이미 보냈어요." : state.bootstrap.telegramConfigured ? "" : "Telegram 전송 설정이 필요합니다."}</p>
      <a class="button secondary" href="/parent">📊 부모용 날짜별 학습 기록 보기</a>
    </div>`;

  document.querySelectorAll("[data-feeling]").forEach((button) => {
    button.disabled = !saved;
    button.addEventListener("click", () => saveFeeling(button.dataset.feeling, summary));
  });
  document.querySelector("#restart-button").addEventListener("click", async () => {
    try { await loadBootstrap(); startSession(); } catch (error) { renderIntro(error.message); }
  });
  document.querySelector("#switch-profile").addEventListener("click", () => renderProfileSelection());
  document.querySelector("#telegram-button").addEventListener("click", () => sendTelegram(summary));
}

async function saveFeeling(feeling, summary) {
  if (!state.result || !state.editToken || state.result.feeling === feeling) return;
  try {
    const data = await api(`/api/sessions/${state.result.id}/feeling`, {
      method: "PATCH",
      headers: { "x-session-token": state.editToken },
      body: JSON.stringify({ feeling }),
    });
    state.result.feeling = data.feeling;
    state.result.recommendedLevel = data.recommendedLevel;
    renderResult(summary, "", "오늘 느낌이 저장되었어요.");
  } catch (error) {
    renderResult(summary, error.message);
  }
}

async function sendTelegram(summary) {
  const button = document.querySelector("#telegram-button");
  button.disabled = true;
  try {
    const data = await api(`/api/sessions/${state.result.id}/telegram`, {
      method: "POST",
      headers: { "x-session-token": state.editToken },
      body: "{}",
    });
    state.result.telegramSentAt = data.telegramSentAt;
    renderResult(summary, "", "아빠에게 오늘 학습 결과를 보냈어요! 📩");
  } catch (error) {
    button.disabled = false;
    renderResult(summary, error.message);
  }
}

renderProfileSelection();
