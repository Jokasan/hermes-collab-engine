# Hermes 协同引擎沙盒演示环境 — 最终交付报告

> 请求："能不能把这个页面复制然后连接到一个沙盒环境，方便作为演示。"
>
> **结论：已完成，可演示；上线公网前有 2 项阻断需处理。**

---

## 1. 已交付内容

页面已被克隆到独立沙盒目录，与生产代码、生产数据、生产 worker 完全隔离，可立即用于本地/内网演示。

| 类别 | 路径 | 说明 |
|---|---|---|
| 沙盒页面 | `/root/hermes-collab-engine/sandbox/index.html` | 由 `web/index.html` 克隆，加沙盒横幅与隔离提示 |
| 沙盒后端 | `/root/hermes-collab-engine/sandbox/server.py` | 独立 HTTP 服务，提供 Mock API + 只读 SQLite 演示数据 |
| 使用说明 | `/root/hermes-collab-engine/sandbox/README.md` | 启动命令、反向代理示例、隔离说明 |
| 演示数据脚本 | `/root/hermes-collab-engine/scripts/seed_demo_data.py` | 生成脱敏 SQLite，覆盖 runs/nodes/workers/logs/lessons |
| Mock 服务配置 | `/root/hermes-collab-engine/config/sandbox-mocks.json` | localhost-only，默认拒绝外连 |

> 临时验证脚本（非交付物）：`/tmp/hermes_sandbox_verify.py`、`/tmp/hermes_isolation_check.py`、`/tmp/hermes_sensitive_scan.py`。

---

## 2. 启动方式

```bash
cd /root/hermes-collab-engine

# 1) 生成脱敏演示数据库
python3 scripts/seed_demo_data.py --db data/demo_sandbox.sqlite3 --reset

# 2) 启动沙盒服务（默认绑定 127.0.0.1）
HERMES_SANDBOX_DB=data/demo_sandbox.sqlite3 \
HERMES_SANDBOX_BASE_PATH=/sandbox/hermes \
HERMES_SANDBOX_PUBLIC_URL=https://demo.example.com/sandbox/hermes \
HERMES_SANDBOX_MOCK_CONFIG=config/sandbox-mocks.json \
python3 sandbox/server.py --host 127.0.0.1 --port 8876
```

访问 URL：
- 本地：`http://127.0.0.1:8876/sandbox/hermes/`
- 公开（经反代）：`https://<your-domain>/sandbox/hermes/`

反向代理示例已写入 `sandbox/README.md`。

---

## 3. 隔离边界（已验证）

- ✅ **不写生产**：沙盒 SQLite 以只读 URI 打开；POST `/api/runs` 仅写入服务进程内存；通过哨兵库验证生产 DB POST 前后字节未变。
- ✅ **不调真实 worker**：沙盒 server 不导入 `CollabEngine`；`productionExecution: disabled`。
- ✅ **不外联生产**：服务端无 HTTP 客户端调用；Mock 服务全部 `127.0.0.1`/`localhost`，默认拒绝 egress。
- ✅ **演示数据脱敏**：种子数据无真实凭据/客户信息，token 均为 `demo-*` fixture。

---

## 4. 演示路径验证结果

| 用例 | 结果 |
|---|---|
| 页面 HTML 在 `/sandbox/hermes/` 加载 | ✅ |
| 子路径 API base 注入正确 | ✅ |
| `/api/overview` `/api/runs` `/api/runs/:id` `/api/skills` `/api/tools` | ✅ |
| `POST /api/runs` 提交 → 列表/详情正确刷新 | ✅ |
| SSE `/api/events` 首帧返回 | ✅ |
| 异常输入（空 request、路径穿越） | ✅ 返回 400/404 |
| 浏览器像素渲染与点击截图 | ⚠️ **阻塞** — 当前环境无 Chromium/Playwright/Selenium |

---

## 5. 上线前阻断风险（必须处理 2 项）

1. **🔴 前端外部字体外联**：`sandbox/index.html:7-9` 加载 Google Fonts。若要求"沙盒无公网外联"，请改本地字体或删除外链。
2. **🔴 公开 API 无鉴权/限流**：`POST /api/runs` 虽不落库，但可被滥用刷内存与 SSE 连接。**公网暴露前必须由反向代理加 SSO/Basic Auth/IP allowlist + 限流**。

