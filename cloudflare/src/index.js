import {
  DEFAULT_SETTINGS,
  DOMAIN_LABELS,
  LEVELS,
  adjustLevelForFeeling,
  chooseStartLevel,
  normalizedSettings,
  summarizeSession,
} from "../public/learning.js";

const JSON_HEADERS = { "content-type": "application/json; charset=utf-8" };
const SECURITY_HEADERS = {
  "content-security-policy": "default-src 'self'; connect-src 'self' https://api.telegram.org; img-src 'self' data:; style-src 'self'; script-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
  "referrer-policy": "no-referrer",
  "x-content-type-options": "nosniff",
  "x-frame-options": "DENY",
  "permissions-policy": "camera=(), microphone=(), geolocation=()",
};
const FEELING_LABELS = { easy: "쉬웠어요", normal: "딱 좋았어요", hard: "어려웠어요", "": "선택하지 않음" };
const PARENT_COOKIE = "parent_session";
const PARENT_SESSION_SECONDS = 8 * 60 * 60;

function responseJson(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), { status, headers: { ...JSON_HEADERS, ...SECURITY_HEADERS, ...headers } });
}

function errorJson(message, status = 400) {
  return responseJson({ error: message }, status);
}

function withSecurity(response) {
  const secured = new Response(response.body, response);
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) secured.headers.set(name, value);
  return secured;
}

async function readJson(request) {
  const length = Number(request.headers.get("content-length") || 0);
  if (length > 200_000) throw new Error("요청 데이터가 너무 큽니다.");
  try {
    const text = await request.text();
    if (text.length > 200_000) throw new Error("요청 데이터가 너무 큽니다.");
    return JSON.parse(text);
  } catch (error) {
    if (error?.message === "요청 데이터가 너무 큽니다.") throw error;
    throw new Error("요청 형식이 올바르지 않습니다.");
  }
}

function base64url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/g, "");
}

function textBase64url(text) {
  return base64url(new TextEncoder().encode(text));
}

async function sha256(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(String(value)));
  return base64url(new Uint8Array(digest));
}

async function hmac(value, secret) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return base64url(new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(value))));
}

async function constantTimeEquals(left, right) {
  const [leftHash, rightHash] = await Promise.all([sha256(left), sha256(right)]);
  let difference = leftHash.length ^ rightHash.length;
  const length = Math.max(leftHash.length, rightHash.length);
  for (let index = 0; index < length; index += 1) {
    difference |= (leftHash.charCodeAt(index) || 0) ^ (rightHash.charCodeAt(index) || 0);
  }
  return difference === 0;
}

export async function createParentSession(secret, now = Date.now()) {
  const payload = textBase64url(JSON.stringify({ exp: Math.floor(now / 1000) + PARENT_SESSION_SECONDS }));
  return `${payload}.${await hmac(payload, secret)}`;
}

