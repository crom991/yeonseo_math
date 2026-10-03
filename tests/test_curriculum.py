import unittest

from curriculum import choose_start_level, domain_is_mastered, unlocked_domains


def session(domain, accuracy=85, feeling="normal", attempted=10, recommended_level=2):
    return {
        "domain": domain,
        "accuracy": accuracy,
        "feeling": feeling,
        "attempted": attempted,
        "recommended_level": recommended_level,
    }


class CurriculumTests(unittest.TestCase):
    def test_first_session_starts_at_two_digit_addition(self):
        self.assertEqual(choose_start_level([], None), 2)

    def test_next_domain_unlocks_after_two_mastery_sessions(self):
        sessions = [session("addition"), session("addition", recommended_level=3)]
        self.assertTrue(domain_is_mastered("addition", sessions))
        self.assertEqual(unlocked_domains(sessions, None), ["addition", "subtraction"])
        self.assertEqual(choose_start_level(sessions, None), 5)

    def test_hard_feedback_prevents_unlock(self):
        sessions = [session("addition"), session("addition", feeling="hard")]
        self.assertFalse(domain_is_mastered("addition", sessions))
        self.assertEqual(unlocked_domains(sessions, None), ["addition"])

    def test_parent_focus_overrides_automatic_choice(self):
        settings = {
            "mode": "focus",
            "enabled_domains": ["addition", "multiplication"],
            "focus_domain": "multiplication",
            "forced_level": 9,
        }
        self.assertEqual(choose_start_level([], settings), 9)


if __name__ == "__main__":
    unittest.main()
