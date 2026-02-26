# Quant Genius Nation - 量化天才之国

**全自动量化策略进化系统**

---

## 🏛️ 系统架构

```
Quant Genius Nation
├── ⛏️ 素材挖掘层 (DataSourceExpansion)
│   ├── ArXiv 论文挖掘
│   ├── GitHub 开源策略
│   ├── 市场数据模式
│   └── 历史交易记录
│
├── 🔍 模式识别层 (PatternRecognition)
│   ├── 8大策略类别识别
│   ├── 逻辑骨架提取
│   └── 质量评分
│
├── 🧬 基因工程层 (GeneEngineering)
│   ├── 元模式实例化
│   ├── 参数变体生成
│   └── 公式模板构建
│
├── 🦁 自然选择层 (DarwinianSelection)
│   ├── 分层淘汰机制
│   ├── 多样性保护
│   ├── 防过拟合验证
│   └── 时效衰减
│
├── 📚 知识沉淀层 (KnowledgePersistence)
│   ├── SQLite 基因池
│   ├── 进化历史记录
│   └── 状态快照
│
└── 🤖 元认知层 (MetaCognition)
    ├── 自适应参数
    ├── 健康监控
    └── 故障自愈
```

---

## 🚀 快速启动

```bash
cd ~/.openclaw/workspace/quantclaw

# 单轮进化测试
./start_nation.sh single

# 24x7 持续运行
./start_nation.sh continuous

# 查看状态
./start_nation.sh status

# 查看进化报告
./start_nation.sh report
```

---

## 📊 核心组件

### 1. quant_genius_nation.py - 进化引擎
- 7阶段进化周期
- 全自动运行
- 单次/持续模式

### 2. arxiv_meta_extractor_v2.py - 元模式提取
- 从论文提取抽象模式
- 不直接注入具体因子
- 支持模式实例化

### 3. darwin_selection_v2.py - 达尔文选择
- 分层选择机制
- 多样性保护
- 防过拟合验证

### 4. data_source_expansion.py - 数据源扩展
- 27个 arXiv 查询类别
- 实时市场数据
- 历史记录挖掘

### 5. evolution_daemon.py - 守护进程
- 24x7 自动运行
- 故障自愈
- 状态监控

---

## 🎯 设计哲学

### 第一性原理
1. **数据先于观点** - 从不假设，只从数据提取
2. **结构重于参数** - 提取模式骨架，而非具体数值
3. **多样性即力量** - 防止单一策略垄断
4. **时间检验一切** - 老基因必须持续证明价值
5. **发表即失效** - 论文具体因子可能已失效，但结构模式仍有价值

### 创新点
- **Meta-Pattern 提取**: 不直接交易论文因子，而是提取"什么结构有效"
- **分层选择**: 不同来源基因不同淘汰标准
- **防过拟合多层验证**: OOS + 参数稳定 + 成本敏感 + 路径稳健
- **无限素材源**: 持续挖掘新数据源

---

## 📈 第一轮进化成果

| 指标 | 数值 |
|------|------|
| 挖掘素材 | 299 (arXiv) + 29 (本地) |
| 提取模式 | 4 类 |
| 工程基因 | 12 个 |
| 成功注入 | 12/12 |
| 运行时间 | 27.4s |

---

## 🔧 扩展数据源清单

### 学术论文
- [x] arXiv (q-fin, cs.LG, stat.ML)
- [ ] SSRN
- [ ] RePEc
- [ ] JSTOR
- [ ] Google Scholar

### 开源代码
- [x] GitHub (部分)
- [ ] GitLab
- [ ] Bitbucket
- [ ] QuantConnect
- [ ] Quantopian (归档)

### 市场数据
- [x] OKX Crypto
- [ ] Yahoo Finance
- [ ] Alpha Vantage
- [ ] Quandl/NASDAQ Data Link
- [ ] FRED 宏观数据

### 另类数据
- [ ] 社交媒体情绪
- [ ] 卫星数据
- [ ] 信用卡数据
- [ ] 供应链数据
- [ ] 链上数据

---

## 🛡️ 风控机制

### 分层保护
| 基因类型 | 保护期 | 淘汰阈值 | 压力系数 |
|----------|--------|----------|----------|
| Seed (人工) | 30天 | 0.3 | 0.5x |
| Evolved | 14天 | 0.5 | 1.0x |
| Meta | 7天 | 0.6 | 1.5x |
| ArXiv Raw | 0天 | 0.7 | 2.0x |

### 多样性保护
- 单一类别上限: 35%
- 稀缺类别奖励: +20% 保护
- 过剩类别惩罚: -10% 适应度

### 防过拟合检查
- 样本外稳健性 (OOS/IS > 0.8)
- 参数数量惩罚 (>6参数扣分)
- 成本敏感性 (>30%成本侵蚀淘汰)
- 简洁性奖励 (复杂公式扣分)

---

## 📁 文件结构

```
quantclaw/
├── quant_genius_nation.py      # 主进化系统
├── arxiv_meta_extractor_v2.py  # 元模式提取
├── darwin_selection_v2.py      # 达尔文选择
├── data_source_expansion.py    # 数据源扩展
├── evolution_daemon.py         # 守护进程
├── start_nation.sh             # 启动脚本
├── evolution_hub.db            # 基因池数据库
├── mined_materials.json        # 挖掘素材
└── logs/
    ├── evolution_daemon.log    # 运行日志
    ├── evolution_history.jsonl # 历史记录
    └── daemon_status.json      # 当前状态
```

---

## 🔄 进化周期流程

```
每2小时自动执行:
  Phase 1: 素材挖掘      (ArXiv + 市场 + 历史)
  Phase 2: 模式识别      (提取逻辑骨架)
  Phase 3: 基因工程      (实例化参数变体)
  Phase 4: 基因注入      (写入数据库)
  Phase 5: 生存挑战      (回测验证 + 淘汰)
  Phase 6: 繁衍进化      (交叉 + 变异)
  Phase 7: 知识沉淀      (保存状态)
```

---

## 🎓 梁文峰风格设计决策

1. **不追热点因子** - 提取结构，而非具体实现
2. **相信统计** - 用出现频率衡量模式可信度
3. **敬畏市场** - 发表即失效，论文因子高淘汰压力
4. **工程优先** - 可运行的代码 > 理论完美
5. **持续迭代** - 24x7 进化，永不停止

---

## 📋 下一步 TODO

- [ ] 接入更多数据源 (SSRN, FRED, 链上数据)
- [ ] 实现真实的回测验证 (替换 mock)
- [ ] 添加可视化仪表板
- [ ] 实现参数优化 (Optuna)
- [ ] 接入实盘模拟 (Paper Trading)
- [ ] 建立策略组合优化器

---

*量化天才之国已启动，永不停止的进化开始了。*
