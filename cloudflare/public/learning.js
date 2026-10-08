export const DOMAIN_LABELS = {
  addition: "덧셈",
  subtraction: "뺄셈",
  multiplication: "곱셈",
  division: "나눗셈",
  decimal: "소수",
  fraction: "분수",
};

export const DOMAIN_ORDER = Object.keys(DOMAIN_LABELS);

export const LEVELS = {
  1: { name: "두 자리 수 + 한 자리 수", description: "받아올림이 없는 덧셈", domain: "addition" },
  2: { name: "두 자리 수 + 두 자리 수", description: "받아올림이 없는 덧셈", domain: "addition" },
  3: { name: "두 자리 수 + 두 자리 수", description: "받아올림이 있는 덧셈", domain: "addition" },
  4: { name: "세 자리 수 + 두 자리 수", description: "받아올림이 있는 덧셈", domain: "addition" },
  5: { name: "두 자리 수 − 두 자리 수", description: "받아내림이 없는 뺄셈", domain: "subtraction" },
  6: { name: "두 자리 수 − 두 자리 수", description: "받아내림이 있는 뺄셈", domain: "subtraction" },
  7: { name: "세 자리 수 − 두 자리 수", description: "받아내림이 있는 뺄셈", domain: "subtraction" },
  8: { name: "한 자리 수 × 한 자리 수", description: "구구단", domain: "multiplication" },
  9: { name: "두 자리 수 × 한 자리 수", description: "곱셈 확장", domain: "multiplication" },
  10: { name: "세 자리 수 × 한 자리 수", description: "곱셈 심화", domain: "multiplication" },
  11: { name: "곱셈표 안의 나눗셈", description: "나머지가 없는 나눗셈", domain: "division" },
  12: { name: "두 자리 수 ÷ 한 자리 수", description: "나머지가 없는 나눗셈", domain: "division" },
  13: { name: "세 자리 수 ÷ 한 자리 수", description: "나머지가 없는 나눗셈", domain: "division" },
  14: { name: "소수 한 자리 덧셈", description: "소수점 위치 맞추기", domain: "decimal" },
  15: { name: "소수 한 자리 뺄셈", description: "0보다 큰 결과", domain: "decimal" },
  16: { name: "분모가 같은 분수", description: "덧셈과 뺄셈", domain: "fraction" },
  17: { name: "분모가 다른 분수", description: "통분이 필요한 덧셈", domain: "fraction" },
};

export const DEFAULT_SETTINGS = {
  mode: "automatic",
  enabledDomains: [...DOMAIN_ORDER],
  focusDomain: "addition",
  forcedLevel: 2,
};

const DOMAIN_INITIAL_LEVEL = {
  addition: 2,
  subtraction: 5,
  multiplication: 8,
  division: 11,
  decimal: 14,
  fraction: 16,
};

function gcd(left, right) {
  let a = Math.abs(left);
  let b = Math.abs(right);
  while (b) [a, b] = [b, a % b];
  return a || 1;
}

export function fraction(numerator, denominator = 1) {
  if (!Number.isInteger(numerator) || !Number.isInteger(denominator) || denominator === 0) {
    throw new Error("올바르지 않은 분수입니다.");
  }
  const sign = denominator < 0 ? -1 : 1;
  const divisor = gcd(numerator, denominator);
  return {
    numerator: (sign * numerator) / divisor,
    denominator: Math.abs(denominator) / divisor,
  };
}

function addFractions(left, right) {
  return fraction(
    left.numerator * right.denominator + right.numerator * left.denominator,
    left.denominator * right.denominator,
  );
}

function randomInt(rng, minimum, maximum) {
  return Math.floor(rng() * (maximum - minimum + 1)) + minimum;
}

function randomChoice(rng, values) {
  return values[randomInt(rng, 0, values.length - 1)];
}

function problem(expression, answer, level, answerKind = "integer") {
  return {
    expression,
    answer,
    level,
    answerKind,
    signature: expression.replace(" = ?", ""),
    answerText:
      answerKind === "decimal"
        ? (answer.numerator / answer.denominator).toFixed(1)
        : answer.denominator === 1
          ? String(answer.numerator)
          : `${answer.numerator}/${answer.denominator}`,
  };
}

