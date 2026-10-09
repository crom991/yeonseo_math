import assert from "node:assert/strict";
import test from "node:test";

import worker, { buildResultMessage, createParentSession, parentProfileFromSession, verifyParentSession } from "../src/index.js";
import { normalizeProfileId, profileName } from "../public/profiles.js";

test("연서와 하은만 학습 프로필로 허용한다", () => {
  assert.equal(normalizeProfileId("yeonseo"), "yeonseo");
  assert.equal(normalizeProfileId("haeun"), "haeun");
  assert.equal(normalizeProfileId("another-child"), null);
  assert.equal(profileName("haeun"), "하은");
});

test("부모 세션은 올바른 비밀키에서만 검증된다", async () => {
  const now = Date.UTC(2026, 9, 8);
  const token = await createParentSession("충분히-긴-시험용-비밀키", now);
  assert.equal(await verifyParentSession(token, "충분히-긴-시험용-비밀키", now + 1000), true);
  assert.equal(await verifyParentSession(token, "다른-비밀키", now + 1000), false);
});

test("만료된 부모 세션은 거부된다", async () => {
  const now = Date.UTC(2026, 9, 8);
  const token = await createParentSession("시험용-비밀키", now);
  assert.equal(await verifyParentSession(token, "시험용-비밀키", now + 9 * 60 * 60 * 1000), false);
});

test("부모 세션은 PIN에 연결된 아이만 식별한다", async () => {
  const now = Date.UTC(2026, 9, 8);
  const token = await createParentSession("시험용-비밀키", now, "haeun");
  assert.equal(await parentProfileFromSession(token, "시험용-비밀키", now + 1000), "haeun");
});

test("하은 부모 PIN은 하은 전용 부모 세션을 만든다", async () => {
  const response = await worker.fetch(new Request("https://example.test/api/parent/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ pin: "2468" }),
  }), {
    PARENT_PIN: "9876",
    HAEUN_PARENT_PIN: "2468",
    SESSION_SECRET: "충분히-긴-시험용-비밀키",
  });
  assert.equal(response.status, 200);
  assert.equal((await response.json()).profileId, "haeun");
  const token = response.headers.get("set-cookie").match(/parent_session=([^;]+)/)[1];
  assert.equal(await parentProfileFromSession(token, "충분히-긴-시험용-비밀키"), "haeun");
});

test("Telegram 결과 메시지에 핵심 학습 정보를 담는다", () => {
  const message = buildResultMessage({
    profileId: "haeun",
    localDate: "2026-10-08", domain: "addition", finalLevel: 2, recommendedLevel: 3,
    correct: 8, attempted: 10, accuracy: 80, elapsedSeconds: 600, feeling: "normal",
  });
  assert.match(message, /2026-10-08/);
  assert.match(message, /학습자: 하은/);
  assert.match(message, /정답: 8\/10개/);
  assert.match(message, /딱 좋았어요/);
  assert.match(message, /10분 0초/);
  assert.match(message, /\n\n🔗 연산 웹페이지: https:\/\/yeonseo-math\.exambreaker-dev\.workers\.dev\/$/);
});
