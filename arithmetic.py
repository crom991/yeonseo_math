from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Level:
    name: str
    description: str


@dataclass(frozen=True)
class Problem:
    left: int
    operator: str
    right: int
    answer: int
    level: int

    @property
    def expression(self) -> str:
        return f"{self.left} {self.operator} {self.right} = ?"

    @property
    def signature(self) -> str:
        return f"{self.left}{self.operator}{self.right}"


@dataclass(frozen=True)
class SessionSummary:
    attempted: int
    correct: int
    accuracy: float
    elapsed_seconds: int
    recommended_level: int
    message: str


LEVELS = {
    1: Level("두 자리 수 + 한 자리 수", "받아올림이 없는 덧셈"),
    2: Level("두 자리 수 + 두 자리 수", "받아올림이 없는 덧셈"),
    3: Level("두 자리 수 + 두 자리 수", "받아올림이 있는 덧셈"),
    4: Level("두 자리 수 − 두 자리 수", "받아내림이 없는 뺄셈"),
    5: Level("두 자리 수 − 두 자리 수", "받아내림이 있는 뺄셈"),
    6: Level("세 자리 수 + 두 자리 수", "받아올림이 있는 덧셈"),
}


def _problem_for_level(level: int, rng: random.Random) -> Problem:
    if level == 1:
        tens = rng.randint(1, 8)
        ones = rng.randint(0, 8)
        right = rng.randint(1, 9 - ones)
        left = tens * 10 + ones
        return Problem(left, "+", right, left + right, level)

    if level == 2:
        left_tens = rng.randint(1, 7)
        right_tens = rng.randint(1, 9 - left_tens)
        left_ones = rng.randint(0, 8)
        right_ones = rng.randint(0, 9 - left_ones)
        left = left_tens * 10 + left_ones
        right = right_tens * 10 + right_ones
        return Problem(left, "+", right, left + right, level)

    if level == 3:
        left_tens = rng.randint(2, 8)
        left_ones = rng.randint(1, 9)
        left = left_tens * 10 + left_ones
        right_tens = rng.randint(1, 9 - left // 10)
        right_ones = rng.randint(10 - left_ones, 9)
        right = right_tens * 10 + right_ones
        return Problem(left, "+", right, left + right, level)

    if level == 4:
        left_tens = rng.randint(2, 9)
        right_tens = rng.randint(1, left_tens - 1)
        left_ones = rng.randint(0, 9)
        right_ones = rng.randint(0, left_ones)
        left = left_tens * 10 + left_ones
        right = right_tens * 10 + right_ones
        return Problem(left, "−", right, left - right, level)

    if level == 5:
        left_tens = rng.randint(2, 9)
        right_tens = rng.randint(1, left_tens - 1)
        left_ones = rng.randint(0, 8)
        right_ones = rng.randint(left_ones + 1, 9)
        left = left_tens * 10 + left_ones
        right = right_tens * 10 + right_ones
        return Problem(left, "−", right, left - right, level)

    if level == 6:
        left = rng.randint(100, 899)
        right = rng.randint(11, 99)
        while (left % 10 + right % 10 < 10) and (
            (left // 10) % 10 + right // 10 < 10
        ):
            right = rng.randint(11, 99)
        return Problem(left, "+", right, left + right, level)

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


def choose_next_level(current_level: int, records: Sequence[Mapping[str, object]]) -> int:
    """최근 성취만 보고 한 단계씩 조절해 아이의 부담을 낮춘다."""
    if not records:
        return current_level

    recent = list(records[-4:])
    same_level = [record for record in recent if int(record["level"]) == current_level]
    if len(same_level) >= 4 and all(bool(record["correct"]) for record in same_level[-4:]):
        return min(max(LEVELS), current_level + 1)

    last_three = list(records[-3:])
    wrong_count = sum(not bool(record["correct"]) for record in last_three)
    if len(last_three) == 3 and wrong_count >= 2:
        return max(min(LEVELS), current_level - 1)

    return current_level


def summarize_session(
    records: Sequence[Mapping[str, object]], elapsed_seconds: int
) -> SessionSummary:
    attempted = len(records)
    correct = sum(bool(record["correct"]) for record in records)
    accuracy = correct / attempted * 100 if attempted else 0.0

    if not records:
        recommended_level = 2
        message = "오늘은 시작 화면까지 확인했어요. 다음에는 한 문제부터 가볍게 시작해 봐요."
    else:
        final_level = int(records[-1]["level"])
        recent = list(records[-5:])
        recent_accuracy = sum(bool(record["correct"]) for record in recent) / len(recent)
        if recent_accuracy >= 0.8:
            recommended_level = min(max(LEVELS), final_level + 1)
            message = "정확하게 잘 풀었어요. 다음에는 한 단계 더 도전해도 좋아요."
        elif recent_accuracy < 0.6:
            recommended_level = max(min(LEVELS), final_level - 1)
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
        message=message,
    )
