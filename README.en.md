# Hermes Collab Engine v4.5

Multi-Agent Collaboration Engine: A Leader decomposes tasks, Workers execute in parallel, and a dashboard provides real-time visualization.

![Pixel Collab Office Dashboard](docs/screenshots/dashboard.png)

## Quick Start

```bash
# Clone
git clone https://github.com/lpc0387/hermes-collab-engine.git
cd hermes-collab-engine
pip install -e .

# Launch
opc
```

After launching, choose a configuration method → select a model → the dashboard starts automatically.

## Core Concepts

```
User → Leader(AI) → WBS Decomposition → Worker(AI) × N in parallel → Aggregation → Result
```

- **Leader** handles complexity scoring, WBS decomposition, result aggregation, and Skill/Tool distribution
- **Worker** executes individual nodes, loading Skills and tool whitelists on demand
- **Agent Backend** abstracts different coding agents (Claude Code / Codex / OpenCode)
- **SQLite** persists runtime state, node results, context snapshots, and lessons learned
- **Dashboard** provides real-time visualization of the pipeline, Worker pool, and Skill/Tool injection

## What's New in v4.5

| Feature | Description |
|---|---|
| Skill Distribution | The Leader automatically selects skills to inject into Worker prompts based on node capabilities, with a top-3 limit |
| MCP Tool Management | The Leader assigns tool whitelists by node type, including MCP read-only tools, following the principle of least privilege |
| Visualization Dashboard | Pipeline view + Worker pool cards + Skill/Tool badges, dark theme |

## Full Capabilities

| Capability | Description |
|---|---|
| Complexity Assessment | Scores by domain, number of steps, ambiguity, coupling, and risk |
| WBS Decomposition | Automatically breaks tasks into executable work-breakdown nodes |
| Agent Backend | Claude Code / Codex / OpenCode / Custom |
| Skill Distribution | Selects skills to inject into prompts based on node capabilities |
| MCP Tool Management | Tool whitelists + MCP read-only + fallback |
| Parallel Dispatch | Dispatches as soon as dependencies are satisfied, streaming scheduling |
| Timeout Guard + Shard Retry | Timeouts are split into scope/evidence/implementation/risk shards |
| Result Aggregation | Honestly reports successes, failures, and timeouts |
| Dual-Track Output | Machine-parseable JSON + human-readable deliverables |
| Context Snapshots | Automatically saved before compression, supports restoration |
| Self-Learning Lessons | Scoped lessons (global / project / run / node) |
| Parent Intervention | CLI can kill / split / skip running nodes |
| Visualization Dashboard | Pipeline + Worker pool + Skill/Tool badges |
| Environment Variable Models | `HERMES_COLLAB_MODEL` / `ANTHROPIC_MODEL` fallback |

## Configuration Sources

The launcher auto-detects API configuration in the following priority order:

1. **`~/.hermes/.env`** — `ANTHROPIC_API_KEY` + `ANTHROPIC_BASE_URL` (recommended)
2. **`~/.hermes/config.yaml`** — `model.base_url` + `model.default`
3. **`~/.hermes/auth.json`** — Anthropic credentials from the credential pool
4. **`~/.claude/settings.json`** — Claude Code configuration (fallback)
5. **Manual Input** — BaseURL + API Key + model list

Hermes acts as the Leader, so its configuration should be the primary source. Claude Code configuration is only used as a compatibility fallback.

## Model Selection

At startup, you select separately:

- **Leader Model**: complexity assessment, WBS decomposition, result aggregation, Hermes CLI default model
- **Worker Model**: node execution, shard retry

## CLI Commands

### Run a Task

```bash
hermes-collab run "Analyze the current project structure" --cwd . --json
hermes-collab run --request-file request.md --cwd .
hermes-collab run "Implement a collaborative task" --agent claude-code --concurrency 4 --timeout 900
```

### Start the Dashboard

```bash
hermes-collab server --host 0.0.0.0 --port 8765 --cwd .
```

### View Skills / Tools