function generateCandidate(level, rng) {
  if (level === 1) {
    const tens = randomInt(rng, 1, 8);
    const ones = randomInt(rng, 0, 8);
    const right = randomInt(rng, 1, 9 - ones);
    const left = tens * 10 + ones;
    return problem(`${left} + ${right} = ?`, fraction(left + right), level);
  }
  if (level === 2) {
    const leftTens = randomInt(rng, 1, 7);
    const rightTens = randomInt(rng, 1, 9 - leftTens);
    const leftOnes = randomInt(rng, 0, 8);
    const rightOnes = randomInt(rng, 0, 9 - leftOnes);
    const left = leftTens * 10 + leftOnes;
    const right = rightTens * 10 + rightOnes;
    return problem(`${left} + ${right} = ?`, fraction(left + right), level);
  }
  if (level === 3) {
    const leftTens = randomInt(rng, 2, 8);
    const leftOnes = randomInt(rng, 1, 9);
    const left = leftTens * 10 + leftOnes;
    const rightTens = randomInt(rng, 1, 9 - leftTens);
    const rightOnes = randomInt(rng, 10 - leftOnes, 9);
    const right = rightTens * 10 + rightOnes;
    return problem(`${left} + ${right} = ?`, fraction(left + right), level);
  }
  if (level === 4) {
    let left = randomInt(rng, 100, 899);
    while (left % 100 === 0) left = randomInt(rng, 100, 899);
    let right = randomInt(rng, 11, 99);
    while ((left % 10) + (right % 10) < 10 && (Math.floor(left / 10) % 10) + Math.floor(right / 10) < 10) {
      right = randomInt(rng, 11, 99);
    }
    return problem(`${left} + ${right} = ?`, fraction(left + right), level);
  }
  if (level === 5) {
    const leftTens = randomInt(rng, 2, 9);
    const rightTens = randomInt(rng, 1, leftTens - 1);
    const leftOnes = randomInt(rng, 0, 9);
    const rightOnes = randomInt(rng, 0, leftOnes);
    const left = leftTens * 10 + leftOnes;
    const right = rightTens * 10 + rightOnes;
    return problem(`${left} − ${right} = ?`, fraction(left - right), level);
  }
  if (level === 6) {
    const leftTens = randomInt(rng, 2, 9);
    const rightTens = randomInt(rng, 1, leftTens - 1);
    const leftOnes = randomInt(rng, 0, 8);
    const rightOnes = randomInt(rng, leftOnes + 1, 9);
    const left = leftTens * 10 + leftOnes;
    const right = rightTens * 10 + rightOnes;
    return problem(`${left} − ${right} = ?`, fraction(left - right), level);
  }
  if (level === 7) {
    const left = randomInt(rng, 2, 9) * 100 + randomInt(rng, 0, 9) * 10 + randomInt(rng, 0, 8);
    const right = randomInt(rng, 1, 9) * 10 + randomInt(rng, (left % 10) + 1, 9);
    return problem(`${left} − ${right} = ?`, fraction(left - right), level);
  }
  if (level === 8) {
    const left = randomInt(rng, 2, 9);
    const right = randomInt(rng, 2, 9);
    return problem(`${left} × ${right} = ?`, fraction(left * right), level);
  }
  if (level === 9) {
    const left = randomInt(rng, 11, 99);
    const right = randomInt(rng, 2, 9);
    return problem(`${left} × ${right} = ?`, fraction(left * right), level);
  }
  if (level === 10) {
    const left = randomInt(rng, 100, 499);
    const right = randomInt(rng, 2, 9);
    return problem(`${left} × ${right} = ?`, fraction(left * right), level);
  }
  if (level === 11) {
    const divisor = randomInt(rng, 2, 9);
    const quotient = randomInt(rng, 2, 9);
    return problem(`${divisor * quotient} ÷ ${divisor} = ?`, fraction(quotient), level);
  }
  if (level === 12) {
    const divisor = randomInt(rng, 2, 9);
    const quotient = randomInt(rng, 11, Math.floor(99 / divisor));
    return problem(`${divisor * quotient} ÷ ${divisor} = ?`, fraction(quotient), level);
  }
  if (level === 13) {
    const divisor = randomInt(rng, 2, 9);
    const quotient = randomInt(rng, Math.ceil(100 / divisor), Math.min(120, Math.floor(999 / divisor)));
    return problem(`${divisor * quotient} ÷ ${divisor} = ?`, fraction(quotient), level);
  }
  if (level === 14) {
    const leftTenths = randomInt(rng, 11, 89);
    const rightTenths = randomInt(rng, 1, 49);
    return problem(`${(leftTenths / 10).toFixed(1)} + ${(rightTenths / 10).toFixed(1)} = ?`, fraction(leftTenths + rightTenths, 10), level, "decimal");
  }
  if (level === 15) {
    const leftTenths = randomInt(rng, 20, 99);
    const rightTenths = randomInt(rng, 1, leftTenths - 1);
    return problem(`${(leftTenths / 10).toFixed(1)} − ${(rightTenths / 10).toFixed(1)} = ?`, fraction(leftTenths - rightTenths, 10), level, "decimal");
  }
  if (level === 16) {
    const denominator = randomInt(rng, 3, 10);
    let left = randomInt(rng, 1, denominator - 1);
    let right = randomInt(rng, 1, denominator - 1);
    const operator = randomChoice(rng, ["+", "−"]);
    if (operator === "−" && right > left) [left, right] = [right, left];
    const answer = addFractions(fraction(left, denominator), fraction(operator === "+" ? right : -right, denominator));
    return problem(`${left}/${denominator} ${operator} ${right}/${denominator} = ?`, answer, level, "fraction");
  }
  if (level === 17) {
    const leftDenominator = randomInt(rng, 2, 8);
    let rightDenominator = randomInt(rng, 2, 8);
    while (rightDenominator === leftDenominator) rightDenominator = randomInt(rng, 2, 8);
    const left = fraction(randomInt(rng, 1, leftDenominator - 1), leftDenominator);
    const right = fraction(randomInt(rng, 1, rightDenominator - 1), rightDenominator);
    return problem(
      `${left.numerator}/${left.denominator} + ${right.numerator}/${right.denominator} = ?`,
      addFractions(left, right),
      level,
      "fraction",
    );
  }
  throw new Error(`지원하지 않는 단계입니다: ${level}`);
}

