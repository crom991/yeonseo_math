from fractions import Fraction
import random
import unittest

from arithmetic import (
    LEVELS,
    adjust_level_for_feeling,
    choose_next_level,
    is_correct_answer,
    make_problem,
    parse_answer,
    summarize_session,
)


class ProblemGenerationTests(unittest.TestCase):
    def test_every_level_generates_an_answer_that_is_accepted(self):
        for level in LEVELS:
            rng = random.Random(100 + level)
            for _ in range(100):
                problem = make_problem(level, rng)
                self.assertTrue(is_correct_answer(problem, problem.answer_text))

    def test_level_two_has_no_ones_carry(self):
        rng = random.Random(7)
        for _ in range(100):
            problem = make_problem(2, rng)
            expression = problem.expression.replace(" = ?", "")
            left, right = [int(value.strip()) for value in expression.split("+")]
            self.assertLess((left % 10) + (right % 10), 10)

    def test_level_three_always_has_ones_carry(self):
        rng = random.Random(8)
        for _ in range(100):
            problem = make_problem(3, rng)
            expression = problem.expression.replace(" = ?", "")
            left, right = [int(value.strip()) for value in expression.split("+")]
            self.assertGreaterEqual((left % 10) + (right % 10), 10)

    def test_fraction_and_decimal_equivalent_answers_are_accepted(self):
        fraction_problem = make_problem(16, random.Random(1))
        equivalent = Fraction(fraction_problem.answer.numerator * 2, fraction_problem.answer.denominator * 2)
        self.assertTrue(
            is_correct_answer(
                fraction_problem, f"{equivalent.numerator}/{equivalent.denominator}"
            )
        )
        self.assertEqual(parse_answer("1.5"), Fraction(3, 2))

    def test_division_levels_keep_the_promised_digit_count(self):
        rng = random.Random(12)
        for level, minimum, maximum in [(12, 10, 99), (13, 100, 999)]:
            for _ in range(100):
                problem = make_problem(level, rng)
                dividend = int(problem.expression.split("÷")[0].strip())
                self.assertGreaterEqual(dividend, minimum)
                self.assertLessEqual(dividend, maximum)

    def test_excludes_recent_problem(self):
        rng = random.Random(10)
        first = make_problem(2, rng)
        second = make_problem(2, rng, exclude={first.signature})
        self.assertNotEqual(first.signature, second.signature)


class AdaptationTests(unittest.TestCase):
    def _record(self, level, correct):
        return {"level": level, "correct": correct}

    def test_four_correct_answers_raise_one_level_inside_domain(self):
        records = [self._record(2, True) for _ in range(4)]
        self.assertEqual(choose_next_level(2, records), 3)

    def test_last_level_does_not_cross_into_next_domain(self):
        records = [self._record(4, True) for _ in range(4)]
        self.assertEqual(choose_next_level(4, records), 4)

    def test_two_errors_in_three_lower_one_level(self):
        records = [
            self._record(3, False),
            self._record(3, True),
            self._record(3, False),
        ]
        self.assertEqual(choose_next_level(3, records), 2)

    def test_feeling_adjustment_stays_inside_domain(self):
        self.assertEqual(adjust_level_for_feeling(2, "easy", 80), 3)
        self.assertEqual(adjust_level_for_feeling(1, "hard", 90), 1)
        self.assertEqual(adjust_level_for_feeling(4, "easy", 90), 4)


class SummaryTests(unittest.TestCase):
    def test_summary_counts_and_recommendation(self):
        records = [
            {"level": 2, "correct": True},
            {"level": 2, "correct": True},
            {"level": 2, "correct": False},
            {"level": 2, "correct": True},
            {"level": 2, "correct": True},
        ]
        summary = summarize_session(records, 600)
        self.assertEqual(summary.attempted, 5)
        self.assertEqual(summary.correct, 4)
        self.assertEqual(summary.accuracy, 80.0)
        self.assertEqual(summary.recommended_level, 3)
        self.assertEqual(summary.domain, "addition")


if __name__ == "__main__":
    unittest.main()
