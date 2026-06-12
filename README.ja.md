# Hermes Collab Engine v4.5

マルチエージェント協調エンジン：Leader がタスクを分解し、Worker が並列実行、ダッシュボードでリアルタイム可視化。

![ピクセル協調オフィス ダッシュボード](docs/screenshots/dashboard.png)

## クイックスタート

```bash
# クローン
git clone https://github.com/lpc0387/hermes-collab-engine.git
cd hermes-collab-engine
pip install -e .

# 起動
opc
```

起動後に設定方式を選択 → モデルを選択 → ダッシュボードが自動的に起動します。

## サンドボックスデモ

リポジトリには本番環境と完全に隔離されたサンドボックスが同梱されています。匿名化済み SQLite + モック API を使用し、**真の Worker を起動せず、本番データに書き込みもしない** ため、ローカルやデモ機での画面紹介に最適です。

```bash
# ワンコマンド起動（デフォルト 2 時間でタイムアウト停止）
./scripts/start_sandbox.sh

# 実行時間をカスタマイズ
./scripts/start_sandbox.sh 4              # 4 時間
./scripts/start_sandbox.sh 0.5            # 30 分
./scripts/start_sandbox.sh --hours 8      # 8 時間
./scripts/start_sandbox.sh --port 8877    # ポート変更
./scripts/start_sandbox.sh -i             # 対話的に時間を尋ねる

# 既存 DB を流用しシード再生成をスキップ
./scripts/start_sandbox.sh --no-reseed
```

起動後アクセス：`http://127.0.0.1:8876/`

詳細：[`sandbox/README.md`](sandbox/README.md)

## Leader 総括ダイアリー

タスクが終了（completed/failed）すると、ダッシュボードは **ピクセル絵本風のダイアリー** をポップアップ表示し、Leader の最終集約フィードバックを全文プリントします：

- 完了時に自動表示（同一セッション内では重複表示しない）
- 履歴テーブル内の 📓 ボタンで任意の run の総括を再表示可能
- 内蔵スクロールバーにより長文レポートでも完全閲覧可能
- ワンクリックでコピー / Markdown ダウンロード
- ESC または背景クリックで閉じる

## コアコンセプト

```
ユーザー → Leader(AI) → WBS 分解 → Worker(AI) × N 並列 → 集約 → 結果
```

- **Leader** は複雑度スコアリング、WBS 分解、結果集約、Skill/Tool 配信を担当
- **Worker** は個別ノードを実行し、必要に応じて Skill とツールホワイトリストを読み込む
- **Agent Backend** は異なるコーディングエージェント（Claude Code / Codex / OpenCode）を抽象化
- **SQLite** は実行状態、ノード結果、コンテキストスナップショット、経験を永続化
- **ダッシュボード** はパイプライン、Worker プール、Skill/Tool 注入をリアルタイム可視化

## v4.5 の新機能

| 機能 | 説明 |
|---|---|
| Skill 配信 | Leader がノードの能力に応じて自動的にスキルを選択し Worker のプロンプトに注入、top-3 制限あり |
| MCP ツール管理 | Leader がノードタイプごとにツールホワイトリストを割り当て、MCP 読み取り専用ツールを含む、最小権限 |
| 可視化ダッシュボード | パイプラインビュー + Worker プールカード + Skill/Tool バッジ、ダークテーマ |

## 全機能一覧

| 機能 | 説明 |
|---|---|
| 複雑度判定 | ドメイン、ステップ数、曖昧さ、結合度、リスクに基づきスコアリング |
| WBS 分解 | 実行可能な作業分解ノードに自動分割 |
| Agent Backend | Claude Code / Codex / OpenCode / カスタム |
| Skill 配信 | ノードの能力に応じてスキルを選択しプロンプトに注入 |
| MCP ツール管理 | ツールホワイトリスト + MCP 読み取り専用 + フォールバック |
| 並列ディスパッチ | 依存関係が満たされ次第即座に割り当て、ストリーミングスケジューリング |
| タイムアウト監視 + シャードリトライ | タイムアウト時は scope / evidence / implementation / risk のシャードに分割 |
| 結果集約 | 成功・失敗・タイムアウトを正直に報告 |
| デュアルトラック出力 | 機械可読 JSON + 人間可読な成果物 |
| コンテキストスナップショット | 圧縮前に自動保存、リストア対応 |
| 自学習経験 | スコープ付きの lessons（global / project / run / node） |
| 親プロセス介入 | CLI から実行中ノードの kill / split / skip が可能 |
| 可視化ダッシュボード | Pipeline + Worker プール + Skill/Tool バッジ |
| 環境変数モデル | `HERMES_COLLAB_MODEL` / `ANTHROPIC_MODEL` フォールバック |

## 設定ソース

ランチャーは以下の優先度で API 設定を自動検出します：

1. **`~/.hermes/.env`** — `ANTHROPIC_API_KEY` + `ANTHROPIC_BASE_URL`（推奨）
2. **`~/.hermes/config.yaml`** — `model.base_url` + `model.default`
3. **`~/.hermes/auth.json`** — credential pool 内の anthropic 認証情報
4. **`~/.claude/settings.json`** — Claude Code 設定（フォールバック）
5. **手動入力** — BaseURL + API Key + モデル一覧

Hermes が Leader であり、その設定を主ソースとすべきです。Claude Code 設定は互換性のためのフォールバックに過ぎません。

