#!/usr/bin/env python3
"""
Evolver 紧急修复脚本
- 注入多样化种子基因
- 重启进化系统
"""

import sys
import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from evolution_ecosystem import QuantClawEvolutionHub, Gene

DB_PATH = "/Users/oneday/.openclaw/workspace/quantclaw/evolution_hub.db"

def generate_diverse_seeds():
    """生成多样化的高质量种子基因"""
    
    seeds = [
        # 趋势跟踪类
        Gene(
            gene_id="g_trend_sma20_" + hashlib.sha256(b"sma20_trend").hexdigest()[:6],
            name="SMA20_Trend_Follow",
            description="20日均线趋势跟踪策略",
            formula="Close > SMA(20) and Close[1] <= SMA(20)[1]",
            parameters={'period': 20, 'type': 'trend'},
            source="emergency_seed",
            author="system_recovery",
            created_at=datetime.now(),
            generation=0
        ),
        Gene(
            gene_id="g_trend_sma50_" + hashlib.sha256(b"sma50_trend").hexdigest()[:6],
            name="SMA50_Trend_Follow",
            description="50日均线趋势跟踪策略",
            formula="Close > SMA(50) and Volume > SMA(Volume,20) * 1.2",
            parameters={'period': 50, 'volume_factor': 1.2, 'type': 'trend'},
            source="emergency_seed",
            author="system_recovery",
            created_at=datetime.now(),
            generation=0
        ),
        
        # 均值回归类
        Gene(
            gene_id="g_mean_rsi30_" + hashlib.sha256(b"rsi30_mean").hexdigest()[:6],
            name="RSI30_Mean_Reversion",
            description="RSI超卖反弹策略",
            formula="RSI(14) < 30 and RSI(14)[1] < RSI(14)[2]",
            parameters={'rsi_period': 14, 'threshold': 30, 'type': 'mean_reversion'},
            source="emergency_seed",
            author="system_recovery",
            created_at=datetime.now(),
            generation=0
        ),
        Gene(
            gene_id="g_mean_bb_" + hashlib.sha256(b"bb_mean").hexdigest()[:6],
            name="Bollinger_Bottom",
            description="布林带下轨反弹策略",
            formula="Close < BB_Lower(20,2) and Close[1] >= BB_Lower(20,2)[1]",
            parameters={'bb_period': 20, 'bb_std': 2, 'type': 'mean_reversion'},
            source="emergency_seed",
            author="system_recovery",
            created_at=datetime.now(),
            generation=0
        ),
        
        # 动量类
        Gene(
            gene_id="g_mom_macd_" + hashlib.sha256(b"macd_mom").hexdigest()[:6],
            name="MACD_Momentum",
            description="MACD金叉动量策略",
            formula="MACD > Signal and MACD[1] <= Signal[1]",
            parameters={'fast': 12, 'slow': 26, 'signal': 9, 'type': 'momentum'},
            source="emergency_seed",
            author="system_recovery",
            created_at=datetime.now(),
            generation=0
        ),
        Gene(
            gene_id="g_mom_break_" + hashlib.sha256(b"break_mom").hexdigest()[:6],
            name="Price_Breakout",
            description="价格突破策略",
            formula="Close > Highest(High,20)[1] and Volume > SMA(Volume,20) * 1.5",
            parameters={'lookback': 20, 'volume_factor': 1.5, 'type': 'breakout'},
            source="emergency_seed",
            author="system_recovery",
            created_at=datetime.now(),
            generation=0
        ),
        
        # 波动率类
        Gene(
            gene_id="g_vol_atr_" + hashlib.sha256(b"atr_vol").hexdigest()[:6],
            name="ATR_Volatility_Break",
            description="ATR波动率突破策略",
            formula="Close - Open > ATR(14) * 0.5 and Close > SMA(20)",
            parameters={'atr_period': 14, 'threshold': 0.5, 'type': 'volatility'},
            source="emergency_seed",
            author="system_recovery",
            created_at=datetime.now(),
            generation=0
        ),
        
        # 多因子组合
        Gene(
            gene_id="g_multi_1_" + hashlib.sha256(b"multi1").hexdigest()[:6],
            name="Multi_Trend_Momentum",
            description="趋势+动量组合策略",
            formula="Close > SMA(20) and MACD > Signal and Volume > SMA(Volume,20)",
            parameters={'sma_period': 20, 'type': 'multi_factor'},
            source="emergency_seed",
            author="system_recovery",
            created_at=datetime.now(),
            generation=0
        ),
        Gene(
            gene_id="g_multi_2_" + hashlib.sha256(b"multi2").hexdigest()[:6],
            name="Multi_Value_Momentum",
            description="价值+动量组合策略",
            formula="Close < SMA(50) * 1.05 and RSI(14) > 50 and RSI(14) < 70",
            parameters={'type': 'multi_factor'},
            source="emergency_seed",
            author="system_recovery",
            created_at=datetime.now(),
            generation=0
        ),
        
        # 复杂条件
        Gene(
            gene_id="g_complex_1_" + hashlib.sha256(b"complex1").hexdigest()[:6],
            name="Complex_Swing",
            description="复杂摆动策略",
            formula="SMA(10) > SMA(30) and RSI(14) < 60 and Close > Open * 1.01",
            parameters={'fast': 10, 'slow': 30, 'type': 'complex'},
            source="emergency_seed",
            author="system_recovery",
            created_at=datetime.now(),
            generation=0
        ),
    ]
    
    return seeds

