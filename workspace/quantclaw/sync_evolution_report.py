#!/usr/bin/env python3
"""
QuantMap Evolution Report Sync
进化报告同步到 Nowledge Memory
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, '/Users/oneday/.openclaw/workspace')

# Import the nmem module for saving memories
import subprocess

def generate_evolution_report():
    """生成进化报告"""
    db_path = '/Users/oneday/.openclaw/workspace/quantclaw/evolution_hub.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 今日统计
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(*) FROM genes 
        WHERE DATE(created_at) = DATE('now')
    ''')
    new_genes = cursor.fetchone()[0]
    
    # 来源统计
    cursor.execute('''
        SELECT 
            CASE 
                WHEN source LIKE '%crossover%' THEN 'Crossover'
                WHEN source LIKE '%mutation%' THEN 'Mutation'
                WHEN source LIKE '%rescue%' OR source LIKE '%seed%' THEN 'Seed'
                ELSE 'Other'
            END as type,
            COUNT(*) as count
        FROM genes 
        WHERE DATE(created_at) = DATE('now')
        GROUP BY type
    ''')
    sources = {row[0]: row[1] for row in cursor.fetchall()}
    
    # 最高代数
    cursor.execute('SELECT MAX(generation) FROM genes WHERE DATE(created_at) = DATE("now")')
    max_gen = cursor.fetchone()[0] or 0
    
    # 总基因数
    cursor.execute('SELECT COUNT(*) FROM genes')
    total_genes = cursor.fetchone()[0]
    
    # 最佳表现者 (从回测结果表中查询)
    cursor.execute('''
        SELECT g.name, g.formula, b.sharpe_ratio
        FROM genes g
        JOIN backtest_results b ON g.gene_id = b.gene_id
        WHERE b.timestamp > datetime('now', '-1 day')
        ORDER BY b.sharpe_ratio DESC
        LIMIT 3
    ''')
    top_performers = []
    for row in cursor.fetchall():
        top_performers.append({
            'name': row[0],
            'formula': row[1][:50] if row[1] else 'N/A',
            'sharpe': row[2] or 0
        })
    
    conn.close()
    
    return {
        'date': today,
        'new_genes': new_genes,
        'total_genes': total_genes,
        'sources': sources,
        'max_generation': max_gen,
        'top_performers': top_performers,
        'timestamp': datetime.now().isoformat()
    }

def save_to_nowledge(report):
    """保存报告到 Nowledge Memory"""
    
    # 构建报告内容
    content = f"""# QuantClaw 进化日报 - {report['date']}

## 今日进化统计

| 指标 | 数值 |
|------|------|
| 新增基因 | {report['new_genes']} |
| 总基因数 | {report['total_genes']} |
| 最高代数 | Gen {report['max_generation']} |

## 来源分布

"""
    
    for source, count in report['sources'].items():
        content += f"- **{source}**: {count} 个\n"
    
    content += f"""
## 表现最佳基因

"""
    
    for i, gene in enumerate(report['top_performers'], 1):
        content += f"""{i}. **{gene['name']}**
   - 夏普比率: {gene['sharpe']:.2f}
   - 公式: `{gene['formula']}`

"""
    
    content += f"""
## 可视化

实时进化网络: http://localhost:8888/quantclaw/ecosystem_visualization_dynamic.html

---
*自动生成于 {report['timestamp']}*
"""
    
    # 保存到知识图谱 (使用 nowledge_mem_save)
    # 注意: 这里需要通过命令行或直接调用API
    
    print(content)
    
    # 同时保存到每日日志
    daily_path = Path(f"/Users/oneday/.openclaw/workspace/memory/daily/{report['date']}_evolution.md")
    daily_path.parent.mkdir(parents=True, exist_ok=True)
    daily_path.write_text(content)
    
    print(f"\n✅ Report saved to: {daily_path}")
    
    return content

def main():
    """主函数"""
    print("🧬 Generating evolution report...")
    
    report = generate_evolution_report()
    
    if report['new_genes'] == 0:
        print("No new genes today, skipping report.")
        return
    
    content = save_to_nowledge(report)
    
    print("\n" + "="*60)
    print(f"📊 Evolution Report for {report['date']}")
    print("="*60)
    print(f"New genes: {report['new_genes']}")
    print(f"Total pool: {report['total_genes']}")
    print(f"Max generation: {report['max_generation']}")
    print("="*60)

if __name__ == "__main__":
    main()