export async function verifyParentSession(token, secret, now = Date.now()) {
  if (!token || !secret) return false;
  const [payload, signature, extra] = token.split(".");
  if (!payload || !signature || extra) return false;
  const expected = await hmac(payload, secret);
  if (!(await constantTimeEquals(signature, expected))) return false;
  try {
    const normalized = payload.replaceAll("-", "+").replaceAll("_", "/");
    const decoded = JSON.parse(atob(normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=")));
    return Number(decoded.exp) > Math.floor(now / 1000);
  } catch {
    return false;
  }
}

function cookieValue(request, name) {
  const cookies = request.headers.get("cookie") || "";
  for (const item of cookies.split(";")) {
    const [key, ...parts] = item.trim().split("=");
    if (key === name) return parts.join("=");
  }
  return "";
}

async function requireParent(request, env) {
  return verifyParentSession(cookieValue(request, PARENT_COOKIE), env.SESSION_SECRET || "");
}

function kstDate(now = new Date()) {
  return new Date(now.getTime() + 9 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

function parseSessionRow(row) {
  return {
    id: row.id,
    completedAt: row.completed_at,
    localDate: row.local_date,
    domain: row.domain,
    startLevel: Number(row.start_level),
    finalLevel: Number(row.final_level),
    recommendedLevel: Number(row.recommended_level),
    attempted: Number(row.attempted),
    correct: Number(row.correct),
    accuracy: Number(row.accuracy),
    elapsedSeconds: Number(row.elapsed_seconds),
    feeling: row.feeling || "",
    telegramSentAt: row.telegram_sent_at || null,
    records: JSON.parse(row.records_json || "[]"),
  };
}

async function listSessions(env, limit = 500) {
  const result = await env.DB.prepare(
    "SELECT * FROM (SELECT * FROM sessions ORDER BY completed_at DESC LIMIT ?1) ORDER BY completed_at ASC",
  ).bind(limit).all();
  return (result.results || []).map(parseSessionRow);
}

async function loadSettings(env) {
  const row = await env.DB.prepare("SELECT settings_json FROM settings WHERE id = 'family'").first();
  if (!row) return normalizedSettings(DEFAULT_SETTINGS);
  try {
    return normalizedSettings(JSON.parse(row.settings_json));
  } catch {
    return normalizedSettings(DEFAULT_SETTINGS);
  }
}

function sanitizedRecords(records) {
  if (!Array.isArray(records) || records.length > 500) throw new Error("문제 기록이 올바르지 않습니다.");
  return records.map((record) => {
    const level = Number(record.level);
    if (!LEVELS[level]) throw new Error("지원하지 않는 학습 단계입니다.");
    return {
      level,
      expression: String(record.expression || "").slice(0, 80),
      answer: String(record.answer || "").slice(0, 30),
      userAnswer: String(record.userAnswer || record.user_answer || "").slice(0, 30),
      correct: Boolean(record.correct),
      seconds: Math.max(0, Math.min(600, Number(record.seconds || 0))),
    };
  });
}

function publicSession(session) {
  const { editTokenHash: _hidden, ...visible } = session;
  return visible;
}

async function saveSession(request, env) {
  const body = await readJson(request);
  const records = sanitizedRecords(body.records);
  const elapsedSeconds = Math.max(0, Math.min(600, Math.trunc(Number(body.elapsedSeconds || 0))));
  const summary = summarizeSession(records, elapsedSeconds);
  const startLevel = Number(body.startLevel || 2);
  const finalLevel = records.length ? Number(records.at(-1).level) : startLevel;
  if (!LEVELS[startLevel] || !LEVELS[finalLevel]) throw new Error("학습 단계가 올바르지 않습니다.");
  const id = crypto.randomUUID();
  const tokenBytes = crypto.getRandomValues(new Uint8Array(24));
  const editToken = base64url(tokenBytes);
  const editTokenHash = await sha256(editToken);
  const completedAt = new Date().toISOString();
  const localDate = kstDate();
  const record = {
    id,
    completedAt,
    localDate,
    domain: summary.domain,
    startLevel,
    finalLevel,
    recommendedLevel: summary.recommendedLevel,
    attempted: summary.attempted,
    correct: summary.correct,
    accuracy: Math.round(summary.accuracy * 10) / 10,
    elapsedSeconds,
    feeling: "",
    telegramSentAt: null,
    records,
    editTokenHash,
  };
  await env.DB.prepare(
    `INSERT INTO sessions (
      id, edit_token_hash, completed_at, local_date, domain, start_level, final_level,
      recommended_level, attempted, correct, accuracy, elapsed_seconds, feeling,
      telegram_sent_at, records_json
    ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, '', NULL, ?13)`,
  ).bind(
    id, editTokenHash, completedAt, localDate, summary.domain, startLevel, finalLevel,
    summary.recommendedLevel, summary.attempted, summary.correct, record.accuracy,
    elapsedSeconds, JSON.stringify(records),
  ).run();
  return responseJson({ session: publicSession(record), editToken }, 201);
}

async function editableSession(request, env, id) {
  const row = await env.DB.prepare("SELECT * FROM sessions WHERE id = ?1").bind(id).first();
  if (!row) return { error: errorJson("학습 기록을 찾지 못했습니다.", 404) };
  const token = request.headers.get("x-session-token") || "";
  if (!(await constantTimeEquals(await sha256(token), row.edit_token_hash))) {
    return { error: errorJson("학습 기록을 수정할 권한이 없습니다.", 403) };
  }
  return { row, session: parseSessionRow(row) };
}

async function updateFeeling(request, env, id) {
  const editable = await editableSession(request, env, id);
  if (editable.error) return editable.error;
  const body = await readJson(request);
  if (!Object.hasOwn(FEELING_LABELS, body.feeling) || !body.feeling) return errorJson("오늘 느낌을 선택해 주세요.");
  const recommendedLevel = adjustLevelForFeeling(
    editable.session.finalLevel,
    body.feeling,
    editable.session.accuracy,
  );
  await env.DB.prepare("UPDATE sessions SET feeling = ?1, recommended_level = ?2 WHERE id = ?3")
    .bind(body.feeling, recommendedLevel, id).run();
  return responseJson({ feeling: body.feeling, recommendedLevel });
}

export function buildResultMessage(session) {
  const minutes = Math.floor(Number(session.elapsedSeconds || 0) / 60);
  const seconds = Number(session.elapsedSeconds || 0) % 60;
  const finalLevel = Number(session.finalLevel || session.recommendedLevel || 2);
  const recommendedLevel = Number(session.recommendedLevel || finalLevel);
  return [
    "🧮 오늘의 연산 10분 학습 결과",
    `📅 날짜: ${session.localDate || "-"}`,
    `📚 영역: ${DOMAIN_LABELS[session.domain] || "-"}`,
    `✏️ 단계: ${LEVELS[finalLevel]?.name || "-"}`,
    `✅ 정답: ${session.correct || 0}/${session.attempted || 0}개`,
    `🎯 정확도: ${Math.round(Number(session.accuracy || 0))}%`,
    `⏱ 학습 시간: ${minutes}분 ${seconds}초`,
    `🙂 오늘 느낌: ${FEELING_LABELS[session.feeling || ""] || "선택하지 않음"}`,
    `➡️ 다음 권장: ${LEVELS[recommendedLevel]?.name || "-"}`,
  ].join("\n");
}

async function sendTelegram(request, env, id) {
  const editable = await editableSession(request, env, id);
  if (editable.error) return editable.error;
  if (editable.session.telegramSentAt) return errorJson("오늘 결과를 이미 보냈습니다.", 409);
  if (!env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) return errorJson("Telegram 설정이 필요합니다.", 503);
  const endpoint = `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`;
  const telegramResponse = await fetch(endpoint, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded;charset=UTF-8" },
    body: new URLSearchParams({ chat_id: env.TELEGRAM_CHAT_ID, text: buildResultMessage(editable.session) }),
  });
  const result = await telegramResponse.json().catch(() => ({}));
  if (!telegramResponse.ok || !result.ok) return errorJson("Telegram 메시지 전송에 실패했습니다.", 502);
  const sentAt = new Date().toISOString();
  await env.DB.prepare("UPDATE sessions SET telegram_sent_at = ?1 WHERE id = ?2").bind(sentAt, id).run();
  return responseJson({ telegramSentAt: sentAt });
}

async function parentLogin(request, env) {
  if (!env.PARENT_PIN || !env.SESSION_SECRET) return errorJson("부모 인증 설정이 필요합니다.", 503);
  const body = await readJson(request);
  const valid = await constantTimeEquals(String(body.pin || "").slice(0, 40), env.PARENT_PIN);
  if (!valid) return errorJson("PIN이 맞지 않습니다.", 401);
  const token = await createParentSession(env.SESSION_SECRET);
  return responseJson(
    { authenticated: true },
    200,
    { "set-cookie": `${PARENT_COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${PARENT_SESSION_SECONDS}` },
  );
}

async function parentState(request, env) {
  if (!(await requireParent(request, env))) return errorJson("부모 인증이 필요합니다.", 401);
  const [sessions, settings] = await Promise.all([listSessions(env), loadSettings(env)]);
  return responseJson({ sessions: sessions.map(publicSession), settings });
}

async function saveParentSettings(request, env) {
  if (!(await requireParent(request, env))) return errorJson("부모 인증이 필요합니다.", 401);
  const settings = normalizedSettings(await readJson(request));
  await env.DB.prepare(
    `INSERT INTO settings (id, settings_json, updated_at) VALUES ('family', ?1, ?2)
     ON CONFLICT(id) DO UPDATE SET settings_json = excluded.settings_json, updated_at = excluded.updated_at`,
  ).bind(JSON.stringify(settings), new Date().toISOString()).run();
  return responseJson({ settings });
}

async function apiRouter(request, env, url) {
  if (request.method === "GET" && url.pathname === "/api/bootstrap") {
    const [sessions, settings] = await Promise.all([listSessions(env), loadSettings(env)]);
    const nextLevel = chooseStartLevel(sessions, settings);
    return responseJson({
      nextLevel,
      nextStudyLabel: `오늘은 ${DOMAIN_LABELS[LEVELS[nextLevel].domain]} · ${LEVELS[nextLevel].name}부터 시작해요.`,
      telegramConfigured: Boolean(env.TELEGRAM_BOT_TOKEN && env.TELEGRAM_CHAT_ID),
    });
  }
  if (request.method === "POST" && url.pathname === "/api/sessions") return saveSession(request, env);
  const feelingMatch = url.pathname.match(/^\/api\/sessions\/([0-9a-f-]+)\/feeling$/i);
  if (request.method === "PATCH" && feelingMatch) return updateFeeling(request, env, feelingMatch[1]);
  const telegramMatch = url.pathname.match(/^\/api\/sessions\/([0-9a-f-]+)\/telegram$/i);
  if (request.method === "POST" && telegramMatch) return sendTelegram(request, env, telegramMatch[1]);
  if (request.method === "POST" && url.pathname === "/api/parent/login") return parentLogin(request, env);
  if (request.method === "POST" && url.pathname === "/api/parent/logout") {
    return responseJson({ authenticated: false }, 200, { "set-cookie": `${PARENT_COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0` });
  }
  if (request.method === "GET" && url.pathname === "/api/parent/state") return parentState(request, env);
  if (request.method === "PUT" && url.pathname === "/api/parent/settings") return saveParentSettings(request, env);
  return errorJson("요청한 API를 찾지 못했습니다.", 404);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    try {
      if (url.pathname.startsWith("/api/")) return await apiRouter(request, env, url);
      if (request.method !== "GET" && request.method !== "HEAD") return errorJson("허용되지 않은 요청입니다.", 405);
      return withSecurity(await env.ASSETS.fetch(request));
    } catch (error) {
      console.error("request_failed", { path: url.pathname, message: error instanceof Error ? error.message : String(error) });
      return errorJson(error instanceof Error ? error.message : "처리 중 오류가 발생했습니다.", 500);
    }
  },
};
