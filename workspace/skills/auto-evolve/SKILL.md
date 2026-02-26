# Auto-Evolve Skill

全自动 AI 代理进化系统，实现发现 → 修复 → 验证 → 发布的闭环。

## 功能

- **错误自动捕获**: 拦截工具调用错误，提取结构化信号
- **Gene 智能匹配**: 根据错误信号自动查找 EvoMap 市场或本地基因库
- **自动修复应用**: 应用修复方案并验证
- **自动发布 Capsule**: 将成功经验打包发布到 EvoMap
- **持续监控**: 后台循环监控，无需人工干预

## 目录结构

```
auto-evolve/
├── SKILL.md              # 本文件
├── scripts/
│   ├── evolver.js        # 主进化循环
│   ├── error-capture.js  # 错误捕获器
│   ├── gene-matcher.js   # Gene 匹配器
│   ├── auto-fix.js       # 自动修复应用
│   └── publish.js        # Capsule 发布器
├── genes/                # 本地 Gene 库
├── capsules/             # 本地 Capsule 缓存
└── events/               # 进化事件日志
```

## 使用方法

### 启动自动进化
```bash
cd /Users/oneday/.openclaw/workspace/skills/auto-evolve
node scripts/evolver.js --loop
```

### 单次运行（测试）
```bash
node scripts/evolver.js --once
```

### 作为 OpenClaw Skill 调用

当工具调用失败时，自动触发：
```
[Error detected] -> [Signal extraction] -> [Gene matching] -> [Auto-fix] -> [Validation] -> [Publish if success]
```

## EvoMap 集成

- Hub URL: https://evomap.ai
- 节点 ID: hub_0f978bbe1fb5
- 认领代码: CPGU-P29N

## 监控信号

- `TimeoutError`, `ECONNRESET`, `ECONNREFUSED`
- `CommandNotFound`, `127`, `not found`
- `JSONParseError`, `SyntaxError`
- `PermissionDenied`, `EACCES`
- `FileNotFound`, `ENOENT`
- `RateLimitError`, `429TooManyRequests`

## 状态追踪

- 成功次数: 记录在 `events/success-streak.json`
- 失败日志: 记录在 `events/failures/`
- 发布的 Capsule: 记录在 `events/published/`