## モデル選択

起動時にそれぞれ選択します：

- **Leader モデル**：複雑度判定、WBS 分解、結果集約、Hermes CLI のデフォルトモデル
- **Worker モデル**：ノード実行、シャードリトライ

## CLI コマンド

### タスク実行

```bash
hermes-collab run "現在のプロジェクト構造を分析" --cwd . --json
hermes-collab run --request-file request.md --cwd .
hermes-collab run "協調タスクを実装" --agent claude-code --concurrency 4 --timeout 900
```

### ダッシュボード起動

```bash
hermes-collab server --host 0.0.0.0 --port 8765 --cwd .
```

### Skill / Tool 確認

```bash
hermes-collab skills                                # 全スキル一覧
hermes-collab skills --node-type implementation      # 選択されたスキルをプレビュー
hermes-collab tools                                 # 全ツール設定
hermes-collab tools --node-type implementation       # 選択されたツールをプレビュー
```

### Agent / ステータス確認

```bash
hermes-collab agents                # 登録済みバックエンド
hermes-collab agents --available    # PATH 上で利用可能なもの
hermes-collab status --json
```

### 経験管理

```bash
hermes-collab lessons                       # 経験一覧
hermes-collab lessons --scope global        # スコープで絞り込み
hermes-collab add-lesson --category timeout --lesson "大きなファイルは分割する" --scope global
```

### 実行中の介入

```bash
hermes-collab kill-node <run_id> <node_id>  # ノードを終了
hermes-collab split-node <run_id> <node_id> # ノードを分割
hermes-collab skip-node <run_id> <node_id>  # ノードをスキップ
hermes-collab redo-node <run_id> <node_id>  # ノードを再実行
hermes-collab log <run_id> <node_id> "msg"  # ログに書き込み
```

### 検証

```bash
hermes-collab verify-v45    # v4.5 機能の完全性チェック
```

## API

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/overview` | 概要データ |
| GET | `/api/runs` | 実行履歴 |
| GET | `/api/runs/:id` | 実行詳細（ノード、Worker、ログを含む） |
| GET | `/api/logs` | 直近のログ |
| GET | `/api/lessons` | 自学習経験 |
| GET | `/api/agents` | 利用可能な Agent Backend |
| GET | `/api/skills?node_type=&task=` | Skill レジストリ（選択プレビュー可能） |
| GET | `/api/tools?node_type=&task=` | Tool 設定（選択プレビュー可能） |
| GET | `/api/events` | SSE リアルタイムイベントストリーム |
| POST | `/api/runs` | 非同期タスク送信 |

## 永続化

SQLite ファイル（デフォルト `data/collab.sqlite3`）に以下を保存：

- `runs` — 実行履歴（agent フィールド含む）
- `wbs_nodes` — ノード（skills_json, tools_json 含む）
- `workers` — 実行器の状態
- `logs` — 監査ログ
- `lessons` — 経験（scope 含む）
- `node_results` — 構造化された結果
- `settings` — エンジン設定
- `context_snapshots` — コンテキストスナップショット

## タイムアウト分割戦略

1. Worker がタイムアウト → 自動的に scope / evidence / implementation / risk のシャードに分割
2. 各シャードは独立して実行され、結果は親ノードに集約される
3. 能動的分割：タイムアウトや高リスクが予想されるノードは実行前に分割可能
4. `redo-node` で完了済みノードを再実行、`--cascade` で下流にも伝播

## Agent Backend

| バックエンド | コマンド | 出力パース |
|---|---|---|
| claude-code | `claude -p` | session ID + text |
| codex | `codex` | JSON |
| opencode | `opencode` | text |

カスタムバックエンド：`AgentBackend` インターフェース（`name`, `build_command`, `parse_output`, `default_allowed_tools`）を実装して登録。

## Hermes との統合

```bash
# Hermes から直接呼び出し
hermes-collab run "タスクの説明" --cwd /path/to/project --json

# ランチャーモード
opc  # 設定を選択 → モデルを選択 → ダッシュボード + Hermes CLI
```

環境変数：

```bash
HERMES_COLLAB_MODEL=glm-5.1           # グローバルモデル
HERMES_COLLAB_LEADER_MODEL=glm-5.1    # Leader モデル
HERMES_COLLAB_WORKER_MODEL=kimi-k2.6  # Worker モデル
ANTHROPIC_MODEL=glm-5.1               # フォールバック
```

## セキュリティ境界

- Worker は独立したサブプロセスで実行され、`allowed_tools` ホワイトリストにより制約される
- API Key は環境変数と `~/.hermes/.env` にのみ保存され、データベースには書き込まれない
- `git push` は `git-write` ツールプロファイルにより制限され、implementation ノードでのみ利用可能
- MCP ツールはデフォルトで読み取り専用（`mcp-readonly` プロファイル）

## 開発

```bash
pip install -e .
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

```
src/hermes_collab_engine/
├── cli.py           # CLI エントリポイント
├── engine.py        # コアエンジン
├── server.py        # Web ダッシュボード
├── store.py         # SQLite 永続化
├── models.py        # データモデル
├── skills.py        # Skill 配信
├── tools.py         # MCP ツール管理
├── agents/          # Agent Backend 抽象化
├── verification.py  # v4.5 完全性チェック
└── ...
web/
└── index.html       # 可視化ダッシュボード
```

## ライセンス

MIT