export function makeProblem(level, rng = Math.random, excluded = []) {
  const excludedSet = new Set(excluded);
  let candidate = generateCandidate(Number(level), rng);
  for (let attempt = 0; attempt < 50 && excludedSet.has(candidate.signature); attempt += 1) {
    candidate = generateCandidate(Number(level), rng);
  }
  return candidate;
}

export function parseAnswer(value) {
  const cleaned = String(value ?? "").trim().replaceAll(",", "");
  if (!cleaned) return null;
  if (/^[+-]?\d+\s*\/\s*[+-]?\d+$/.test(cleaned)) {
    const [numerator, denominator] = cleaned.split("/").map((item) => Number(item.trim()));
    if (denominator === 0) return null;
    return fraction(numerator, denominator);
  }
  if (!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(cleaned)) return null;
  const sign = cleaned.startsWith("-") ? -1 : 1;
  const unsigned = cleaned.replace(/^[+-]/, "");
  const [integerPart, decimalPart = ""] = unsigned.split(".");
  const denominator = 10 ** decimalPart.length;
  const numerator = sign * (Number(integerPart || 0) * denominator + Number(decimalPart || 0));
  return fraction(numerator, denominator);
}

export function isCorrectAnswer(currentProblem, value) {
  const parsed = parseAnswer(value);
  return Boolean(
    parsed &&
      parsed.numerator === currentProblem.answer.numerator &&
      parsed.denominator === currentProblem.answer.denominator,
  );
}

export function levelsForDomain(domain) {
  return Object.keys(LEVELS).map(Number).filter((level) => LEVELS[level].domain === domain);
}

export function firstLevelForDomain(domain) {
  const levels = levelsForDomain(domain);
  if (!levels.length) throw new Error(`지원하지 않는 학습 영역입니다: ${domain}`);
  return levels[0];
}

function neighborLevel(level, direction) {
  const levels = levelsForDomain(LEVELS[level].domain);
  const index = levels.indexOf(Number(level));
  return levels[Math.max(0, Math.min(levels.length - 1, index + direction))];
}

export function chooseNextLevel(currentLevel, records) {
  if (!records.length) return currentLevel;
  const domain = LEVELS[currentLevel].domain;
  const recent = records.slice(-4).filter((record) => LEVELS[Number(record.level)]?.domain === domain);
  const sameLevel = recent.filter((record) => Number(record.level) === Number(currentLevel));
  if (sameLevel.length >= 4 && sameLevel.slice(-4).every((record) => Boolean(record.correct))) {
    return neighborLevel(currentLevel, 1);
  }
  const lastThree = recent.slice(-3);
  if (lastThree.length === 3 && lastThree.filter((record) => !record.correct).length >= 2) {
    return neighborLevel(currentLevel, -1);
  }
  return currentLevel;
}

