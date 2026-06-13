import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def load_sandbox_server():
    path = Path(__file__).resolve().parents[1] / "sandbox" / "server.py"
    spec = importlib.util.spec_from_file_location("sandbox_server_under_test", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeStore:
    def __init__(self):
        self.calls = 0

    def run_detail(self, run_id):
        self.calls += 1
        return {
            "run": {
                "id": run_id,
                "title": "真实运行",
                "status": "running",
                "created_at": "2026-06-12 17:00:00",
            },
            "nodes": [
                {
                    "id": "wbs-1",
                    "title": "真实节点",
                    "description": "",
                    "capability": "analysis",
                    "deliverable": "结果",
                    "status": "running",
                    "result": None,
                    "brief": "",
                    "skills_json": '["search-verify"]',
                    "tools_json": '["mcp-readonly"]',
                }
            ],
            "logs": [
                {
                    "created_at": "2026-06-12 17:00:01",
                    "level": "info",
                    "node_id": "wbs-1",
                    "message": "worker started",
                    "data_json": '{"node":"wbs-1"}',
                }
            ],
        }

    def lessons(self):
        return []


class SandboxRealRefreshTests(unittest.TestCase):
    def test_real_run_refresh_keeps_placeholder_id_as_alias_to_live_wbs(self):
        server = load_sandbox_server()
        server.RUNS[:] = [
            {
                "id": "sandbox-real-pending-001",
                "title": "占位运行",
                "status": "running",
                "created_at": "2026-06-12T17:00:00+00:00",
            }
        ]
        server.RUN_DETAILS.clear()
        server.RUN_DETAILS["sandbox-real-pending-001"] = {
            "id": "sandbox-real-pending-001",
            "title": "占位运行",
            "status": "running",
            "created_at": "2026-06-12T17:00:00+00:00",
            "nodes": [
                {"id": "sandbox-real", "title": "启动隔离真实执行", "status": "running"}
            ],
            "logs": [],
        }

        store = FakeStore()

        server._refresh_from_store(store, "run_real123", alias_run_id="sandbox-real-pending-001")

        self.assertEqual(server.RUNS[0]["id"], "sandbox-real-pending-001")
        self.assertEqual(server.RUNS[0]["real_run_id"], "run_real123")
        self.assertEqual(server.RUNS[0]["status"], "running")
        detail = server.RUN_DETAILS["sandbox-real-pending-001"]
        self.assertEqual(detail["id"], "sandbox-real-pending-001")
        self.assertEqual(detail["real_run_id"], "run_real123")
        self.assertEqual(detail["nodes"][0]["id"], "wbs-1")
        self.assertEqual(detail["nodes"][0]["status"], "running")
        self.assertEqual(detail["logs"][0]["message"], "worker started")
        self.assertEqual(server.RUN_DETAILS["run_real123"]["real_run_id"], "run_real123")

    def test_real_run_refresh_preserves_placeholder_order_on_subsequent_updates(self):
        server = load_sandbox_server()
        server.RUNS[:] = [
            {"id": "older", "title": "旧运行", "status": "completed", "created_at": "2026-06-12 16:00:00"},
            {"id": "sandbox-real-pending-002", "title": "占位运行", "status": "running", "created_at": "2026-06-12T17:00:00+00:00"},
        ]
        server.RUN_DETAILS.clear()

        store = FakeStore()
        server._refresh_from_store(store, "run_real456", alias_run_id="sandbox-real-pending-002")

        ids = [run["id"] for run in server.RUNS]
        self.assertEqual(ids.count("sandbox-real-pending-002"), 1)
        self.assertNotIn("run_real456", ids)
        self.assertIn("run_real456", server.RUN_DETAILS)
        self.assertEqual(server.RUN_DETAILS["sandbox-real-pending-002"]["nodes"][0]["id"], "wbs-1")

    def test_safe_copytree_rejects_existing_unmarked_workspace(self):
        server = load_sandbox_server()
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dst = Path(tmp) / "dst"
            src.mkdir()
            dst.mkdir()

            with self.assertRaises(RuntimeError):
                server._safe_copytree(src, dst)

    def test_shutdown_after_waits_then_stops_server(self):
        server = load_sandbox_server()
        sleeps = []

        class FakeHttpd:
            def __init__(self):
                self.shutdown_called = False

            def shutdown(self):
                self.shutdown_called = True

        original_sleep = server.time.sleep
        server.time.sleep = sleeps.append
        try:
            httpd = FakeHttpd()
            server._shutdown_after(httpd, 7200)
        finally:
            server.time.sleep = original_sleep

        self.assertEqual(sleeps, [7200])
        self.assertTrue(httpd.shutdown_called)
        self.assertEqual(server.DEFAULT_TTL_SECONDS, 7200)


if __name__ == "__main__":
    unittest.main()
