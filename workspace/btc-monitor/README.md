# BTC $71K 突破追涨监控系统

## 系统概述

自动监控BTC价格，当满足所有追涨条件时发送WhatsApp提醒。

## 触发条件（需同时满足）

1. ✅ BTC现货价格突破 $71,000
2. ✅ 成交量 > 1.5倍20日均量
3. ✅ 资金费率转正（>+0.01%）
4. ✅ 突破后维持30分钟以上

## 文件结构

```
btc-monitor/
├── package.json          # 项目配置
├── monitor.js            # 主监控脚本
├── state.json            # 状态跟踪文件
├── run.sh                # 手动运行脚本
├── monitor.log           # 运行日志
├── cron.log              # 定时任务日志
└── README.md             # 本说明文档
```

## 监控频率

每5分钟检查一次（通过macOS LaunchAgent实现）

## 启动/停止监控

```bash
# 启动
launchctl load ~/Library/LaunchAgents/com.user.btc71kmonitor.plist

# 停止
launchctl unload ~/Library/LaunchAgents/com.user.btc71kmonitor.plist

# 手动运行一次
cd /Users/oneday/.openclaw/workspace/btc-monitor && node monitor.js
```

## 状态说明

- `isMonitoring`: 是否进入突破监控模式
- `breakoutStartTime`: 突破开始时间戳
- `alerted`: 是否已发送提醒
- `lastCheckTime`: 最后一次检查时间

## 查看日志

```bash
# 实时监控
tail -f /Users/oneday/.openclaw/workspace/btc-monitor/cron.log

# 查看所有日志
cat /Users/oneday/.openclaw/workspace/btc-monitor/monitor.log
```

## API数据来源

- **价格和成交量**: Binance Spot API (https://api.binance.com)
- **资金费率**: Binance Futures API (https://fapi.binance.com)
- **20日成交量**: Binance Kline API

## 提醒内容

突破确认后会发送包含以下内容的WhatsApp消息：
- 当前价格和成交量数据
- 资金费率
- 突破持续时间
- 操作建议（期权合约推荐）
- 风险提示
