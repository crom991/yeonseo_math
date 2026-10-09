import { DOMAIN_LABELS, DOMAIN_ORDER, LEVELS, domainIsMastered, levelsForDomain, normalizedSettings, unlockedDomains } from "./learning.js";
import { profileName } from "./profiles.js";

const root = document.querySelector("#parent-app");

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "content-type": "application/json", ...(options.headers || {}) },
  });
  const data = await response.json().catch(() => ({}));
  return { ok: response.ok, status: response.status, data };
}

function renderLogin(message = "") {
  root.innerHTML = `
    <section class="panel login-card">
      <h1>🔒 부모 확인</h1>
      <p class="caption">부모 PIN에 연결된 아이의 학습 기록과 설정만 보여 드려요.</p>
      ${message ? `<div class="feedback error">${escapeHtml(message)}</div>` : ""}
      <form id="login-form" class="stack">
        <label class="field"><span>부모 PIN</span><input id="pin" type="password" inputmode="numeric" maxlength="40" autocomplete="current-password" required></label>
        <button class="button primary" type="submit">확인</button>
        <a class="button secondary" href="/">✏️ 학습 화면으로 돌아가기</a>
      </form>
    </section>`;
  document.querySelector("#login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const pin = document.querySelector("#pin").value;
    const result = await request("/api/parent/login", { method: "POST", body: JSON.stringify({ pin }) });
    if (!result.ok) return renderLogin(result.data.error || "로그인하지 못했습니다.");
    await loadState();
  });
  document.querySelector("#pin").focus();
}

function metricsHtml(sessions) {
  const totalAttempted = sessions.reduce((sum, session) => sum + Number(session.attempted || 0), 0);
  const totalCorrect = sessions.reduce((sum, session) => sum + Number(session.correct || 0), 0);
  const accuracy = totalAttempted ? (totalCorrect / totalAttempted) * 100 : 0;
  const days = new Set(sessions.map((session) => session.localDate)).size;
  return `<div class="dashboard-metrics">
    <div class="dashboard-metric">학습한 날<strong>${days}일</strong></div>
    <div class="dashboard-metric">총 학습<strong>${sessions.length}회</strong></div>
    <div class="dashboard-metric">총 문제<strong>${totalAttempted}개</strong></div>
    <div class="dashboard-metric">전체 정확도<strong>${Math.round(accuracy)}%</strong></div>
  </div>`;
}

function historyHtml(sessions) {
  if (!sessions.length) return `<div class="notice">아직 저장된 학습 기록이 없습니다.</div>`;
  const rows = [...sessions].reverse().map((session) => {
    const minutes = Math.round((Number(session.elapsedSeconds || 0) / 60) * 10) / 10;
    const feeling = { easy: "쉬웠어요", normal: "딱 좋았어요", hard: "어려웠어요", "": "선택하지 않음" }[session.feeling || ""];
    return `<tr>
      <td>${escapeHtml(session.localDate)}</td><td>${escapeHtml(DOMAIN_LABELS[session.domain] || "-")}</td>
      <td>${escapeHtml(LEVELS[Number(session.finalLevel)]?.name || "-")}</td><td>${Number(session.attempted)}</td>
      <td>${Number(session.correct)}</td><td>${Math.round(Number(session.accuracy))}%</td><td>${minutes}</td>
      <td>${escapeHtml(feeling)}</td><td>${session.telegramSentAt ? "완료" : "미전송"}</td>
    </tr>`;
  }).join("");
  return `<div class="table-wrap"><table>
    <thead><tr><th>날짜</th><th>영역</th><th>단계</th><th>문제</th><th>정답</th><th>정확도</th><th>시간(분)</th><th>아이 느낌</th><th>전송</th></tr></thead>
    <tbody>${rows}</tbody></table></div>`;
}

