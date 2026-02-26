---
name: market-data
description: 统一多市场行情数据入口，覆盖 A股、美股、Crypto、贵金属。
---

# market-data

## 目标

把现有分散数据源统一到一个入口，避免重复实现。

## 数据源映射

- A股: `akshare`
- 美股: `yfinance` / `alpaca`
- Crypto: `OKX` / `Binance`
- 贵金属: XAU/XAG 价格源

## 标准输出结构

```json
{
  "market": "us-stock",
  "symbol": "NVDA",
  "timeframe": "1h",
  "timestamp": 0,
  "open": 0,
  "high": 0,
  "low": 0,
  "close": 0,
  "volume": 0
}
```

## 使用约定

- 不同市场统一字段命名
- 时间统一用 UTC 毫秒时间戳
- 实时与历史接口分离
