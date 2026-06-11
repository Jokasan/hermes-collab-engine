import unittest
from unittest.mock import patch

import start


class StartupModeSelectionTest(unittest.TestCase):
    def test_choose_interaction_mode_defaults_to_web_panel(self):
        calls = []

        def fake_choose(label, items, default=1):
            calls.append((label, items, default))
            return items[0]

        with patch.object(start, "choose", fake_choose):
            mode = start.choose_interaction_mode()

        self.assertEqual(mode, "web")
        label, items, default = calls[0]
        self.assertIn("操作方式", label)
        self.assertEqual(default, 1)
        self.assertIn("Web", items[0])
        self.assertIn("Hermes 命令行", items[1])

    def test_choose_interaction_mode_can_select_hermes_cli(self):
        def fake_choose(label, items, default=1):
            return items[1]

        with patch.object(start, "choose", fake_choose):
            mode = start.choose_interaction_mode()

        self.assertEqual(mode, "cli")


if __name__ == "__main__":
    unittest.main()
