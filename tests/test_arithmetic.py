import random
import unittest

from arithmetic import LEVELS, choose_next_level, make_problem, summarize_session


class ProblemGenerationTests(unittest.TestCase):
    def test_every_level_generates_valid_answers(self):
        for level in LEVELS:
            rng = random.Random(100 + level)
            for _ in range(100):
                problem = make_problem(level, rng)
                if problem.operator == "+":
                    self.assertEqual(problem.left + problem.right, problem.answer)
                else:
                    self.assertEqual(problem.left - problem.right, problem.answer)
                    self.assertGreaterEqual(problem.answer, 0)

    def test_level_two_has_no_carry(self):
        rng = random.Random(7)
        for _ in range(100):
            problem = make_problem(2, rng)
            self.assertLess((problem.left % 10) + (problem.right % 10), 10)

    def test_level_three_always_has_ones_carry(self):
        rng = random.Random(8)
        for _ in range(100):
            problem = make_problem(3, rng)
            self.assertGreaterEqual((problem.left % 10) + (problem.right % 10), 10)

    def test_level_five_always_has_borrow(self):
        rng = random.Random(9)
        for _ in range(100):
            problem = make_problem(5, rng)
            self.assertLess(problem.left % 10, problem.right % 10)

    def test_excludes_recent_problem(self):
        rng = random.Random(10)
        first = make_problem(2, rng)
        second = make_problem(2, rng, exclude={first.signature})
        self.assertNotEqual(first.signature, second.signature)


class AdaptationTests(unittest.TestCase):
    def _record(self, level, correct):
        return {"level": level, "correct": correct}

    def test_four_correct_answers_raise_one_level(self):
        records = [self._record(2, True) for _ in range(4)]
        self.assertEqual(choose_next_level(2, records), 3)

    def test_two_errors_in_three_lower_one_level(self):
        records = [
            self._record(3, False),
            self._record(3, True),
            self._record(3, False),
        ]
        self.assertEqual(choose_next_level(3, records), 2)

    def test_level_stays_inside_bounds(self):
        wrong = [self._record(1, False) for _ in range(3)]
        correct = [self._record(6, True) for _ in range(4)]
        self.assertEqual(choose_next_level(1, wrong), 1)
        self.assertEqual(choose_next_level(6, correct), 6)


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


if __name__ == "__main__":
    unittest.main()