function settingsHtml(sessions, rawSettings) {
  const settings = normalizedSettings(rawSettings);
  const domainChoices = DOMAIN_ORDER.map((domain) => `
    <label><input type="checkbox" name="enabled-domain" value="${domain}" ${settings.enabledDomains.includes(domain) ? "checked" : ""}>${DOMAIN_LABELS[domain]}</label>`).join("");
  const focusOptions = settings.enabledDomains.map((domain) => `<option value="${domain}" ${domain === settings.focusDomain ? "selected" : ""}>${DOMAIN_LABELS[domain]}</option>`).join("");
  const levelOptions = levelsForDomain(settings.focusDomain).map((level) => `<option value="${level}" ${level === settings.forcedLevel ? "selected" : ""}>${level}단계 · ${escapeHtml(LEVELS[level].name)}</option>`).join("");
  const unlocked = unlockedDomains(sessions, settings);
  const statuses = settings.enabledDomains.map((domain) => `<li>${DOMAIN_LABELS[domain]}: ${domainIsMastered(domain, sessions) ? "기준 충족" : "연습 중"}</li>`).join("");
  return `<form id="settings-form">
    <fieldset><legend>운영 방식</legend><div class="choices">
      <label><input type="radio" name="mode" value="automatic" ${settings.mode === "automatic" ? "checked" : ""}>자동 성장</label>
      <label><input type="radio" name="mode" value="focus" ${settings.mode === "focus" ? "checked" : ""}>부모 지정</label>
    </div></fieldset>
    <fieldset><legend>자동 성장에 포함할 영역</legend><div class="choices">${domainChoices}</div></fieldset>
    <div class="form-row">
      <label class="field"><span>부모가 지정할 영역</span><select id="focus-domain">${focusOptions}</select></label>
      <label class="field"><span>시작 단계</span><select id="forced-level">${levelOptions}</select></label>
    </div>
    <button class="button primary" type="submit">설정 저장</button>
    <p class="caption">현재 자동으로 열린 영역: ${unlocked.map((domain) => DOMAIN_LABELS[domain]).join(", ")}</p>
    <ul class="caption">${statuses}</ul>
    <p class="caption">한 영역에서 최근 두 번 모두 5문제 이상 풀고 정확도 80% 이상이며 ‘어려웠어요’가 아니면 다음 영역이 열립니다.</p>
  </form>`;
}

function bindSettings(sessions, settings, profileId) {
  const modeInputs = [...document.querySelectorAll('input[name="mode"]')];
  const focus = document.querySelector("#focus-domain");
  const level = document.querySelector("#forced-level");
  function refreshMode() {
    const disabled = document.querySelector('input[name="mode"]:checked').value !== "focus";
    focus.disabled = disabled;
    level.disabled = disabled;
  }
  function refreshDomains() {
    const enabled = [...document.querySelectorAll('input[name="enabled-domain"]:checked')].map((item) => item.value);
    const safe = enabled.length ? enabled : ["addition"];
    const previous = focus.value;
    focus.innerHTML = safe.map((domain) => `<option value="${domain}">${DOMAIN_LABELS[domain]}</option>`).join("");
    focus.value = safe.includes(previous) ? previous : safe[0];
    refreshLevels();
  }
  function refreshLevels() {
    level.innerHTML = levelsForDomain(focus.value).map((item) => `<option value="${item}">${item}단계 · ${escapeHtml(LEVELS[item].name)}</option>`).join("");
  }
  modeInputs.forEach((input) => input.addEventListener("change", refreshMode));
  document.querySelectorAll('input[name="enabled-domain"]').forEach((input) => input.addEventListener("change", refreshDomains));
  focus.addEventListener("change", refreshLevels);
  refreshMode();
  document.querySelector("#settings-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    let enabledDomains = [...document.querySelectorAll('input[name="enabled-domain"]:checked')].map((item) => item.value);
    if (!enabledDomains.length) enabledDomains = ["addition"];
    const payload = {
      mode: document.querySelector('input[name="mode"]:checked').value,
      enabledDomains,
      focusDomain: focus.value,
      forcedLevel: Number(level.value),
    };
    const result = await request("/api/parent/settings", { method: "PUT", body: JSON.stringify(payload) });
    if (!result.ok) return showStatus(result.data.error || "설정을 저장하지 못했습니다.", true);
    showStatus(`${profileName(profileId)}의 다음 10분 학습부터 새 설정을 적용합니다.`);
  });
}

function showStatus(message, error = false) {
  const target = document.querySelector("#parent-status");
  target.className = `feedback ${error ? "error" : "success"}`;
  target.textContent = message;
  target.hidden = false;
}

function renderDashboard(data) {
  const { profileId, profile, sessions, settings } = data;
  root.innerHTML = `
    <header class="parent-header"><div><h1>${escapeHtml(profile?.emoji || "📊")} ${profileName(profileId)} 부모용 학습 기록</h1><p class="caption">입력한 부모 PIN에 연결된 아이의 기록과 설정만 표시합니다.</p></div><button id="logout" class="button danger" type="button">로그아웃</button></header>
    <div id="parent-status" hidden></div>
    <section class="panel"><h2>${profileName(profileId)}의 날짜별 학습 기록</h2>${metricsHtml(sessions)}${historyHtml(sessions)}</section>
    <section class="panel"><h2>${profileName(profileId)}의 학습 영역과 난이도 설정</h2>${settingsHtml(sessions, settings)}</section>
    <a class="button secondary" href="/">✏️ 학습 화면으로 돌아가기</a>`;
  bindSettings(sessions, settings, profileId);
  document.querySelector("#logout").addEventListener("click", async () => {
    await request("/api/parent/logout", { method: "POST", body: "{}" });
    renderLogin();
  });
}

async function loadState() {
  const result = await request("/api/parent/state");
  if (result.status === 401) return renderLogin();
  if (!result.ok) return renderLogin(result.data.error || "학습 기록을 불러오지 못했습니다.");
  renderDashboard(result.data);
}

loadState();
