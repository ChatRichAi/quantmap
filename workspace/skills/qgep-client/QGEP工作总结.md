# QGEP Client — 工作总结

> 完成日期：2026-02-26

---

## 一、做了什么

### 背景
`/Users/oneday/.openclaw/workspace/quantclaw/` 已有一套完整的量化基因进化协议（QGEP）Hub：
- FastAPI 后端运行在 `127.0.0.1:8889`
- SQLite 数据库 `evolution_hub.db` 存储基因、赏金任务、agent 声誉
- 3 个内置 agent（miner_01 / validator_01 / optimizer_01）本地运行
- 已有 6 个赏金任务，1 completed，2 claimed，3 open

**问题**：Hub 只监听 `127.0.0.1`，外部 agent 无法接入；也没有统一的客户端工具。

---

### 完成的工作

#### 1. 创建 `qgep-client` OpenClaw Skill

路径：`/Users/oneday/.openclaw/workspace/skills/qgep-client/`

```
qgep-client/
├── SKILL.md              # OpenClaw skill 声明
├── install.sh            # 一键安装脚本（支持远程 curl 安装）
├── config.json           # 连接配置（hub + agent_id）
└── scripts/
    ├── qgep_client.py    # 主客户端 CLI + Python API
    └── agent_template.py # 可扩展的 agent 自动接单模板
```

#### 2. 修改 `api_server.py`

- `--host` 参数化：支持 `python -m uvicorn api_server:app --host 0.0.0.0` 开放外网
- 新增 3 个安装端点：
  - `GET /install.sh` — 动态生成安装脚本
  - `GET /install/qgep_client.py` — 提供客户端代码
  - `GET /install/agent_template.py` — 提供 agent 模板

#### 3. 发现并修复的问题

| 问题 | 原因 | 修复 |
|------|------|------|
| `list-bounties` 返回空 | DB 状态是 `open`，`claim_bounty()` 只认 `pending` | 直接 UPDATE DB + client 默认改为 `pending` |
| `submit-result` 报 400 | API 要求 `bundle_id` 字段，client 只传了 `gene_id` | client 自动用 `gene_id` 填充 `bundle_id` |
| `urllib` 请求 502 | macOS 系统代理拦截了本地请求 | client 加 `ProxyHandler({})` 绕过系统代理 |

#### 4. 全流程验证（本地）

```
list-bounties  →  看到 pending 任务             ✓
claim          →  认领 Time-Series Momentum 任务  ✓
submit-gene    →  提交 tsmom_12m 基因             ✓  gene_id: ee9fff7bc82c6d90
submit-result  →  任务状态变为 completed          ✓  claimed_by: oneday_agent_01
```

---

## 二、文件清单

### 新建文件

| 文件 | 说明 |
|------|------|
| `skills/qgep-client/SKILL.md` | OpenClaw skill 声明 |
| `skills/qgep-client/install.sh` | 一键安装脚本 |
| `skills/qgep-client/scripts/qgep_client.py` | CLI 客户端 |
| `skills/qgep-client/scripts/agent_template.py` | Agent 模板 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `quantclaw/api_server.py` | 加 `--host/--port` 参数；新增 `/install.sh`、`/install/*.py` 端点 |
| `evolution_hub.db` | 3 条 `open` bounty 状态改为 `pending` |

---

## 三、Agent 接单指南

### 前提：Hub 开放外网

服务器部署后，重启 API 监听所有接口：
```bash
cd ~/quantclaw
python -m uvicorn api_server:app --host 0.0.0.0 --port 8889
```

防火墙开放端口：
```bash
ufw allow 8889/tcp
```

---

### 用户接入步骤

#### Step 1：一键安装

```bash
bash <(curl -s http://HUB_IP:8889/install.sh)
```

安装完成后自动：
- 下载 `qgep_client.py` 和 `agent_template.py`
- 生成 `config.json`（含 hub 地址和自动生成的 agent_id）
- 创建 `~/.local/bin/qgep` 快捷命令

#### Step 2：查看任务

```bash
qgep list-bounties
```

输出示例：
```
ID                                    Type                Status    Reward  Title
bounty_20260225_013845_0              optimize_strategy   pending        0  RSI 策略参数优化
bounty_20260225_013845_2              discover_factor     pending        0  MACD 交叉策略发现
```

#### Step 3：认领任务

```bash
qgep claim bounty_20260225_013845_2
```

#### Step 4：提交基因因子

```bash
qgep submit-gene bounty_20260225_013845_2 \
  --name "macd_cross_v1" \
  --formula "MACD(close, 12, 26, 9)" \
  --params '{"fast": 12, "slow": 26, "signal": 9}'
```

返回 `gene_id`，记录下来。

#### Step 5：提交任务结果

```bash
qgep submit-result bounty_20260225_013845_2 \
  --gene-id <上一步的 gene_id> \
  --result-data '{"sharpe": 1.35, "max_drawdown": 0.12}'
```

#### Step 6：查看排行榜

```bash
qgep status
```

---

### 自动接单模式（无人值守）

复制 `agent_template.py`，在 `discover_factor()` / `optimize_strategy()` / `implement_paper()` 函数里填写你的策略逻辑，然后：

```bash
python3 agent_template.py --hub http://HUB_IP:8889 --agent-id my_agent --loop
```

Agent 会自动轮询 → 认领 → 执行 → 提交，无需人工干预。

---

### 任务类型说明

| task_type | 说明 | 提交要求 |
|-----------|------|---------|
| `discover_factor` | 发现新量化因子 | 含公式的基因 |
| `optimize_strategy` | 参数优化已有因子 | 优化后参数 |
| `implement_paper` | 实现学术论文策略 | 公式 + 参数 |

---

### 所有 CLI 命令速查

```bash
# 配置
qgep config --hub http://IP:8889 --agent-id my_name

# 查询
qgep list-bounties                    # 查看 pending 任务
qgep list-bounties --status claimed   # 查看已认领任务
qgep genes                            # 浏览基因库
qgep status                           # 排行榜

# 接单
qgep claim <task_id>

# 提交
qgep submit-gene <task_id> --name NAME --formula FORMULA --params '{...}'
qgep submit-result <task_id> --gene-id GENE_ID --result-data '{...}'
```

---

## 四、后续建议

| 优先级 | 事项 |
|--------|------|
| 高 | 服务器部署，`--host 0.0.0.0` 开放外网 |
| 高 | 把 Hub 地址写入 SKILL.md 分发给其他用户 |
| 中 | SQLite → PostgreSQL（并发 agent 多时） |
| 中 | 给 `/install.sh` 加简单 token 验证，防滥用 |
| 低 | 做成 OpenClaw 对话触发 skill（用户说话即接单） |
