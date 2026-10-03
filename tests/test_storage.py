import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import storage


class LocalStorageTests(unittest.TestCase):
    def test_save_update_and_list_session(self):
        with tempfile.TemporaryDirectory(dir=".") as directory:
            root = Path(directory)
            with (
                patch.object(storage, "SESSIONS_PATH", root / "sessions.json"),
                patch.object(storage, "SETTINGS_PATH", root / "settings.json"),
                patch.object(storage, "storage_mode", return_value="local"),
            ):
                saved = storage.save_session(
                    {"local_date": "2026-10-04", "domain": "addition", "accuracy": 80}
                )
                storage.update_session(saved["id"], {"feeling": "normal"})
                sessions = storage.list_sessions()
                self.assertEqual(len(sessions), 1)
                self.assertEqual(sessions[0]["feeling"], "normal")

                config = storage.save_settings(
                    {
                        "mode": "focus",
                        "enabled_domains": ["multiplication"],
                        "focus_domain": "multiplication",
                        "forced_level": 9,
                    }
                )
                self.assertEqual(config["forced_level"], 9)
                self.assertEqual(storage.load_settings()["focus_domain"], "multiplication")


if __name__ == "__main__":
    unittest.main()
