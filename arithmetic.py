from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import random
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Level:
    name: str
    description: str
    domain: str


@dataclass(frozen=True)
class Problem:
    expression: str
    answer: Fraction
    level: int
    answer_kind: str = "integer"

    @property
    def signature(self) -> str:
        return self.expression.replace(" = ?", "")

    @property
    def answer_text(self) -> str:
        if self.answer_kind == "fraction":
            if self.answer.denominator == 1:
                return str(self.answer.numerator)
            return f"{self.answer.numerator}/{self.answer.denominator}"
        if self.answer_kind == "decimal":
            return f"{float(self.answer):.1f}"
        return str(self.answer.numerator)


@dataclass(frozen=True)
class SessionSummary:
    attempted: int
    correct: int
    accuracy: float
    elapsed_seconds: int
    recommended_level: int
    domain: str
    message: str


DOMAIN_LABELS = {
    "addition": "덧셈",
    "subtraction": "뺄셈",
    "multiplication": "곱셈",
    "division": "나눗셈",
    "decimal": "소수",
    "fraction": "분수",
}

DOMAIN_ORDER = list(DOMAIN_LABELS)

LEVELS = {
    1: Level("두 자리 수 + 한 자리 수", "받아올림이 없는 덧셈", "addition"),
    2: Level("두 자리 수 + 두 자리 수", "받아올림이 없는 덧셈", "addition"),
    3: Level("두 자리 수 + 두 자리 수", "받아올림이 있는 덧셈", "addition"),
    4: Level("세 자리 수 + 두 자리 수", "받아올림이 있는 덧셈", "addition"),
    5: Level("두 자리 수 − 두 자리 수", "받아내림이 없는 뺄셈", "subtraction"),
    6: Level("두 자리 수 − 두 자리 수", "받아내림이 있는 뺄셈", "subtraction"),
    7: Level("세 자리 수 − 두 자리 수", "받아내림이 있는 뺄셈", "subtraction"),
    8: Level("한 자리 수 × 한 자리 수", "구구단", "multiplication"),
    9: Level("두 자리 수 × 한 자리 수", "곱셈 확장", "multiplication"),
    10: Level("세 자리 수 × 한 자리 수", "곱셈 심화", "multiplication"),
    11: Level("곱셈표 안의 나눗셈", "나머지가 없는 나눗셈", "division"),
    12: Level("두 자리 수 ÷ 한 자리 수", "나머지가 없는 나눗셈", "division"),
    13: Level("세 자리 수 ÷ 한 자리 수", "나머지가 없는 나눗셈", "division"),
    14: Level("소수 한 자리 덧셈", "소수점 위치 맞추기", "decimal"),
    15: Level("소수 한 자리 뺄셈", "0보다 큰 결과", "decimal"),
    16: Level("분모가 같은 분수", "덧셈과 뺄셈", "fraction"),
    17: Level("분모가 다른 분수", "통분이 필요한 덧셈", "fraction"),
}


def levels_for_domain(domain: str) -> list[int]:
    return [level for level, info in LEVELS.items() if info.domain == domain]


def first_level_for_domain(domain: str) -> int:
    levels = levels_for_domain(domain)
    if not levels:
        raise ValueError(f"지원하지 않는 학습 영역입니다: {domain}")
    return levels[0]


