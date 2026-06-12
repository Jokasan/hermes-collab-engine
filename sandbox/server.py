#!/usr/bin/env python3
"""Standalone sandbox dashboard server with mock Hermes data."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
INDEX_HTML = ROOT / "index.html"

DATA_SOURCE = "memory"
LESSON_COUNT = 3
SANDBOX_CONFIG: dict = {}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


RUNS: list[dict] = [
    {
        "id": "sandbox-demo-001",
        "title": "沙盒演示：页面克隆与隔离验证",
        "status": "running",
        "created_at": "2026-06-12T09:00:00+00:00",
    },
    {
        "id": "sandbox-demo-000",
        "title": "沙盒演示：历史运行样例",
        "status": "completed",
        "created_at": "2026-06-12T08:30:00+00:00",
    },
]

RUN_DETAILS: dict[str, dict] = {
    "sandbox-demo-001": {
        "id": "sandbox-demo-001",
        "title": "沙盒演示：页面克隆与隔离验证",
        "status": "running",
        "created_at": "2026-06-12T09:00:00+00:00",
        "nodes": [
            {
                "id": "wbs-sandbox-1",
                "title": "分析现有页面结构",
                "capability": "analysis",
                "status": "completed",
                "deliverable": "页面结构说明",
                "brief": "读取生产页面，仅复制演示需要的最小集合。",
                "skills": ["debug-root-cause"],
                "tools": ["file-edit"],
                "result": "识别 dashboard HTML、API 列表、运行详情和 SSE 更新链路。",
            },
            {
                "id": "wbs-sandbox-2",
                "title": "复制前端到沙盒目录",
                "capability": "implementation",
                "status": "completed",
                "deliverable": "sandbox/index.html",
                "brief": "保留页面视觉效果，替换品牌文案为沙盒演示。",
                "skills": ["implementation-focus"],
                "tools": ["file-edit"],
                "result": "沙盒页面使用本地 mock API，不读取生产数据库。",
            },
            {
                "id": "wbs-sandbox-3",
                "title": "连接 Mock 后端入口",
                "capability": "implementation",
                "status": "running",
                "deliverable": "sandbox/server.py",
                "brief": "提供演示所需的最小 API：overview、runs、skills、tools、events。",
                "skills": ["implementation-focus", "test-verify"],
                "tools": ["python-tests"],
                "result": "POST /api/runs 仅创建内存演示记录，不启动 worker。",
            },
            {
                "id": "wbs-sandbox-4",
                "title": "验证本地构建运行",
                "capability": "verification",
                "status": "planning",
                "deliverable": "本地检查结果",
                "brief": "执行语法检查并说明启动方式。",
                "skills": ["test-verify"],
                "tools": ["python-tests"],
            },
        ],
        "logs": [
            {"timestamp": "2026-06-12T09:00:01+00:00", "level": "info", "node_id": "wbs-sandbox-1", "message": "sandbox analysis started", "data": {"source": "mock"}},
            {"timestamp": "2026-06-12T09:01:12+00:00", "level": "info", "node_id": "wbs-sandbox-2", "message": "frontend cloned into isolated directory", "data": {"path": "sandbox/index.html"}},
            {"timestamp": "2026-06-12T09:02:20+00:00", "level": "warning", "node_id": "wbs-sandbox-3", "message": "production task execution disabled in sandbox", "data": {"post_runs": "mock-only"}},
            {"timestamp": "2026-06-12T09:03:05+00:00", "level": "info", "node_id": "wbs-sandbox-3", "message": "worker skills selected", "data": {"skills": ["implementation-focus", "test-verify"]}},
            {"timestamp": "2026-06-12T09:03:06+00:00", "level": "info", "node_id": "wbs-sandbox-3", "message": "worker tool profiles selected", "data": {"profiles": ["file-edit", "python-tests"]}},
        ],
    },
    "sandbox-demo-000": {
        "id": "sandbox-demo-000",
        "title": "沙盒演示：历史运行样例",
        "status": "completed",
        "created_at": "2026-06-12T08:30:00+00:00",
        "nodes": [
            {"id": "wbs-history-1", "title": "准备演示数据", "capability": "implementation", "status": "completed", "deliverable": "Mock 数据", "skills": ["implementation-focus"], "tools": ["file-edit"]},
            {"id": "wbs-history-2", "title": "检查隔离策略", "capability": "verification", "status": "completed", "deliverable": "隔离检查", "skills": ["test-verify"], "tools": ["python-tests"]},
        ],
        "logs": [
            {"timestamp": "2026-06-12T08:30:00+00:00", "level": "info", "node_id": "wbs-history-1", "message": "demo data loaded", "data": {"source": "mock"}},
            {"timestamp": "2026-06-12T08:31:00+00:00", "level": "info", "node_id": "wbs-history-2", "message": "sandbox isolation verified", "data": {"db": "not used"}},
        ],
    },
}

SKILLS = [
    {"name": "implementation-focus", "display_name": "Focused Implementation", "priority": 100, "description": "Make the smallest useful code change for the sandbox demo."},
    {"name": "test-verify", "display_name": "Test & Verification", "priority": 90, "description": "Run narrow checks and report exact results."},
    {"name": "debug-root-cause", "display_name": "Debug Root Cause", "priority": 70, "description": "Inspect the failing path before changing code."},
]

TOOLS = [
    {"name": "file-edit", "display_name": "File Read/Edit", "priority": 100, "description": "Read and edit repository files for sandbox implementation.", "allowed_tools": ["Read", "Edit", "Write"]},
    {"name": "python-tests", "display_name": "Python Test Runner", "priority": 90, "description": "Run local Python syntax checks for sandbox entrypoints.", "allowed_tools": ["python3 -m py_compile"]},
]


def normalize_base_path(value: str | None) -> str:
    if not value or value == "/":
        return ""
    return "/" + value.strip("/")


def public_url(host: str, port: int, base_path: str, configured: str | None) -> str:
    if configured:
        return configured.rstrip("/") + (base_path or "/")
    return f"http://{host}:{port}{base_path or '/'}"


def _loads(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def load_db_snapshot(db_path: Path) -> bool:
    global DATA_SOURCE, LESSON_COUNT
    if not db_path.exists():
        return False

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        runs = [dict(row) for row in conn.execute("SELECT id,title,status,created_at FROM runs ORDER BY created_at DESC").fetchall()]
        details: dict[str, dict] = {}
        for run in runs:
            nodes = []
            for row in conn.execute(
                """SELECT id,title,description,capability,deliverable,status,result,brief,skills_json,tools_json
                FROM wbs_nodes WHERE run_id=? ORDER BY created_at,id""",
                (run["id"],),
            ).fetchall():
                node = dict(row)
                node["skills"] = _loads(node.pop("skills_json", None), [])
                node["tools"] = _loads(node.pop("tools_json", None), [])
                nodes.append(node)
            logs = []
            for row in conn.execute(
                "SELECT created_at AS timestamp,level,node_id,message,data_json FROM logs WHERE run_id=? ORDER BY created_at,id",
                (run["id"],),
            ).fetchall():
                log = dict(row)
                log["data"] = _loads(log.pop("data_json", None), {})
                logs.append(log)
            details[run["id"]] = {**run, "nodes": nodes, "logs": logs}

        if not runs:
            return False
        RUNS[:] = runs
        RUN_DETAILS.clear()
        RUN_DETAILS.update(details)
        LESSON_COUNT = conn.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
        DATA_SOURCE = f"sqlite:{db_path}"
        return True
    finally:
        conn.close()


def load_mock_config(path: Path | None) -> dict:
    if not path or not path.exists():
        return {"services": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    services = []
    for service in data.get("services", []):
        services.append({"name": service.get("name"), "kind": service.get("kind"), "base_url": service.get("base_url")})
    return {"path": str(path), "services": services, "egress_policy": data.get("egress_policy", {})}


def overview() -> dict:
    running = sum(1 for run in RUNS if run["status"] == "running")
    latest_nodes = RUN_DETAILS.get(RUNS[0]["id"], {}).get("nodes", []) if RUNS else []
    workers = sum(1 for node in latest_nodes if node.get("status") == "running")
    return {"runs": len(RUNS), "running": running, "workers_running": workers, "lessons": LESSON_COUNT, "sandbox": True, "data_source": DATA_SOURCE}


def add_demo_run(request: str) -> dict:
    run_id = f"sandbox-demo-{len(RUNS) + 1:03d}"
    created = now_iso()
    run = {"id": run_id, "title": request[:80], "status": "running", "created_at": created}
    detail = {
        **run,
        "nodes": [
            {"id": f"{run_id}-1", "title": "接收沙盒任务", "capability": "implementation", "status": "completed", "deliverable": "内存演示记录", "brief": request, "skills": ["implementation-focus"], "tools": ["file-edit"]},
            {"id": f"{run_id}-2", "title": "模拟协同执行", "capability": "verification", "status": "running", "deliverable": "Mock 运行状态", "brief": "沙盒不会启动真实 worker。", "skills": ["test-verify"], "tools": ["python-tests"]},
            {"id": f"{run_id}-3", "title": "输出演示结果", "capability": "verification", "status": "planning", "deliverable": "演示页面更新", "brief": "用于展示页面交互，不写入生产数据。", "skills": ["test-verify"], "tools": ["python-tests"]},
        ],
        "logs": [
            {"timestamp": created, "level": "info", "node_id": f"{run_id}-1", "message": "sandbox run accepted", "data": {"mock_only": True}},
            {"timestamp": created, "level": "warning", "node_id": f"{run_id}-2", "message": "real worker execution is disabled", "data": {"isolation": "sandbox"}},
        ],
    }
    RUNS.insert(0, run)
    RUN_DETAILS[run_id] = detail
    return {"accepted": True, "run_id": run_id, "sandbox": True}


class SandboxHandler(BaseHTTPRequestHandler):
    server: ThreadingHTTPServer

    def _json(self, data, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _path_under_base(self, raw_path: str) -> str | None:
        base_path = self.server.sandbox_base_path  # type: ignore[attr-defined]
        if not base_path:
            return raw_path
        if raw_path == base_path:
            return "/"
        if raw_path.startswith(base_path + "/"):
            return raw_path[len(base_path):]
        return None

    def _redirect(self, location: str) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def _index(self) -> None:
        config = {"apiBase": self.server.sandbox_base_path, **SANDBOX_CONFIG}  # type: ignore[attr-defined]
        marker = "</head>"
        html = INDEX_HTML.read_text(encoding="utf-8")
        inject = f"<script>window.__HERMES_SANDBOX_CONFIG__={json.dumps(config, ensure_ascii=False)};</script>\n"
        body = html.replace(marker, inject + marker, 1).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        raw_path = urlparse(self.path).path
        if raw_path == "/" and self.server.sandbox_base_path:  # type: ignore[attr-defined]
            return self._redirect(self.server.sandbox_base_path + "/")  # type: ignore[attr-defined]
        path = self._path_under_base(raw_path)
        if path is None:
            return self._json({"error": "not found", "sandbox_base_path": self.server.sandbox_base_path}, 404)  # type: ignore[attr-defined]
        if path in {"/", "/index.html"}:
            self._index()
        elif path == "/api/overview":
            self._json(overview())
        elif path == "/api/runs":
            self._json(RUNS)
        elif path.startswith("/api/runs/"):
            run_id = path.rsplit("/", 1)[-1]
            self._json(RUN_DETAILS.get(run_id, {"error": "not found"}), 200 if run_id in RUN_DETAILS else 404)
        elif path == "/api/logs":
            self._json(RUN_DETAILS[RUNS[0]["id"]]["logs"] if RUNS else [])
        elif path == "/api/skills":
            self._json(SKILLS)
        elif path == "/api/tools":
            self._json(TOOLS)
        elif path == "/api/sandbox/config":
            self._json(SANDBOX_CONFIG)
        elif path == "/api/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                while True:
                    latest_logs = RUN_DETAILS[RUNS[0]["id"]]["logs"][-10:] if RUNS else []
                    payload = json.dumps({"type": "sandbox", "overview": overview(), "logs": latest_logs}, ensure_ascii=False)
                    self.wfile.write(f"data: {payload}\n\n".encode())
                    self.wfile.flush()
                    time.sleep(2)
            except Exception:
                pass
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        raw_path = urlparse(self.path).path
        path = self._path_under_base(raw_path)
        if path is None:
            return self._json({"error": "not found", "sandbox_base_path": self.server.sandbox_base_path}, 404)  # type: ignore[attr-defined]
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode() if length else "{}"
        try:
            data = json.loads(body)
        except Exception:
            return self._json({"error": "invalid json"}, 400)
        if path == "/api/runs":
            request = str(data.get("request") or "").strip()
            if not request:
                return self._json({"error": "request is required"}, 400)
            return self._json(add_demo_run(request), 201)
        self._json({"error": "not found"}, 404)

    def log_message(self, fmt, *args) -> None:
        return


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def main() -> int:
    global SANDBOX_CONFIG
    parser = argparse.ArgumentParser(description="Run the Hermes sandbox dashboard with mock data")
    parser.add_argument("--host", default=os.environ.get("HERMES_SANDBOX_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=env_int("HERMES_SANDBOX_PORT", 8876))
    parser.add_argument("--base-path", default=os.environ.get("HERMES_SANDBOX_BASE_PATH", "/"))
    parser.add_argument("--public-url", default=os.environ.get("HERMES_SANDBOX_PUBLIC_URL"))
    parser.add_argument("--db", default=os.environ.get("HERMES_SANDBOX_DB", ""))
    parser.add_argument("--mock-config", default=os.environ.get("HERMES_SANDBOX_MOCK_CONFIG", str(REPO_ROOT / "config" / "sandbox-mocks.json")))
    args = parser.parse_args()

    base_path = normalize_base_path(args.base_path)
    db_path = Path(args.db).expanduser().resolve() if args.db else None
    if db_path:
        load_db_snapshot(db_path)
    mock_config = load_mock_config(Path(args.mock_config).expanduser().resolve() if args.mock_config else None)
    SANDBOX_CONFIG = {
        "mode": "sandbox-demo",
        "publicUrl": public_url(args.host, args.port, base_path, args.public_url),
        "basePath": base_path or "/",
        "database": {"path": str(db_path) if db_path else None, "source": DATA_SOURCE, "readOnly": True},
        "mockConfig": mock_config,
        "productionExecution": "disabled",
    }

    httpd = ThreadingHTTPServer((args.host, args.port), SandboxHandler)
    httpd.sandbox_base_path = base_path  # type: ignore[attr-defined]
    httpd.sandbox_config = SANDBOX_CONFIG  # type: ignore[attr-defined]
    print(f"Hermes sandbox dashboard: {SANDBOX_CONFIG['publicUrl']}")
    print(f"Hermes sandbox API: {base_path}/api/sandbox/config" if base_path else "Hermes sandbox API: /api/sandbox/config")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
