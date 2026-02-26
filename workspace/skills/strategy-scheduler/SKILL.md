---
name: strategy-scheduler
description: 策略调度技能，基于 cron 统一调度多市场策略任务。
---

# strategy-scheduler

## 目标

统一调度 A股、美股、Crypto、贵金属相关策略任务。

## 功能

- 任务注册与启停
- 时区管理
- 失败重试与告警
- 运行结果写入日志

## 任务最小结构

```json
{
  "id": "quant-job-id",
  "name": "job-name",
  "market": "us-stock",
  "schedule": "0 * * * *",
  "command": "python3 /path/to/script.py"
}
```

## 实现路径

与 `.openclaw/cron/jobs.json` 保持同构。
