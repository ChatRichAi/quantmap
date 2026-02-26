# Quant EvoMap UI - Next.js 迁移方案

## 📋 概述

将现有的两个独立 HTML 可视化页面迁移到统一的 Next.js 应用，实现：
- ✅ 国际化 (i18n) - 中英文切换
- ✅ 统一导航和路由
- ✅ 组件化和代码复用
- ✅ 更好的 SEO 和性能
- ✅ 热重载开发体验

## 🗂 目录结构

```
quant-evomap-ui/
├── app/                          # Next.js App Router
│   ├── [locale]/                 # 国际化路由
│   │   ├── layout.tsx            # 主布局 (Header + Sidebar)
│   │   ├── page.tsx              # 首页 → QuantMap 网络可视化
│   │   ├── evomap/
│   │   │   └── page.tsx          # Quant EvoMap 动态生态
│   │   └── settings/
│   │       └── page.tsx          # 设置页面
│   ├── api/                      # API Routes (代理后端)
│   │   ├── ecosystem/route.ts
│   │   └── stats/route.ts
│   └── globals.css
├── components/
│   ├── layout/
│   │   ├── Header.tsx            # 顶部导航栏
│   │   ├── Sidebar.tsx           # 侧边栏
│   │   └── LanguageSwitch.tsx    # 语言切换器
│   ├── visualization/
│   │   ├── ForceGraph.tsx        # D3 力导向图
│   │   ├── GeneCard.tsx          # 基因卡片
│   │   ├── StatsBar.tsx          # 统计栏
│   │   ├── Legend.tsx            # 图例
│   │   └── Tooltip.tsx           # 悬浮提示
│   └── ui/                       # 通用 UI 组件
│       ├── Button.tsx
│       ├── Badge.tsx
│       └── Card.tsx
├── lib/
│   ├── api.ts                    # API 客户端
│   ├── i18n.ts                   # 国际化配置
│   └── utils.ts                  # 工具函数
├── locales/                      # 翻译文件
│   ├── en.json
│   └── zh.json
├── public/
│   └── images/
├── next.config.js
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

## 🌐 国际化方案

使用 `next-intl` 实现路由级国际化：

- `/en/` → 英文版
- `/zh/` → 中文版
- 默认语言：中文 (根据当前用户场景)

### 翻译文件结构

**locales/zh.json:**
```json
{
  "common": {
    "genes": "基因",
    "generation": "世代",
    "survivalRate": "存活率",
    "avgSharpe": "平均夏普",
    "evolutionLive": "进化实时"
  },
  "nav": {
    "quantmap": "QuantMap",
    "evomap": "Quant EvoMap",
    "settings": "设置"
  },
  "evomap": {
    "title": "量化策略进化网络",
    "topGenes": "表现最佳基因",
    "evolutionLog": "进化日志",
    "resetView": "重置视图",
    "runEvolution": "运行进化"
  },
  "legend": {
    "title": "基因类型",
    "passed": "通过 (Sharpe > 1.0)",
    "survived": "存活 (Sharpe > 0.5)",
    "eliminated": "淘汰",
    "newOffspring": "新后代"
  },
  "tooltip": {
    "formula": "公式",
    "sharpe": "夏普比率",
    "generation": "世代",
    "status": "状态",
    "passed": "✅ 已通过",
    "failed": "❌ 未通过"
  }
}
```

**locales/en.json:**
```json
{
  "common": {
    "genes": "Genes",
    "generation": "Generation",
    "survivalRate": "Survival Rate",
    "avgSharpe": "Avg Sharpe",
    "evolutionLive": "Evolution Live"
  },
  "nav": {
    "quantmap": "QuantMap",
    "evomap": "Quant EvoMap",
    "settings": "Settings"
  },
  "evomap": {
    "title": "Quant Strategy Evolution Network",
    "topGenes": "Top Performing Genes",
    "evolutionLog": "Evolution Log",
    "resetView": "Reset View",
    "runEvolution": "Run Evolution"
  },
  "legend": {
    "title": "Gene Types",
    "passed": "Passed (Sharpe > 1.0)",
    "survived": "Survived (Sharpe > 0.5)",
    "eliminated": "Eliminated",
    "newOffspring": "New Offspring"
  },
  "tooltip": {
    "formula": "Formula",
    "sharpe": "Sharpe Ratio",
    "generation": "Generation",
    "status": "Status",
    "passed": "✅ Passed",
    "failed": "❌ Failed"
  }
}
```

## 🔄 迁移映射

| 原文件 | Next.js 路由 | 组件 |
|--------|-------------|------|
| `quantmap/visualization/index.html` | `/[locale]/` | `ForceGraph` + `StatsBar` |
| `quantclaw/ecosystem_visualization_dynamic.html` | `/[locale]/evomap` | `ForceGraph` (enhanced) + `GeneCard` |

## 📦 依赖

```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "next-intl": "^3.15.0",
    "d3": "^7.9.0",
    "tailwindcss": "^3.4.0",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    "@types/d3": "^7.4.0",
    "@types/node": "^20.0.0",
    "@types/react": "^18.3.0",
    "typescript": "^5.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

## 🚀 实施步骤

### Phase 1: 项目初始化
1. 创建 Next.js 项目结构
2. 配置 Tailwind CSS
3. 设置 next-intl 国际化
4. 创建基础布局组件

### Phase 2: 组件迁移
1. 提取 CSS 变量到 Tailwind 配置
2. 迁移 Header 组件
3. 迁移 StatsBar 组件
4. 封装 D3 ForceGraph 为 React 组件

### Phase 3: 页面迁移
1. 实现 QuantMap 主页
2. 实现 EvoMap 页面
3. 添加 API 代理路由

### Phase 4: 优化
1. 添加加载状态和错误处理
2. 实现暗色/亮色主题
3. 添加 SEO 元数据
4. 性能优化

## ⚡ 启动命令

```bash
# 安装依赖
cd quant-evomap-ui && npm install

# 开发模式
npm run dev  # http://localhost:3000

# 构建
npm run build

# 生产模式
npm run start
```

## 🔗 API 配置

Next.js API Routes 代理到后端：

```typescript
// app/api/ecosystem/route.ts
export async function GET() {
  const res = await fetch('http://localhost:8891/api/ecosystem');
  const data = await res.json();
  return Response.json(data);
}
```

## 📝 注意事项

1. **D3 + React**: 使用 `useRef` + `useEffect` 挂载 D3 图表
2. **SSR**: D3 代码需要 `"use client"` 标记
3. **动画**: 保留首次加载动画逻辑，使用 `sessionStorage` 记录状态
4. **API 端口**: 自动检测 8889/8891 端口
