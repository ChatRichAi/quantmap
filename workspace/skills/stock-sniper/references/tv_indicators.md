# TradingView 指标说明

## 核心指标使用指南

### 1. 订单流 (Order Flow)

**定义**: 显示买卖双方力量对比的指标

**读取方法**:
- **买方柱状** > 卖方柱状 = 买盘占优
- **卖方柱状** > 买方柱状 = 卖盘占优
- **失衡区域**: 连续多根同方向柱 = 趋势可能延续
- **吸收**: 大量成交但价格不动 = 可能反转

**交易应用**:
- 突破关键位 + 买方放量 = 有效突破
- 顶部 + 卖方放量 = 可能见顶
- 底部 + 买方放量 = 可能见底

### 2. 成交量分布 (Volume Profile)

**定义**: 显示不同价格区间的成交量分布

**关键概念**:
- **POC (Point of Control)**: 成交量最大的价格，强支撑/阻力
- **HVN (High Volume Node)**: 高成交量区域，价格停留时间长
- **LVN (Low Volume Node)**: 低成交量区域，价格快速穿过
- **VA (Value Area)**: 70%成交量所在区域

**交易应用**:
- 价格接近POC = 可能反弹或受阻
- 突破HVN = 趋势可能加速
- 在LVN区域 = 价格可能快速移动

### 3. 支撑阻力位

**识别方法**:
- **水平支撑/阻力**: 前期高低点
- **趋势线**: 连接多个高点或低点
- **均线**: 常用20日、60日、120日
- **黄金分割**: 38.2%、50%、61.8%

**有效性判断**:
- 触及次数越多 = 越有效
- 成交量配合 = 更可靠
- 时间跨度越长 = 越重要

### 4. VWAP (成交量加权平均价)

**定义**: 当日成交的平均成本价

**交易应用**:
- 价格在VWAP上方 = 多头占优
- 价格在VWAP下方 = 空头占优
- 回踩VWAP反弹 = 买入机会
- 跌破VWAP = 卖出信号

## 多周期分析

### 5分钟图 - 微观结构
**用途**: 
- 精确入场点
- 观察即时买卖力量
- 识别假突破

**关注指标**:
- 订单流实时变化
- VWAP偏离度
- 短期支撑阻力

### 15分钟图 - 波段操作
**用途**:
- 判断日内趋势
- 寻找波段高低点
- 确认突破有效性

**关注指标**:
- 成交量分布
- 中期支撑阻力
- 趋势方向

### 1小时图 - 日线结构
**用途**:
- 判断日线趋势
- 寻找关键支撑阻力
- 确定大方向

**关注指标**:
- 长期支撑阻力
- 成交量分布全貌
- 趋势通道

## TV快捷键

| 快捷键 | 功能 |
|--------|------|
| Alt + 1/2/3 | 切换时间周期 |
| Ctrl + S | 保存图表布局 |
| F | 切换全屏 |
| / | 打开指标搜索 |
| ← → | 左右移动图表 |
| + - | 缩放图表 |

## 常用脚本

### 支撑阻力自动标记
```pinescript
//@version=5
indicator("Support Resistance", overlay=true)

// 找近期高低点
pivotHigh = ta.pivothigh(high, 5, 5)
pivotLow = ta.pivotlow(low, 5, 5)

plotshape(pivotHigh, "Resistance", style=shape.triangledown, location=location.abovebar, color=color.red, size=size.small)
plotshape(pivotLow, "Support", style=shape.triangleup, location=location.belowbar, color=color.green, size=size.small)
```

### 量能异常提示
```pinescript
//@version=5
indicator("Volume Alert", overlay=false)

// 计算量比
volumeRatio = volume / ta.sma(volume, 20)

// 放量提示
plotshape(volumeRatio > 2, "Volume Spike", style=shape.labelup, location=location.bottom, color=color.blue, size=size.small)
```
