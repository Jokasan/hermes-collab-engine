import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.hermes_collab_engine.engine import CollabEngine
from src.hermes_collab_engine.models import WBSNode


class WorkerPermissionCommandTest(unittest.TestCase):
    def test_worker_claude_command_allows_file_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = CollabEngine(db_path=Path(tmp) / "collab.sqlite3", cwd=tmp)
            node = WBSNode(
                id="wbs-1",
                title="Edit docs",
                description="Modify docs/example.md only.",
                capability="docs",
                complexity=1,
                dependencies=[],
                parallelizable=True,
                deliverable="Updated docs/example.md",
            )

            captured = {}

            def fake_run(cmd, **kwargs):
                captured["cmd"] = cmd
                class Proc:
                    returncode = 0
                    stdout = '{"result":"ok","session_id":"s1","is_error":false}'
                    stderr = ""
                return Proc()

            with patch("subprocess.run", side_effect=fake_run):
                result = engine._run_worker("run_test", node, timeout=30)

            self.assertTrue(result.ok)
            cmd = captured["cmd"]
            self.assertIn("--permission-mode", cmd)
            self.assertIn("acceptEdits", cmd)
            self.assertIn("--allowedTools", cmd)
            allowed = cmd[cmd.index("--allowedTools") + 1]
            self.assertIn("Read", allowed)
            self.assertIn("Edit", allowed)
            self.assertIn("Write", allowed)
            self.assertIn("MultiEdit", allowed)
            self.assertIn("Bash(git diff*)", allowed)
            self.assertIn("Bash(git add*)", allowed)
            self.assertIn("Bash(git commit*)", allowed)
            self.assertIn("Bash(git push*)", allowed)
            self.assertIn("Bash(python3 -m unittest*)", allowed)
            self.assertIn("Bash(python3 -m py_compile*)", allowed)
            self.assertIn("Bash(bash -n*)", allowed)
            self.assertNotIn("--dangerously-skip-permissions", cmd)


if __name__ == "__main__":
    unittest.main()
