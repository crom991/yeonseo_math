import unittest

from notifications import build_result_message


class NotificationTests(unittest.TestCase):
    def test_result_message_contains_parent_summary(self):
        message = build_result_message(
            {
                "local_date": "2026-10-04",
                "domain": "addition",
                "final_level": 2,
                "recommended_level": 3,
                "correct": 8,
                "attempted": 10,
                "accuracy": 80,
                "elapsed_seconds": 600,
                "feeling": "normal",
            }
        )
        self.assertIn("2026-10-04", message)
        self.assertIn("정답: 8/10개", message)
        self.assertIn("딱 좋았어요", message)
        self.assertIn("10분 0초", message)
        self.assertTrue(
            message.endswith(
                "🔗 연산 웹페이지: https://yeonseo-math.exambreaker-dev.workers.dev/"
            )
        )


if __name__ == "__main__":
    unittest.main()
