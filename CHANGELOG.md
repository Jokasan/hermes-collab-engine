# Changelog

All notable public changes to Hermes Collab Engine are documented here.

## v5.0.0 — First formal public release

Hermes Collab Engine v5.0.0 is the first formal public release line for the standalone Hermes collaboration workflow. Earlier v4.5 materials remain useful as internal/pre-release lineage, but v5.0.0 is the baseline intended for public review, installation, sandbox demos, and downstream release notes.

### Added

- WBS-based multi-agent collaboration flow: a Leader scores and decomposes a request, Workers execute dependency-scoped nodes in parallel, and the Leader aggregates results into a final deliverable.
- Real-time dashboard for runs, WBS nodes, Worker state, Skill/Tool injection, active models, logs, and Leader feedback.
- Leader feedback diary in the dashboard with copy/download Markdown actions for aggregate feedback after completion.
- Agent Backend abstraction for Claude Code, Codex, OpenCode, and custom command-backed coding agents.
- Skill registry and Tool profile registry with CLI/API previews for node-specific capability injection.
- SQLite persistence for runs, nodes, workers, logs, lessons, node results, settings, and context snapshots.
- One-line installer that clones or updates the repository, checks dependencies, creates a local virtual environment, and keeps runtime secrets/configuration outside the repository.
- Hermes integration template installer with dry-run review before copying local configuration skeletons.
- Sandbox launcher and sandbox server with mock demo data, TTL cleanup, sub-path deployment support, and optional limited real-worker mode in an isolated database/workspace.
- CLI commands for running tasks, starting the dashboard, inspecting skills/tools/agents/status, managing lessons, intervening in nodes, and running local verification.

### Changed

- Public release framing now treats v5.0.0 as the formal release baseline instead of exposing v4.5 as the primary public version.
- Dashboard run-detail payloads are split between lightweight refresh-friendly responses and full responses for Worker/log/model/Leader-feedback detail.
- Sandbox real execution is explicitly scoped to ignored demo runtime paths and remains separate from production data.

### Security and release boundaries

- The repository does not bundle runtime data, API keys, real Hermes/Claude configuration, tokens, sessions, logs, memories, skills, auth files, or production SQLite files.
- API keys are sourced from local environment/configuration and are not written to the collaboration database.
- Worker execution is constrained by node-specific `allowed_tools` profiles; MCP tooling is read-only by default.
- Sandbox demos default to mock data and an isolated demo database; real-worker sandbox mode writes to `data/sandbox_real.sqlite3` and `data/sandbox_workspace/`.

### Verification

Recommended release checks before publishing artifacts:

```bash
python3 -m py_compile src/hermes_collab_engine/*.py sandbox/server.py scripts/seed_demo_data.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m hermes_collab_engine.cli verify-release
bash -n scripts/install.sh scripts/install-hermes-integration.sh scripts/start_sandbox.sh start.sh
```

### Known limitations

- `verify-v45` remains available as a compatibility alias for the capability set inherited from the v4.5 pre-release line; public release checks should use `verify-release`.
- Package metadata may still be updated by the release-versioning step; confirm `pyproject.toml` and `src/hermes_collab_engine/__init__.py` before building distribution artifacts.
- The sandbox is a demo environment, not a production deployment profile. Keep it on isolated demo data and reviewed mock configuration.
- Real Worker execution requires locally installed/configured agent backends and valid local credentials; the public repository intentionally does not include them.