def _problem_for_level(level: int, rng: random.Random) -> Problem:
    if level == 1:
        tens = rng.randint(1, 8)
        ones = rng.randint(0, 8)
        right = rng.randint(1, 9 - ones)
        left = tens * 10 + ones
        return Problem(f"{left} + {right} = ?", Fraction(left + right), level)

    if level == 2:
        left_tens = rng.randint(1, 7)
        right_tens = rng.randint(1, 9 - left_tens)
        left_ones = rng.randint(0, 8)
        right_ones = rng.randint(0, 9 - left_ones)
        left = left_tens * 10 + left_ones
        right = right_tens * 10 + right_ones
        return Problem(f"{left} + {right} = ?", Fraction(left + right), level)

    if level == 3:
        left_tens = rng.randint(2, 8)
        left_ones = rng.randint(1, 9)
        left = left_tens * 10 + left_ones
        right_tens = rng.randint(1, 9 - left_tens)
        right_ones = rng.randint(10 - left_ones, 9)
        right = right_tens * 10 + right_ones
        return Problem(f"{left} + {right} = ?", Fraction(left + right), level)

    if level == 4:
        left = rng.randint(100, 899)
        right = rng.randint(11, 99)
        while (left % 10 + right % 10 < 10) and (
            (left // 10) % 10 + right // 10 < 10
        ):
            right = rng.randint(11, 99)
        return Problem(f"{left} + {right} = ?", Fraction(left + right), level)

    if level == 5:
        left_tens = rng.randint(2, 9)
        right_tens = rng.randint(1, left_tens - 1)
        left_ones = rng.randint(0, 9)
        right_ones = rng.randint(0, left_ones)
        left = left_tens * 10 + left_ones
        right = right_tens * 10 + right_ones
        return Problem(f"{left} − {right} = ?", Fraction(left - right), level)

    if level == 6:
        left_tens = rng.randint(2, 9)
        right_tens = rng.randint(1, left_tens - 1)
        left_ones = rng.randint(0, 8)
        right_ones = rng.randint(left_ones + 1, 9)
        left = left_tens * 10 + left_ones
        right = right_tens * 10 + right_ones
        return Problem(f"{left} − {right} = ?", Fraction(left - right), level)

    if level == 7:
        left = rng.randint(2, 9) * 100 + rng.randint(0, 9) * 10 + rng.randint(0, 8)
        right = rng.randint(1, 9) * 10 + rng.randint(left % 10 + 1, 9)
        return Problem(f"{left} − {right} = ?", Fraction(left - right), level)

    if level == 8:
        left, right = rng.randint(2, 9), rng.randint(2, 9)
        return Problem(f"{left} × {right} = ?", Fraction(left * right), level)

    if level == 9:
        left, right = rng.randint(11, 99), rng.randint(2, 9)
        return Problem(f"{left} × {right} = ?", Fraction(left * right), level)

    if level == 10:
        left, right = rng.randint(100, 499), rng.randint(2, 9)
        return Problem(f"{left} × {right} = ?", Fraction(left * right), level)

    if level == 11:
        divisor, quotient = rng.randint(2, 9), rng.randint(2, 9)
        dividend = divisor * quotient
        return Problem(f"{dividend} ÷ {divisor} = ?", Fraction(quotient), level)

    if level == 12:
        divisor = rng.randint(2, 9)
        quotient = rng.randint(11, 99 // divisor)
        dividend = divisor * quotient
        return Problem(f"{dividend} ÷ {divisor} = ?", Fraction(quotient), level)

    if level == 13:
        divisor = rng.randint(2, 9)
        minimum_quotient = (100 + divisor - 1) // divisor
        quotient = rng.randint(minimum_quotient, min(120, 999 // divisor))
        dividend = divisor * quotient
        return Problem(f"{dividend} ÷ {divisor} = ?", Fraction(quotient), level)

    if level == 14:
        left_tenths, right_tenths = rng.randint(11, 89), rng.randint(1, 49)
        return Problem(
            f"{left_tenths / 10:.1f} + {right_tenths / 10:.1f} = ?",
            Fraction(left_tenths + right_tenths, 10),
            level,
            "decimal",
        )

    if level == 15:
        left_tenths = rng.randint(20, 99)
        right_tenths = rng.randint(1, left_tenths - 1)
        return Problem(
            f"{left_tenths / 10:.1f} − {right_tenths / 10:.1f} = ?",
            Fraction(left_tenths - right_tenths, 10),
            level,
            "decimal",
        )

    if level == 16:
        denominator = rng.randint(3, 10)
        left = rng.randint(1, denominator - 1)
        right = rng.randint(1, denominator - 1)
        operator = rng.choice(["+", "−"])
        if operator == "−" and right > left:
            left, right = right, left
        answer = Fraction(left, denominator) + (
            Fraction(right, denominator) if operator == "+" else -Fraction(right, denominator)
        )
        return Problem(
            f"{left}/{denominator} {operator} {right}/{denominator} = ?",
            answer,
            level,
            "fraction",
        )

    if level == 17:
        left_denominator = rng.randint(2, 8)
        right_denominator = rng.randint(2, 8)
        while right_denominator == left_denominator:
            right_denominator = rng.randint(2, 8)
        left = Fraction(rng.randint(1, left_denominator - 1), left_denominator)
        right = Fraction(rng.randint(1, right_denominator - 1), right_denominator)
        return Problem(
            f"{left.numerator}/{left.denominator} + {right.numerator}/{right.denominator} = ?",
            left + right,
            level,
            "fraction",
        )

    raise ValueError(f"지원하지 않는 단계입니다: {level}")


def make_problem(
    level: int,
    rng: random.Random | None = None,
    exclude: Iterable[str] | None = None,
) -> Problem:
    rng = rng or random.Random()
    excluded = set(exclude or ())
    candidate = _problem_for_level(level, rng)
    for _ in range(50):
        if candidate.signature not in excluded:
            return candidate
        candidate = _problem_for_level(level, rng)
    return candidate


def parse_answer(answer_text: str) -> Fraction | None:
    cleaned = answer_text.strip().replace(",", "")
    if not cleaned:
        return None
    try:
        if "/" in cleaned:
            numerator, denominator = cleaned.split("/", 1)
            return Fraction(int(numerator.strip()), int(denominator.strip()))
        return Fraction(Decimal(cleaned))
    except (ValueError, ZeroDivisionError, InvalidOperation):
        return None


def is_correct_answer(problem: Problem, answer_text: str) -> bool:
    parsed = parse_answer(answer_text)
    return parsed is not None and parsed == problem.answer


def _neighbor_level(level: int, direction: int) -> int:
    domain_levels = levels_for_domain(LEVELS[level].domain)
    index = domain_levels.index(level)
    return domain_levels[max(0, min(len(domain_levels) - 1, index + direction))]


def choose_next_level(current_level: int, records: Sequence[Mapping[str, object]]) -> int:
    """한 세션에서는 같은 영역 안에서만 한 단계씩 조절한다."""
    if not records:
        return current_level

    current_domain = LEVELS[current_level].domain
    recent = [
        record
        for record in records[-4:]
        if LEVELS[int(record["level"])].domain == current_domain
    ]
    same_level = [record for record in recent if int(record["level"]) == current_level]
    if len(same_level) >= 4 and all(bool(record["correct"]) for record in same_level[-4:]):
        return _neighbor_level(current_level, 1)

    last_three = recent[-3:]
    wrong_count = sum(not bool(record["correct"]) for record in last_three)
    if len(last_three) == 3 and wrong_count >= 2:
        return _neighbor_level(current_level, -1)

    return current_level


def adjust_level_for_feeling(level: int, feeling: str | None, accuracy: float) -> int:
    if feeling == "easy" and accuracy >= 70:
        return _neighbor_level(level, 1)
    if feeling == "hard":
        return _neighbor_level(level, -1)
    return level


def summarize_session(
    records: Sequence[Mapping[str, object]], elapsed_seconds: int
) -> SessionSummary:
    attempted = len(records)
    correct = sum(bool(record["correct"]) for record in records)
    accuracy = correct / attempted * 100 if attempted else 0.0

    if not records:
        recommended_level = 2
        domain = LEVELS[recommended_level].domain
        message = "오늘은 시작 화면까지 확인했어요. 다음에는 한 문제부터 가볍게 시작해 봐요."
    else:
        final_level = int(records[-1]["level"])
        domain = LEVELS[final_level].domain
        recent = list(records[-5:])
        recent_accuracy = sum(bool(record["correct"]) for record in recent) / len(recent)
        if recent_accuracy >= 0.8:
            recommended_level = _neighbor_level(final_level, 1)
            message = "정확하게 잘 풀었어요. 다음에는 같은 영역에서 한 단계 더 도전해도 좋아요."
        elif recent_accuracy < 0.6:
            recommended_level = _neighbor_level(final_level, -1)
            message = "어려운 문제에도 끝까지 도전했어요. 다음에는 한 단계 쉬운 문제로 자신감을 채워요."
        else:
            recommended_level = final_level
            message = "지금 단계가 잘 맞아요. 같은 유형을 조금 더 익히면 더 편해질 거예요."

    return SessionSummary(
        attempted=attempted,
        correct=correct,
        accuracy=accuracy,
        elapsed_seconds=max(0, int(elapsed_seconds)),
        recommended_level=recommended_level,
        domain=domain,
        message=message,
    )
