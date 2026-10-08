import assert from "node:assert/strict";
import test from "node:test";

import {
  LEVELS,
  adjustLevelForFeeling,
  chooseNextLevel,
  chooseStartLevel,
  domainIsMastered,
  isCorrectAnswer,
  makeProblem,
  parseAnswer,
  summarizeSession,
  unlockedDomains,
} from "../public/learning.js";

function seeded(seed) {
  let value = seed >>> 0;
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0;
    return value / 2 ** 32;
  };
}

test("17단계가 모두 정답으로 판정되는 문제를 만든다", () => {
  for (const level of Object.keys(LEVELS).map(Number)) {
    const rng = seeded(100 + level);
    for (let count = 0; count < 100; count += 1) {
      const problem = makeProblem(level, rng);
      assert.equal(isCorrectAnswer(problem, problem.answerText), true, `${level}단계: ${problem.expression}`);
    }
  }
});

test("2단계는 일의 자리 받아올림이 없다", () => {
  const rng = seeded(7);
  for (let count = 0; count < 100; count += 1) {
    const [left, right] = makeProblem(2, rng).signature.split("+").map(Number);
    assert.ok((left % 10) + (right % 10) < 10);
  }
});

test("3단계는 일의 자리 받아올림이 있다", () => {
  const rng = seeded(8);
  for (let count = 0; count < 100; count += 1) {
    const [left, right] = makeProblem(3, rng).signature.split("+").map(Number);
    assert.ok((left % 10) + (right % 10) >= 10);
  }
});

test("동치인 소수와 분수를 정확히 파싱한다", () => {
  assert.deepEqual(parseAnswer("1.5"), { numerator: 3, denominator: 2 });
  assert.deepEqual(parseAnswer("6/4"), { numerator: 3, denominator: 2 });
  assert.equal(parseAnswer("1/0"), null);
});

test("최근 네 문제를 맞히면 같은 영역 안에서 한 단계 오른다", () => {
  const records = Array.from({ length: 4 }, () => ({ level: 2, correct: true }));
  assert.equal(chooseNextLevel(2, records), 3);
  assert.equal(chooseNextLevel(4, records.map((record) => ({ ...record, level: 4 }))), 4);
});

test("최근 세 문제 중 두 문제를 틀리면 한 단계 내려간다", () => {
  assert.equal(chooseNextLevel(3, [
    { level: 3, correct: false }, { level: 3, correct: true }, { level: 3, correct: false },
  ]), 2);
});

test("체감 난이도 조절은 영역을 벗어나지 않는다", () => {
  assert.equal(adjustLevelForFeeling(2, "easy", 80), 3);
  assert.equal(adjustLevelForFeeling(1, "hard", 90), 1);
  assert.equal(adjustLevelForFeeling(4, "easy", 90), 4);
});

test("학습 요약의 정답 수와 다음 단계를 계산한다", () => {
  const records = [true, true, false, true, true].map((correct) => ({ level: 2, correct }));
  const summary = summarizeSession(records, 600);
  assert.equal(summary.attempted, 5);
  assert.equal(summary.correct, 4);
  assert.equal(summary.accuracy, 80);
  assert.equal(summary.recommendedLevel, 3);
});

test("영역 숙달 뒤 다음 영역을 연다", () => {
  const sessions = [
    { domain: "addition", accuracy: 85, feeling: "normal", attempted: 10, recommendedLevel: 2 },
    { domain: "addition", accuracy: 85, feeling: "normal", attempted: 10, recommendedLevel: 3 },
  ];
  assert.equal(domainIsMastered("addition", sessions), true);
  assert.deepEqual(unlockedDomains(sessions, null), ["addition", "subtraction"]);
  assert.equal(chooseStartLevel(sessions, null), 5);
});

test("부모 지정 단계가 자동 선택보다 우선한다", () => {
  assert.equal(chooseStartLevel([], {
    mode: "focus", enabledDomains: ["addition", "multiplication"], focusDomain: "multiplication", forcedLevel: 9,
  }), 9);
});