中低风险（建议处理）：
- `--db` 可被误指向生产库 → 启动时校验路径或 sandbox 标记。
- `/api/sandbox/config` 暴露本地 DB 绝对路径 → 公网展示时脱敏为逻辑名。

---

## 6. WBS 分片覆盖与诚实说明

8 个 WBS 节点全部 `returncode=0` 完成，无超时、无重试。其中：

| 节点 | 状态 | 说明 |
|---|---|---|
| wbs-1 分析依赖 | ok | 只读分析 |
| wbs-2 设计架构 | ok | 只读规划 |
| wbs-3 演示数据 + Mock | ok | 新增 2 个文件 |
| wbs-4 克隆页面 | ok | 新增 sandbox/ 3 文件 |
| wbs-5 部署接入 | ok | 子路径 + 只读 DB 接入 |
| wbs-6 功能验证 | **blocked** | 后端路径全通过；浏览器截图证据缺失（环境无浏览器） |
| wbs-7 安全检查 | **blocked** | 数据/服务端隔离通过；Google Fonts 外链 + 公开 API 无鉴权未解决 |
| wbs-8 演示文档 | ok | 仅产出 Markdown，未落盘 |

未覆盖项（透明披露）：
- 未在带浏览器的环境对页面做端到端 UI 渲染/点击/筛选验证。
- 未实现服务端鉴权层；当前依赖反向代理补齐。
- 未自动化生成沙盒 systemd unit、CI 流水线，README 仅给示例。
- 未本地化 Google Fonts。

---

## 7. 文件变更汇总（精确路径）

新增：
- `/root/hermes-collab-engine/sandbox/index.html`
- `/root/hermes-collab-engine/sandbox/server.py`
- `/root/hermes-collab-engine/sandbox/README.md`
- `/root/hermes-collab-engine/scripts/seed_demo_data.py`
- `/root/hermes-collab-engine/config/sandbox-mocks.json`

未修改：`web/index.html`、`src/hermes_collab_engine/*`、`data/collab.sqlite3`、`.runtime-config.json`。

---

## 8. 推荐下一步

1. 在带浏览器的环境跑一次端到端 UI 验证（playwright + 截图）。
2. 本地化 Google Fonts，移除外联。
3. 在反向代理上加 SSO/Basic Auth 与 `POST /api/runs` 限流（或 readonly 模式直接禁掉 POST）。
4. 校验启动参数：拒绝把生产 DB 路径传给沙盒。

HERMES-COLLAB-RESULT: {"status":"blocked","summary":"沙盒页面已克隆到独立目录并接入只读脱敏数据与 Mock 服务，本地演示路径全部通过；浏览器截图证据、外部字体外联、公开 API 鉴权三项构成上线前阻断或缺口。","files_modified":["/root/hermes-collab-engine/sandbox/index.html","/root/hermes-collab-engine/sandbox/server.py","/root/hermes-collab-engine/sandbox/README.md","/root/hermes-collab-engine/scripts/seed_demo_data.py","/root/hermes-collab-engine/config/sandbox-mocks.json"],"verification":["wbs-1..wbs-8 全部 returncode=0 完成","HTTP checks: /sandbox/hermes/, /api/overview, /api/runs, /api/runs/:id, /api/sandbox/config 通过","POST /api/runs 提交后只增内存运行记录，生产哨兵库字节未变","SSE /api/events 首帧返回正常","异常输入: 空 request -> 400, 路径穿越 -> 404","sensitive scan: 未发现真实密钥；仅 demo-* fixture token","浏览器像素渲染/截图: 阻塞 (环境无 Chromium/Playwright/Selenium)"],"notes":["公网暴露前必须在反代加鉴权与限流","sandbox/index.html:7-9 仍引用 Google Fonts，需本地化或删除","建议启动时校验 --db 路径，避免误指向生产库","/api/sandbox/config 公网展示时建议脱敏 DB 绝对路径"]}