```bash
hermes-collab skills                                # All skills
hermes-collab skills --node-type implementation      # Preview selected skills
hermes-collab tools                                 # All tool configurations
hermes-collab tools --node-type implementation       # Preview selected tools
```

### View Agents / Status

```bash
hermes-collab agents                # Registered backends
hermes-collab agents --available    # Available on PATH
hermes-collab status --json
```

### Lesson Management

```bash
hermes-collab lessons                       # List lessons
hermes-collab lessons --scope global        # Filter by scope
hermes-collab add-lesson --category timeout --lesson "Split large files" --scope global
```

### Runtime Interventions

```bash
hermes-collab kill-node <run_id> <node_id>  # Kill a node
hermes-collab split-node <run_id> <node_id> # Split a node
hermes-collab skip-node <run_id> <node_id>  # Skip a node
hermes-collab redo-node <run_id> <node_id>  # Redo a node
hermes-collab log <run_id> <node_id> "msg"  # Write a log entry
```

### Verification

```bash
hermes-collab verify-v45    # v4.5 feature completeness check
```

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/overview` | Overview data |
| GET | `/api/runs` | Run records |
| GET | `/api/runs/:id` | Run details (including nodes, workers, logs) |
| GET | `/api/logs` | Recent logs |
| GET | `/api/lessons` | Self-learning lessons |
| GET | `/api/agents` | Available Agent Backends |
| GET | `/api/skills?node_type=&task=` | Skill registry (preview with selection) |
| GET | `/api/tools?node_type=&task=` | Tool configuration (preview with selection) |
| GET | `/api/events` | SSE real-time event stream |
| POST | `/api/runs` | Submit a task asynchronously |

## Persistence

An SQLite file (default: `data/collab.sqlite3`) stores:

- `runs` — Run records (including agent field)
- `wbs_nodes` — Nodes (including skills_json, tools_json)
- `workers` — Executor state
- `logs` — Audit logs
- `lessons` — Lessons learned (including scope)
- `node_results` — Structured results
- `settings` — Engine configuration
- `context_snapshots` — Context snapshots

## Timeout Splitting Strategy

1. Worker timeout → automatically split into scope / evidence / implementation / risk shards
2. Shards execute independently; results are aggregated back to the parent node
3. Proactive splitting: nodes predicted to timeout or be high-risk can be split before execution
4. `redo-node` can redo a completed node; `--cascade` propagates changes downstream

## Agent Backend

| Backend | Command | Output Parsing |
|---|---|---|
| claude-code | `claude -p` | session ID + text |
| codex | `codex` | JSON |
| opencode | `opencode` | text |

Custom Backend: Implement the `AgentBackend` interface (`name`, `build_command`, `parse_output`, `default_allowed_tools`) and register it.

## Integration with Hermes

```bash
# Direct Hermes invocation
hermes-collab run "Task description" --cwd /path/to/project --json

# Launcher mode
opc  # Choose config → choose model → dashboard + Hermes CLI
```

Environment variables:

```bash
HERMES_COLLAB_MODEL=glm-5.1           # Global model
HERMES_COLLAB_LEADER_MODEL=glm-5.1    # Leader model
HERMES_COLLAB_WORKER_MODEL=kimi-k2.6  # Worker model
ANTHROPIC_MODEL=glm-5.1               # Fallback
```

## Security Boundaries

- Workers run in isolated subprocesses, constrained by `allowed_tools` whitelists
- API Keys are stored only in environment variables and `~/.hermes/.env`, never written to the database
- `git push` is restricted by the `git-write` tool profile and only available to implementation nodes
- MCP tools are read-only by default (`mcp-readonly` profile)

## Development

```bash
pip install -e .
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

```
src/hermes_collab_engine/
├── cli.py           # CLI entry point
├── engine.py        # Core engine
├── server.py        # Web dashboard
├── store.py         # SQLite persistence
├── models.py        # Data models
├── skills.py        # Skill distribution
├── tools.py         # MCP tool management
├── agents/          # Agent Backend abstraction
├── verification.py  # v4.5 completeness check
└── ...
web/
└── index.html       # Visualization dashboard
```

## License

MIT