export function adjustLevelForFeeling(level, feeling, accuracy) {
  if (feeling === "easy" && accuracy >= 70) return neighborLevel(level, 1);
  if (feeling === "hard") return neighborLevel(level, -1);
  return Number(level);
}

export function summarizeSession(records, elapsedSeconds) {
  const attempted = records.length;
  const correct = records.filter((record) => Boolean(record.correct)).length;
  const accuracy = attempted ? (correct / attempted) * 100 : 0;
  let recommendedLevel;
  let domain;
  let message;
  if (!records.length) {
    recommendedLevel = 2;
    domain = LEVELS[recommendedLevel].domain;
    message = "오늘은 시작 화면까지 확인했어요. 다음에는 한 문제부터 가볍게 시작해 봐요.";
  } else {
    const finalLevel = Number(records.at(-1).level);
    domain = LEVELS[finalLevel].domain;
    const recent = records.slice(-5);
    const recentAccuracy = recent.filter((record) => Boolean(record.correct)).length / recent.length;
    if (recentAccuracy >= 0.8) {
      recommendedLevel = neighborLevel(finalLevel, 1);
      message = "정확하게 잘 풀었어요. 다음에는 같은 영역에서 한 단계 더 도전해도 좋아요.";
    } else if (recentAccuracy < 0.6) {
      recommendedLevel = neighborLevel(finalLevel, -1);
      message = "어려운 문제에도 끝까지 도전했어요. 다음에는 한 단계 쉬운 문제로 자신감을 채워요.";
    } else {
      recommendedLevel = finalLevel;
      message = "지금 단계가 잘 맞아요. 같은 유형을 조금 더 익히면 더 편해질 거예요.";
    }
  }
  return { attempted, correct, accuracy, elapsedSeconds: Math.max(0, Math.trunc(elapsedSeconds)), recommendedLevel, domain, message };
}

export function normalizedSettings(settings) {
  const source = settings || {};
  const enabledSource = source.enabledDomains || source.enabled_domains || DEFAULT_SETTINGS.enabledDomains;
  const enabledDomains = DOMAIN_ORDER.filter((domain) => enabledSource.includes(domain));
  const safeEnabled = enabledDomains.length ? enabledDomains : ["addition"];
  let focusDomain = source.focusDomain || source.focus_domain || DEFAULT_SETTINGS.focusDomain;
  if (!safeEnabled.includes(focusDomain)) focusDomain = safeEnabled[0];
  let forcedLevel = Number(source.forcedLevel ?? source.forced_level ?? firstLevelForDomain(focusDomain));
  if (!levelsForDomain(focusDomain).includes(forcedLevel)) forcedLevel = firstLevelForDomain(focusDomain);
  return {
    mode: source.mode === "focus" ? "focus" : "automatic",
    enabledDomains: safeEnabled,
    focusDomain,
    forcedLevel,
  };
}

export function domainIsMastered(domain, sessions) {
  const domainSessions = sessions.filter((session) => session.domain === domain);
  if (domainSessions.length < 2) return false;
  return domainSessions.slice(-2).every(
    (session) => Number(session.accuracy || 0) >= 80 && session.feeling !== "hard" && Number(session.attempted || 0) >= 5,
  );
}

export function unlockedDomains(sessions, settings) {
  const selected = normalizedSettings(settings).enabledDomains;
  const unlocked = [];
  for (const domain of selected) {
    if (!unlocked.length) {
      unlocked.push(domain);
    } else if (domainIsMastered(unlocked.at(-1), sessions)) {
      unlocked.push(domain);
    } else {
      break;
    }
  }
  return unlocked;
}

export function chooseStartLevel(sessions, settings) {
  const config = normalizedSettings(settings);
  if (config.mode === "focus") return config.forcedLevel;
  const domains = unlockedDomains(sessions, config);
  const counts = Object.fromEntries(domains.map((domain) => [domain, 0]));
  for (const session of sessions) if (session.domain in counts) counts[session.domain] += 1;
  const chosenDomain = domains.reduce((best, domain) => (counts[domain] < counts[best] ? domain : best), domains[0]);
  const domainSessions = sessions.filter((session) => session.domain === chosenDomain);
  if (!domainSessions.length) return DOMAIN_INITIAL_LEVEL[chosenDomain] || firstLevelForDomain(chosenDomain);
  const recommendation = Number(domainSessions.at(-1).recommendedLevel ?? domainSessions.at(-1).recommended_level);
  return levelsForDomain(chosenDomain).includes(recommendation) ? recommendation : firstLevelForDomain(chosenDomain);
}
