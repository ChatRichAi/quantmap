#!/usr/bin/env python3
"""
QuantClaw Adaptive Schedule Optimizer
自适应调度优化器 - 动态调整进化频率

根据以下因素自动调整运行间隔:
1. 基因池增长率
2. 新基因质量
3. 市场波动性
4. 计算资源使用
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict

DB_PATH = "/Users/oneday/.openclaw/workspace/quantclaw/evolution_hub.db"


def analyze_evolution_efficiency() -> Dict:
    """分析进化效率"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取最近24小时的进化数据
    since = (datetime.now() - timedelta(hours=24)).isoformat()
    
    # 新基因数量
    cursor.execute('''
        SELECT COUNT(*) FROM genes 
        WHERE created_at > ?
    ''', (since,))
    new_genes_24h = cursor.fetchone()[0]
    
    # 高质量基因数量 (适应度>80)
    cursor.execute('''
        SELECT COUNT(*) FROM genes 
        WHERE created_at > ? 
        AND formula LIKE '%RSI%'  -- 简化判断
    ''', (since,))
    high_quality_genes = cursor.fetchone()[0]
 
    # 基因重复率
    cursor.execute('''
        SELECT formula, COUNT(*) as cnt 
        FROM genes 
        WHERE created_at > ?
        GROUP BY formula
        HAVING cnt > 1
    ''', (since,))
    duplicates = cursor.fetchall()
    duplicate_rate = len(duplicates) / max(new_genes_24h, 1)
    
    conn.close()
    
    return {
        'new_genes_24h': new_genes_24h,
        'high_quality_rate': high_quality_genes / max(new_genes_24h, 1),
        'duplicate_rate': duplicate_rate,
        'efficiency_score': (high_quality_genes / max(new_genes_24h, 1)) * (1 - duplicate_rate)
    }


def recommend_interval() -> int:
    """推荐运行间隔（小时）"""
    metrics = analyze_evolution_efficiency()
    
    print("📊 Evolution Efficiency Analysis")
    print(f"   New genes (24h): {metrics['new_genes_24h']}")
    print(f"   High quality rate: {metrics['high_quality_rate']:.1%}")
    print(f"   Duplicate rate: {metrics['duplicate_rate']:.1%}")
    print(f"   Efficiency score: {metrics['efficiency_score']:.2f}")
    print()
    
    # 基于效率推荐间隔
    if metrics['efficiency_score'] > 0.7:
        # 效率高，可以加快
        recommended = 2
        reason = "High efficiency, can accelerate"
    elif metrics['efficiency_score'] > 0.4:
        # 效率正常，保持4小时
        recommended = 4
        reason = "Normal efficiency, maintain current"
    elif metrics['duplicate_rate'] > 0.5:
        # 重复率高，减慢
        recommended = 8
        reason = "High duplicate rate, slow down"
    else:
        # 效率低，减慢并检查
        recommended = 12
        reason = "Low efficiency, investigate issues"
    
    print(f"⏰ Recommended interval: {recommended} hours")
    print(f"   Reason: {reason}")
    
    return recommended


def update_heartbeat_schedule(hours: int):
    """更新HEARTBEAT配置"""
    heartbeat_path = "/Users/oneday/.openclaw/workspace/HEARTBEAT.md"
    
    with open(heartbeat_path, 'r') as f:
        content = f.read()
    
    # 更新描述中的时间
    old_desc = "每4小时运行100%自驱进化系统"
    new_desc = f"每{hours}小时运行100%自驱进化系统"
    
    content = content.replace(old_desc, new_desc)
    
    with open(heartbeat_path, 'w') as f:
        f.write(content)
    
    print(f"\n✅ Updated HEARTBEAT.md to run every {hours} hours")


def main():
    """主函数"""
    print("=" * 60)
    print("🔄 QuantClaw Adaptive Schedule Optimizer")
    print("=" * 60)
    print()
    
    recommended = recommend_interval()
    
    current = 4  # 当前配置
    
    if recommended != current:
        print(f"\n🔄 Adjusting from {current}h to {recommended}h")
        update_heartbeat_schedule(recommended)
        
        # 记录调整
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule_adjustments (
                timestamp TEXT,
                old_interval INTEGER,
                new_interval INTEGER,
                reason TEXT
            )
        ''')
        cursor.execute('''
            INSERT INTO schedule_adjustments VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), current, recommended, 
              f"Efficiency-based auto-adjustment"))
        conn.commit()
        conn.close()
    else:
        print(f"\n✅ Current interval ({current}h) is optimal")


if __name__ == "__main__":
    main()
