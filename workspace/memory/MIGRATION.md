# Memory Migration Notes

## 已迁移到 `memory/state/`

- `amd_planb_state.json` -> `state/amd-planb-state.json`
- `baba_buyalert_state.json` -> `state/baba-buyalert-state.json`
- `nvda_buyalert_state.json` -> `state/nvda-buyalert-state.json`
- `tsla_buyalert_state.json` -> `state/tsla-buyalert-state.json`
- `stock_signals_state.json` -> `state/us-stock-signals-state.json`
- `stock_resonance_state.json` -> `state/stock-resonance-state.json`
- `stock_alert.txt` -> `state/us-stock-alert.txt`
- `stock_resonance_alert.txt` -> `state/stock-resonance-alert.txt`

## 已迁移到 `memory/templates/`

- `weekly-cftc-template.md`
- `monthly-rebalance-template.md`
- `quarterly-rebalance-template.md`

## 兼容策略

旧路径暂时保留，后续脚本逐步切换到新路径。