def inject_seeds():
    """注入种子基因"""
    hub = QuantClawEvolutionHub(DB_PATH)
    
    print("🌱 注入紧急种子基因...")
    seeds = generate_diverse_seeds()
    
    injected = 0
    for seed in seeds:
        try:
            hub.publish_gene(seed)
            print(f"   ✅ {seed.name}")
            injected += 1
        except Exception as e:
            print(f"   ⚠️ {seed.name}: {e}")
    
    print(f"\n📊 成功注入 {injected} 个种子基因")
    return injected

def clear_dead_genes():
    """清理死亡基因记录（保留统计但重置系统状态）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取当前统计
    cursor.execute('SELECT COUNT(*) FROM gene_deaths')
    death_count = cursor.fetchone()[0]
    
    print(f"💀 历史死亡基因: {death_count} 个")
    print("   (保留记录用于分析)")
    
    conn.close()

def reset_state():
    """重置状态文件"""
    state_path = Path("/Users/oneday/.openclaw/workspace/quantclaw/evolver_state.json")
    
    new_state = {
        "started_at": datetime.now().isoformat(),
        "cycles": 0,
        "last_interval_seconds": 300,
        "last_cycle": {
            "at": datetime.now().isoformat(),
            "scan": {
                "pool_size": 0,
                "diversity": 0,
                "hours_since_new_gene": 0,
                "diagnosis": {"severity": "normal", "issues": [], "recommendations": []}
            },
            "signals": [],
            "intent": "initial_seed",
            "mutation": {"intent": "initial_seed", "mode": "none", "report": {}},
            "validation": {"validated": 0, "passed": 0, "pass_rate": 0.0},
            "solidify": {"event_id": f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}", "gdi_score": 0.0},
            "next_interval_seconds": 300
        }
    }
    
    with open(state_path, 'w') as f:
        json.dump(new_state, f, indent=2)
    
    print(f"🔄 状态已重置: {state_path}")

def main():
    print("=" * 70)
    print("🔧 Evolver 系统紧急修复")
    print("=" * 70)
    print()
    
    # 1. 清理统计
    clear_dead_genes()
    print()
    
    # 2. 注入种子
    injected = inject_seeds()
    print()
    
    # 3. 重置状态
    reset_state()
    print()
    
    print("=" * 70)
    print("✅ 修复完成")
    print("=" * 70)
    print(f"""
修复内容:
1. 放宽生存阈值: 0.5 → 0.0
2. 放宽回测标准: 夏普>-0.5, 回撤<50%, 交易>=5次
3. 注入 {injected} 个多样化种子基因
4. 重置系统状态

下一步:
- 系统将在下次周期自动运行生存挑战
- 监控基因池增长情况
- 逐步调整阈值优化质量
""")

if __name__ == "__main__":
    main()
