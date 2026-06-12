#!/usr/bin/env bash
# 一键启动 Hermes 协同引擎沙盒演示
#
# 默认运行 2 小时，超时自动停止；用户可指定运行小时数。
#
# 用法：
#   ./scripts/start_sandbox.sh              # 默认 2 小时
#   ./scripts/start_sandbox.sh 4            # 运行 4 小时
#   ./scripts/start_sandbox.sh 0.5          # 运行 30 分钟
#   ./scripts/start_sandbox.sh --hours 8    # 8 小时
#   ./scripts/start_sandbox.sh --port 8877  # 自定义端口
#   HOURS=3 ./scripts/start_sandbox.sh      # 环境变量

set -euo pipefail

# ---------- 配置默认值 ----------
DEFAULT_HOURS="${HOURS:-2}"
HOURS="$DEFAULT_HOURS"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8876}"
DB="${DB:-data/demo_sandbox.sqlite3}"
RESEED="${RESEED:-1}"  # 1=每次启动重置数据；0=保留

# ---------- 解析参数 ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      sed -n '2,12p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    --hours)   HOURS="$2"; shift 2 ;;
    --host)    HOST="$2";  shift 2 ;;
    --port)    PORT="$2";  shift 2 ;;
    --db)      DB="$2";    shift 2 ;;
    --no-reseed) RESEED=0; shift ;;
    --interactive|-i)
      # 交互式询问运行时长
      read -rp "运行多少小时？ [默认 ${DEFAULT_HOURS}]: " __h
      [[ -n "$__h" ]] && HOURS="$__h"
      shift
      ;;
    [0-9]*)    HOURS="$1"; shift ;;  # 第一个数字参数当作小时数
    *) echo "未知参数：$1" >&2; exit 2 ;;
  esac
done

# ---------- 路径定位 ----------
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." &>/dev/null && pwd)"
cd "$REPO_ROOT"

# ---------- 校验 ----------
if [[ ! -f sandbox/server.py ]]; then
  echo "✗ 找不到 sandbox/server.py（当前目录：$REPO_ROOT）" >&2
  exit 1
fi
if [[ ! -f scripts/seed_demo_data.py ]]; then
  echo "✗ 找不到 scripts/seed_demo_data.py" >&2
  exit 1
fi
if ! command -v python3 &>/dev/null; then
  echo "✗ 未找到 python3" >&2; exit 1
fi

# 小时数转秒（支持小数）
SECS="$(python3 -c "h=float('$HOURS'); print(int(h*3600)) if h>0 else 0" 2>/dev/null || echo 0)"
if [[ "$SECS" -le 0 ]]; then
  echo "✗ 无效的运行小时数：$HOURS（必须 > 0）" >&2; exit 2
fi
if [[ "$SECS" -gt 86400 ]]; then
  echo "⚠ 运行时长超过 24 小时（${HOURS}h），如确认请用环境变量 HERMES_SANDBOX_FORCE=1 跳过该提醒"
  if [[ "${HERMES_SANDBOX_FORCE:-0}" != "1" ]]; then exit 2; fi
fi

# ---------- 端口占用检查 ----------
if command -v lsof &>/dev/null && lsof -iTCP:"$PORT" -sTCP:LISTEN &>/dev/null; then
  echo "✗ 端口 $PORT 已被占用，请用 --port 指定其它端口" >&2
  lsof -iTCP:"$PORT" -sTCP:LISTEN | head -3 >&2
  exit 3
fi

# ---------- 准备数据 ----------
mkdir -p data logs
if [[ "$RESEED" == "1" ]]; then
  echo "▶ 重置脱敏演示数据 → $DB"
  python3 scripts/seed_demo_data.py --db "$DB" --reset
else
  echo "▶ 复用现有数据库 $DB（--no-reseed）"
  if [[ ! -f "$DB" ]]; then
    echo "  ⚠ 数据库不存在，自动播种一次"
    python3 scripts/seed_demo_data.py --db "$DB" --reset
  fi
fi

# ---------- 启动 ----------
LOG_FILE="logs/sandbox-$(date +%Y%m%d-%H%M%S).log"
echo
echo "▶ 启动 Hermes 协同引擎沙盒"
echo "  地址：http://${HOST}:${PORT}/"
echo "  数据：${DB}（脱敏）"
echo "  日志：${LOG_FILE}"
echo "  运行时长：${HOURS} 小时（${SECS} 秒）"
echo "  Ctrl+C 可随时手动停止"
echo

export HERMES_SANDBOX_DB="$DB"
export HERMES_SANDBOX_MOCK_CONFIG="${HERMES_SANDBOX_MOCK_CONFIG:-config/sandbox-mocks.json}"

# 后台启动 server，捕获 PID
python3 sandbox/server.py --host "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 &
SERVER_PID=$!

cleanup() {
  echo
  echo "▶ 正在停止沙盒（PID=$SERVER_PID）..."
  if kill -0 "$SERVER_PID" 2>/dev/null; then
    kill -TERM "$SERVER_PID" 2>/dev/null || true
    for _ in 1 2 3 4 5; do
      if ! kill -0 "$SERVER_PID" 2>/dev/null; then break; fi
      sleep 1
    done
    kill -KILL "$SERVER_PID" 2>/dev/null || true
  fi
  echo "✓ 沙盒已停止。日志：$LOG_FILE"
}
trap cleanup INT TERM EXIT

# 等待 server 就绪（最多 8 秒）
for i in 1 2 3 4 5 6 7 8; do
  sleep 1
  if curl -sf "http://${HOST}:${PORT}/" -o /dev/null 2>/dev/null; then
    echo "✓ 沙盒已就绪 (${i}s)"
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "✗ 沙盒进程已退出，请检查日志：$LOG_FILE" >&2
    tail -20 "$LOG_FILE" >&2
    exit 1
  fi
  if [[ $i -eq 8 ]]; then
    echo "⚠ 8 秒内未就绪，但进程仍在运行；将继续等待倒计时" >&2
  fi
done

# ---------- 倒计时（分钟级心跳）----------
END_TS=$(( $(date +%s) + SECS ))
HEART_INTERVAL=300  # 每 5 分钟打一次心跳
NEXT_HEART=$(( $(date +%s) + HEART_INTERVAL ))

while true; do
  NOW=$(date +%s)
  if [[ $NOW -ge $END_TS ]]; then
    echo
    echo "▶ 已达预定运行时长（${HOURS}h），自动停止"
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo
    echo "✗ 沙盒进程意外退出，最后日志："
    tail -10 "$LOG_FILE"
    exit 1
  fi
  if [[ $NOW -ge $NEXT_HEART ]]; then
    REMAIN=$(( END_TS - NOW ))
    printf '  · 心跳 %s · 剩余 %d 分钟 · http://%s:%s/\n' \
      "$(date +%H:%M:%S)" "$((REMAIN/60))" "$HOST" "$PORT"
    NEXT_HEART=$(( NOW + HEART_INTERVAL ))
  fi
  sleep 5
done
