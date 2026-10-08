import assert from "node:assert/strict";
import test from "node:test";

import { buildResultMessage, createParentSession, verifyParentSession } from "../src/index.js";

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

test("Telegram 결과 메시지에 핵심 학습 정보를 담는다", () => {
  const message = buildResultMessage({
    localDate: "2026-10-08", domain: "addition", finalLevel: 2, recommendedLevel: 3,
    correct: 8, attempted: 10, accuracy: 80, elapsedSeconds: 600, feeling: "normal",
  });
  assert.match(message, /2026-10-08/);
  assert.match(message, /정답: 8\/10개/);
  assert.match(message, /딱 좋았어요/);
  assert.match(message, /10분 0초/);
});
